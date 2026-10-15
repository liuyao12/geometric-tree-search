"""UNEXECUTED finite identity-grounded unit-point calibration.

Exact integer t support is one point per candidate. Extended integer m ports
are sparse: an omitted entry is unconstrained, while zero is an assigned value.
This is not a fractional/shared-support/general-growth engine or a SAT oracle.
"""
from dataclasses import dataclass
from itertools import product

VERSION = 'finite-grounded-unit-point-gcts-v1'
MODEL_FORMAT = 'finite-grounded-unit-point-model-v1'
MAXIMUM_ROOTS = 128  # Declared calibration/recursion ceiling, never a model trim.


class BudgetExceeded(RuntimeError):
    """Whole result is UNKNOWN; no successful/exhausted prefix is accepted."""


def require(value, message):
    if not value:
        raise ValueError(message)


def integer(value, minimum=None):
    require(type(value) is int and (minimum is None or value >= minimum),
            'literal integer; Boolean is not an integer input')
    return value


def point(value):
    require(type(value) is tuple and len(value) == 2, 'integer point tuple')
    for coordinate in value:
        integer(coordinate)
    return value


@dataclass(frozen=True)
class Candidate:
    name: str
    base: tuple
    marks: tuple  # Complete sparse tuple of (x, y, integer-value) entries.


@dataclass(frozen=True)
class Model:
    roots: tuple  # ((integer-point, generation), ...); every finite root is zero.
    candidates: tuple
    fixed_marks: tuple
    marking_version: str


@dataclass(frozen=True)
class State:
    placements: tuple = ()  # (candidate-name, tile-generation), chronological.
    filled: tuple = ()
    marks: tuple = ()


@dataclass(frozen=True)
class Graph:
    point_candidates: tuple
    candidate_points: tuple
    dependencies: tuple  # All original t/m ports, even absent frontier ports.


class Work:
    def __init__(self, maximum_nodes, maximum_candidate_checks, maximum_trace_events):
        self.limits = {'root_points': MAXIMUM_ROOTS, 'nodes': integer(maximum_nodes, 1),
                       'candidate_checks': integer(maximum_candidate_checks, 1),
                       'trace_events': integer(maximum_trace_events, 1)}
        self.counts = {name: 0 for name in ('nodes', 'candidate_checks', 'trace_events')}
        self.stats = dict(graph_rebuilds=0, placements=0, forced_placements=0,
                          branch_decisions=0, backtracks=0, restores=0,
                          capacity_rejections=0, marking_rejections=0,
                          maximum_frontier_points=0, maximum_candidate_nodes=0,
                          maximum_incidence_edges=0, complete_solutions_checked=0)
        self.trace = []

    def charge(self, name):
        if self.counts[name] >= self.limits[name]:
            raise BudgetExceeded('declared ' + name + ' limit')
        self.counts[name] += 1

    def emit(self, kind, state, **details):
        self.charge('trace_events')
        self.trace.append(dict(kind=kind, state=state_wire(state), **details))


def mark_dict(entries):
    require(type(entries) is tuple, 'immutable sparse marking tuple')
    result = {}
    for entry in entries:
        require(type(entry) is tuple and len(entry) == 3, 'exact marking triple')
        p, value = point(entry[:2]), integer(entry[2])
        require(p not in result, 'one assigned value per marking point')
        result[p] = value
    return result


def mark_tuple(values):
    return tuple((x, y, value) for (x, y), value in sorted(values.items()))


def state_wire(state):
    return {'placements': [list(item) for item in state.placements],
            'filled': [list(p) for p in state.filled],
            'marks': [list(entry) for entry in state.marks]}


def model_wire(model):
    return {'schema': MODEL_FORMAT, 'marking_version': model.marking_version,
            'transformations': 'identity_only', 'multiplicity': 'each_candidate_at_most_once',
            'roots': [[*p, generation] for p, generation in model.roots],
            'fixed_marks': [list(entry) for entry in model.fixed_marks],
            'candidates': [{'name': c.name, 't': [[*c.base, 1]],
                            'm': [list(entry) for entry in c.marks]} for c in model.candidates]}


def validate_model(model, work):
    require(type(model) is Model and type(model.roots) is tuple
            and type(model.candidates) is tuple, 'exact immutable model')
    require(type(model.marking_version) is str and model.marking_version,
            'explicit marking version; no live rule change')
    if len(model.roots) > MAXIMUM_ROOTS:
        raise BudgetExceeded('declared root-point calibration ceiling')
    roots = {}
    for item in model.roots:
        require(type(item) is tuple and len(item) == 2, 'root with generation')
        p = point(item[0]); integer(item[1], 0)
        require(item[1] == 0 and p not in roots, 'all finite obligations explicit generation zero')
        roots[p] = item[1]
    mark_dict(model.fixed_marks)
    names = set()
    for c in model.candidates:
        work.charge('candidate_checks')
        require(type(c) is Candidate and type(c.name) is str and c.name
                and c.name not in names, 'unique named grounded candidate')
        require(point(c.base) in roots, 'one positive unit support inside required domain')
        mark_dict(c.marks); names.add(c.name)
    return roots, {c.name: c for c in model.candidates}


