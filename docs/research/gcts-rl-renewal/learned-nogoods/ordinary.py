"""Unexecuted ordinary chronological DPLL control; no point-engine authority.

Clauses and seeds use (variable_index, satisfying_bit) pairs.  Every node
scans every literal before choosing global conflict, first unit, or the
smallest unassigned variable.  Branch values are always zero then one.
"""

VERSION = "ordinary-finite-CNF-DPLL-source-v1"
RESULT_SCHEMA = "ordinary-finite-CNF-DPLL-result-v1"


class BudgetExceeded(Exception):
    """An incomplete bounded run, never a finite unsatisfiability claim."""


def solve_cnf(n, clauses, seed_bits, *, maximum_nodes,
              maximum_literal_checks, maximum_trace_events):
    """Return a complete first solution, finite exhaustion, or UNKNOWN.

No clock or external acceptance is implemented.  The actual cold caller
must independently account for all setup, search, audit and output costs.
"""
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(type(n) is int and 0 <= n <= 4, "n must be an integer in 0..4")
    require(type(clauses) is tuple and len(clauses) <= 8,
            "at most eight tuple clauses")
    for clause in clauses:
        require(type(clause) is tuple and len(clause) <= n, "tuple clause")
        seen = set()
        for literal in clause:
            require(type(literal) is tuple and len(literal) == 2,
                    "literal pair")
            i, bit = literal
            require(type(i) is int and 0 <= i < n and i not in seen,
                    "distinct valid variable in each clause")
            require(type(bit) is int and bit in (0, 1), "literal bit")
            seen.add(i)
    require(type(seed_bits) is tuple, "tuple seeds")
    root = [None] * n
    for pair in seed_bits:
        require(type(pair) is tuple and len(pair) == 2, "seed pair")
        i, bit = pair
        require(type(i) is int and 0 <= i < n and root[i] is None,
                "distinct valid seed variable")
        require(type(bit) is int and bit in (0, 1), "seed bit")
        root[i] = bit
    root = tuple(root)
    limits = {"maximum_nodes": maximum_nodes,
              "maximum_literal_checks": maximum_literal_checks,
              "maximum_trace_events": maximum_trace_events}
    for key, value in limits.items():
        require(type(value) is int and value >= 1, key + " must be positive")

    trace = []
    counts = {"nodes": 0, "scans": 0, "literal_checks": 0,
              "unit_decisions": 0, "branch_decisions": 0,
              "assignments": 0, "restores": 0, "conflicts": 0,
              "solutions": 0, "trace_events": 0}
    reserved_restores = 0

    def wire(state):
        return [[i, bit] for i, bit in enumerate(state) if bit is not None]

    def append_event(kind, **fields):
        trace.append(dict(event_index=len(trace), kind=kind, **fields))

    def emit(kind, **fields):
        # All active placements reserve a restore; one slot is always final.
        if len(trace) + 1 + reserved_restores + 1 > maximum_trace_events:
            raise BudgetExceeded("maximum_trace_events")
        append_event(kind, **fields)

    def scan(state):
        rows = []
        for ci, clause in enumerate(clauses):
            satisfied = False
            unassigned = []
            for i, bit in clause:
                if counts["literal_checks"] >= maximum_literal_checks:
                    raise BudgetExceeded("maximum_literal_checks")
                counts["literal_checks"] += 1
                if state[i] is None:
                    unassigned.append([i, bit])
                elif state[i] == bit:
                    satisfied = True
            rows.append({"index": ci, "satisfied": satisfied,
                         "unassigned": unassigned})
        emit("scan", state=wire(state), clauses=rows)
        counts["scans"] += 1
        return rows

    def move(parent, variable, bit, reason):
        nonlocal reserved_restores
        require(parent[variable] is None, "assignment must extend parent")
        child = parent[:variable] + (bit,) + parent[variable + 1:]
        reserved_restores += 1
        try:
            emit("assign", state=wire(child), parent_state=wire(parent),
                 candidate=[variable, bit], reason=reason)
        except BudgetExceeded:
            reserved_restores -= 1
            raise
        counts["assignments"] += 1
        try:
            return walk(child)
        finally:
            # Parent is an immutable tuple.  This records its exact return
            # even after a budget exception or deliberate first-found stop.
            reserved_restores -= 1
            append_event("restore", state=wire(parent),
                         from_assignment=wire(child))
            counts["restores"] += 1

    def walk(state):
        if counts["nodes"] >= maximum_nodes:
            raise BudgetExceeded("maximum_nodes")
        emit("enter", state=wire(state))
        counts["nodes"] += 1
        rows = scan(state)
        for row in rows:
            if not row["satisfied"] and not row["unassigned"]:
                emit("dead", state=wire(state), clause_index=row["index"])
                counts["conflicts"] += 1
                return None
        for row in rows:
            if not row["satisfied"] and len(row["unassigned"]) == 1:
                variable, bit = row["unassigned"][0]
                emit("unit", state=wire(state), clause_index=row["index"],
                     literal=[variable, bit])
                counts["unit_decisions"] += 1
                return move(state, variable, bit, "unit")
        variable = next((i for i, bit in enumerate(state) if bit is None), None)
        if variable is None:
            emit("solution", state=wire(state))
            counts["solutions"] += 1
            return state
        emit("branch", state=wire(state), variable=variable, values=[0, 1])
        counts["branch_decisions"] += 1
        for bit in (0, 1):
            solution = move(state, variable, bit, "branch")
            if solution is not None:
                return solution
        return None

    stop = None
    solution = None
    try:
        solution = walk(root)
        status = "FOUND" if solution is not None else "EXHAUSTED_FINITE_CNF"
    except BudgetExceeded as exc:
        stop = str(exc)
        status = "UNKNOWN"
    # Reserved events are the only events allowed after ordinary trace EOF.
    require(reserved_restores == 0, "root restoration reservation")
    require(len(trace) < maximum_trace_events, "reserved final trace slot")
    append_event("finished", state=wire(root), status=status)
    counts["trace_events"] = len(trace)
    return {
        "schema": RESULT_SCHEMA,
        "variables": n,
        "clauses": [[[i, bit] for i, bit in clause] for clause in clauses],
        "seed_bits": [[i, bit] for i, bit in seed_bits],
        "root_state": wire(root),
        "status": status,
        "solution": None if solution is None else wire(solution),
        "trace": trace,
        "trace_complete": status != "UNKNOWN",
        "exhaustion_complete": status == "EXHAUSTED_FINITE_CNF",
        "root_restored": True,
        "budget_stop": stop,
        "limits": limits,
        "work_counts": counts,
        "ordinary_origin": "chronological-clause-DPLL-first-solution",
        "point_engine_conformance": False,
        "learned_constraints_generated": False,
    }