def rebuild_graph(model, state, work):
    """Exhaustive current universe, not a proposal list or clause scanner."""
    work.stats['graph_rebuilds'] += 1
    filled, marks = set(state.filled), mark_dict(state.marks)
    links = {p: [] for p, _ in model.roots if p not in filled}
    reverse, dependencies = [], {}
    for c in model.candidates:
        work.charge('candidate_checks')
        for p in {c.base} | {(x, y) for x, y, _ in c.marks}:
            dependencies.setdefault(p, []).append(c.name)
        if c.base in filled:
            work.stats['capacity_rejections'] += 1
            continue
        if any((x, y) in marks and marks[x, y] != value for x, y, value in c.marks):
            work.stats['marking_rejections'] += 1
            continue
        links[c.base].append(c.name)
        reverse.append((c.name, (c.base,)))
    graph = Graph(tuple((p, tuple(ids)) for p, ids in sorted(links.items())),
                  tuple(reverse), tuple((p, tuple(ids)) for p, ids in sorted(dependencies.items())))
    work.stats['maximum_frontier_points'] = max(work.stats['maximum_frontier_points'], len(links))
    work.stats['maximum_candidate_nodes'] = max(work.stats['maximum_candidate_nodes'], len(reverse))
    work.stats['maximum_incidence_edges'] = max(work.stats['maximum_incidence_edges'], len(reverse))
    return graph


def place(state, candidate, roots):
    require(candidate.base not in state.filled, 'unit capacity cannot exceed one')
    marks = mark_dict(state.marks)
    for x, y, value in candidate.marks:
        require((x, y) not in marks or marks[x, y] == value, 'all extended m overlaps agree')
        marks[x, y] = value
    # There is only one positive support point. Its explicit root remains the
    # minimum point generation, so the tile generation is root+1, never its index.
    generation = roots[candidate.base] + 1
    return State(state.placements + ((candidate.name, generation),),
                 tuple(sorted(state.filled + (candidate.base,))), mark_tuple(marks))


def check_complete_solution(model, state, roots, by_name, work):
    """Recompute whole required t totals and all m overlaps from base data."""
    work.stats['complete_solutions_checked'] += 1
    totals, marks, selected = {p: 0 for p in roots}, mark_dict(model.fixed_marks), set()
    for name, generation in state.placements:
        work.charge('candidate_checks')
        require(name in by_name and name not in selected, 'whole unique selected inventory')
        c = by_name[name]; selected.add(name); totals[c.base] += 1
        require(generation == roots[c.base] + 1, 'actual tile generation from root')
        for x, y, value in c.marks:
            require((x, y) not in marks or marks[x, y] == value, 'complete solution m agreement')
            marks[x, y] = value
    require(all(value == 1 for value in totals.values()), 'all required t totals exactly one')
    require(state.filled == tuple(sorted(roots)) and state.marks == mark_tuple(marks),
            'complete recorded state equals full base-data recomposition')


def solve(model, *, maximum_nodes, maximum_candidate_checks, maximum_trace_events):
    """First exact solution, entire finite exhaustion, or declared-budget UNKNOWN.

    Every child receives a new frozen State; parent state is never edited. The
    trace records all restores that fit the declared trace budget. No failed
    child is excluded outside its exact parent menu and no learned rule is added.
    """
    work = Work(maximum_nodes, maximum_candidate_checks, maximum_trace_events)
    require(type(model) is Model, 'exact immutable model')
    initial = State(marks=mark_tuple(mark_dict(model.fixed_marks)))
    solution, reason = None, None
    try:
        roots, by_name = validate_model(model, work)
        initial = State(marks=mark_tuple(mark_dict(model.fixed_marks)))

        def visit(state):
            work.charge('nodes')
            graph = rebuild_graph(model, state, work)
            domains = graph.point_candidates
            work.emit('graph', state, point_candidates=[[list(p), list(ids)] for p, ids in domains],
                      candidate_points=[[name, [list(p) for p in points]] for name, points in graph.candidate_points],
                      dependencies=[[list(p), list(ids)] for p, ids in graph.dependencies],
                      frontier_generations=[[*p, roots[p]] for p, _ in domains])
            dead = [p for p, ids in domains if not ids]
            if dead:
                work.emit('dead', state, points=[list(p) for p in dead])
                return None
            if not domains:
                check_complete_solution(model, state, roots, by_name, work)
                work.emit('solution', state)
                return state
            forced = [(p, ids) for p, ids in domains if len(ids) == 1]
            p, ids = min(forced or list(domains), key=lambda item: (roots[item[0]], len(item[1]), item[0]))
            kind = 'forced' if forced else 'branch'
            if not forced:
                work.stats['branch_decisions'] += 1
            work.emit(kind, state, point=list(p), candidates=list(ids), generation=roots[p])
            for name in ids:
                child = place(state, by_name[name], roots)
                work.stats['placements'] += 1
                work.stats['forced_placements'] += int(bool(forced))
                work.emit('place', child, candidate=name, parent_state=state_wire(state))
                try:
                    found = visit(child)
                finally:
                    # No mutable t/m/graph/generation/cache state was shared.
                    work.stats['restores'] += 1
                    work.emit('restore', state, from_candidate=name)
                if found is not None:
                    return found
                work.stats['backtracks'] += 1
            return None

        solution = visit(initial)
        status = 'FOUND' if solution is not None else 'EXHAUSTED_FINITE_MARKED_MODEL'
        work.emit('finished', initial, status=status)
    except BudgetExceeded as error:
        status, solution, reason = 'UNKNOWN', None, str(error)
    return {'schema': 'finite-unit-point-gcts-result-v1', 'version': VERSION,
            'status': status, 'unknown_reason': reason, 'model': model_wire(model),
            'solution': None if solution is None else state_wire(solution),
            'root_state': state_wire(initial), 'root_state_persistent': True,
            'limits': dict(work.limits), 'work_counts': dict(work.counts), 'stats': dict(work.stats),
            'trace': work.trace, 'trace_complete': status != 'UNKNOWN',
            'scope': 'finite_identity_grounded_single_unit_support_only',
            'independent_oracle_checked': False, 'full_contract_qualified': False,
            'learned_clause_soundness_qualified': False, 'resource_qualified': False}


def build_cnf_model(variable_count, clauses, *, active_guards, seed_bits,
                    maximum_candidates):
    """CNF literal (i,b) is true iff variable i equals exact bit b.

    Tuples are input containers, not a computed clause filter. All clause tuple
    candidates are built, including forbidden ones. Seed bits become explicit
    boundary m assignments; they are never inserted as pre-selected candidates.
    Changing active_guards creates a fresh marking version/model, not a mutation.
    """
    n, cap = integer(variable_count, 0), integer(maximum_candidates, 1)
    require(type(clauses) is tuple and type(active_guards) is tuple and type(seed_bits) is tuple,
            'immutable explicit clauses/active-guard indices/seed-bit pairs')
    if n + 2*len(clauses) > MAXIMUM_ROOTS:
        raise BudgetExceeded('declared root-point calibration ceiling')
    needed = 2*n + len(clauses)
    if needed > cap:
        raise BudgetExceeded('declared builder candidate limit')
    for clause in clauses:
        require(type(clause) is tuple, 'each clause is an ordered literal tuple')
        seen = set()
        for literal in clause:
            require(type(literal) is tuple and len(literal) == 2, 'literal pair (variable, satisfying bit)')
            i, bit = integer(literal[0], 0), integer(literal[1], 0)
            require(i < n and bit in (0, 1) and i not in seen, 'distinct clause variable and exact bit')
            seen.add(i)
        if len(clause) >= cap.bit_length():
            raise BudgetExceeded('declared builder candidate limit')
        needed += 1 << len(clause)
        if needed > cap:
            raise BudgetExceeded('declared builder candidate limit')
    guards = set()
    for c in active_guards:
        integer(c, 0); require(c < len(clauses) and c not in guards, 'unique active clause index')
        guards.add(c)
    fixed, seeded = [], set()
    for entry in seed_bits:
        require(type(entry) is tuple and len(entry) == 2, 'seed boundary (variable, bit)')
        i, bit = integer(entry[0], 0), integer(entry[1], 0)
        require(i < n and bit in (0, 1) and i not in seeded, 'unique valid seed bit')
        seeded.add(i); fixed.append((6*i, 2, bit))
    roots, candidates = [((6*i, 0), 0) for i in range(n)], []
    for i in range(n):
        for bit in (0, 1):
            candidates.append(Candidate('B_'+str(i)+'_'+str(bit), (6*i, 0), ((6*i, 2, bit),)))
    for c, clause in enumerate(clauses):
        roots.extend((((6*c, 6), 0), ((6*c+2, 6), 0)))
        forbidden = tuple(1-bit for _, bit in clause)
        for bits in product((0, 1), repeat=len(clause)):
            marks = tuple((6*i, 2, bit) for (i, _), bit in zip(clause, bits))
            marks += ((6*c+2, 8, int(bits == forbidden)),)
            candidates.append(Candidate('A_'+str(c)+'_'+''.join(map(str, bits)), (6*c, 6), marks))
        candidates.append(Candidate('R_'+str(c), (6*c+2, 6), ((6*c+2, 8, 0),) if c in guards else ()))
    require(len(candidates) == needed, 'whole declared inventory; never trim to a budget prefix')
    marking_version = VERSION + ':guards=' + ','.join(map(str, sorted(guards)))
    return Model(tuple(sorted(roots)), tuple(candidates), tuple(sorted(fixed)), marking_version)
