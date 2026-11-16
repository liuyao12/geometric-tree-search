"""Fair, lifted resolution and factoring over equality-free CNF.

The given-clause index, separate parent scopes, self-resolution and proof
DAG follow the earlier lifted Wang search. This interface takes clauses
directly and keeps advisory scheduling outside inference generation.
"""

from collections import Counter, OrderedDict, defaultdict
from itertools import combinations, islice
from time import monotonic


FORMAT = "lifted-cnf-v1"
SHORTLIST = 12
AGE_PERIOD = 4


def is_variable(term):
    return isinstance(term, str) and term.startswith("?")


def variables(clause):
    names = set()

    def visit(term):
        if is_variable(term):
            names.add(term)
        elif isinstance(term, tuple):
            for child in term[1:]:
                visit(child)

    for _, _, args in clause:
        for term in args:
            visit(term)
    return names


def substitute(term, bindings):
    if isinstance(term, str):
        return bindings.get(term, term)
    return (term[0], *(substitute(child, bindings) for child in term[1:]))


def apply(clause, bindings):
    return tuple((sign, predicate, tuple(substitute(t, bindings) for t in args))
                 for sign, predicate, args in clause)


def skeleton(term):
    if isinstance(term, str):
        return "?" if is_variable(term) else term
    return (term[0], *map(skeleton, term[1:]))


def normalize(row):
    """Deduplicate literals and give variables stable first-use names."""
    def key(literal):
        sign, predicate, args = literal
        return repr((sign, predicate, tuple(map(skeleton, args)))), repr(literal)

    bindings = {}

    def rename(term):
        if is_variable(term):
            return bindings.setdefault(term, f"?v{len(bindings)}")
        if isinstance(term, tuple):
            return (term[0], *map(rename, term[1:]))
        return term

    ordered = sorted(set(row), key=key)
    renamed = ((sign, predicate, tuple(map(rename, args))) for sign, predicate, args in ordered)
    return tuple(sorted(renamed, key=repr)), bindings


def scope(clause, label):
    bindings = {name: f"?{label}{i}" for i, name in enumerate(sorted(variables(clause)))}
    return apply(clause, bindings)


def head(term):
    if isinstance(term, str):
        return term, 0
    return term[0], len(term)-1


def clash(left, right):
    return not is_variable(left) and not is_variable(right) and head(left) != head(right)


def occurs(variable, term):
    return variable == term if isinstance(term, str) else any(
        occurs(variable, child) for child in term[1:])


def unify(left, right, counts, check_time):
    """Return an idempotent most-general substitution, or None."""
    bindings = {}
    pending = list(reversed(list(zip(left, right))))
    while pending:
        check_time()
        raw_left, raw_right = pending.pop()
        x, y = substitute(raw_left, bindings), substitute(raw_right, bindings)
        counts["solved_equations"] += 1
        if x == y:
            continue
        if not is_variable(x) and is_variable(y):
            x, y = y, x
        if is_variable(x):
            if occurs(x, y):
                return None
            update = {x: y}
            bindings = {v: substitute(t, update) for v, t in bindings.items()}
            bindings[x] = y
        elif clash(x, y):
            return None
        else:
            pending.extend(reversed(list(zip(x[1:], y[1:]))))
    return bindings


def validate_input(clauses, check_time):
    predicates, functions = {}, {}

    def arity(table, symbol, n):
        if table.setdefault(symbol, n) != n:
            raise ValueError(f"inconsistent arity for {symbol!r}")

    def term(t):
        if isinstance(t, str) and t and t != "?":
            if not is_variable(t):
                arity(functions, t, 0)
            return
        if (not isinstance(t, tuple) or len(t) < 2 or not isinstance(t[0], str)
                or not t[0] or is_variable(t[0])):
            raise ValueError(f"invalid first-order term {t!r}")
        arity(functions, t[0], len(t)-1)
        for child in t[1:]:
            term(child)

    if not isinstance(clauses, (tuple, list)):
        raise ValueError("clauses must be an ordered sequence")
    for clause in clauses:
        check_time()
        if not isinstance(clause, tuple):
            raise ValueError("each clause must be a tuple")
        for sign, predicate, args in clause:
            check_time()
            if (type(sign) is not bool or not isinstance(predicate, str)
                    or not predicate or predicate.startswith("?")
                    or predicate in {"=", "!=", "$equal", "$distinct"}
                    or not isinstance(args, tuple)):
                raise ValueError("expected an equality-free tuple literal")
            arity(predicates, predicate, len(args))
            for argument in args:
                term(argument)


def geometry(clause):
    """Size and depth used by all advisory modes."""
    def measure(term):
        if isinstance(term, str):
            return 1, 0
        stats = [measure(t) for t in term[1:]]
        return 1+sum(n for n, _ in stats), 1+max(d for _, d in stats)

    stats = [measure(term) for _, _, args in clause for term in args]
    return len(clause)+sum(n for n, _ in stats), max((d for _, d in stats), default=0)


class Limit(Exception):
    """A finite resource cap reached during a search."""


class GivenClauseSearch:
    unify_arguments = staticmethod(unify)

    def __init__(self, clauses, select, max_steps, seconds, max_offers, max_nodes):
        self.deadline = monotonic()+seconds
        self.clauses = clauses
        self.select = select
        self.max_steps, self.max_offers, self.max_nodes = max_steps, max_offers, max_nodes
        self.counts = Counter()
        self.nodes = []
        self.attributes = []
        self.seen = set()
        self.pending = OrderedDict()
        self.active = defaultdict(list)
        self.goal = set()

    def check_time(self):
        if monotonic() >= self.deadline:
            raise Limit("time")

    def add(self, row, record, *, from_goal=False):
        clause, renaming = normalize(row)
        self.check_time()
        if clause in self.seen:
            self.counts["duplicates"] += 1
            return None
        members = set(clause)
        if any((not s, p, args) in members for s, p, args in clause):
            self.counts["tautologies"] += 1
            return None
        if len(self.nodes) >= self.max_nodes:
            raise Limit("nodes")
        number = len(self.nodes)
        self.nodes.append(dict(record, clause=clause, renaming=renaming))
        self.seen.add(clause)
        self.counts["stored"] += 1
        if not clause:
            return number
        parents = record.get("parents", ())
        provenance = any(self.attributes[p]["origin_goal"] for p in parents) if parents else from_goal
        depth = (1+max(self.attributes[p]["derivation_depth"] for p in parents)) if parents else 0
        size, term_depth = geometry(clause)
        heads = {(predicate, len(args)) for _, predicate, args in clause}
        self.attributes.append(dict(id=number, arrival=number, clause=clause, literals=len(clause),
                                    symbols=size, depth=term_depth, variables=len(renaming),
                                    input=not parents, origin_goal=provenance,
                                    goal_overlap=len(heads & self.goal), derivation_depth=depth))
        self.pending[number] = self.counts["given"]
        return None

    def options(self, step):
        ids = list(islice(self.pending, SHORTLIST//2))
        ids.extend(reversed(list(islice(reversed(self.pending), SHORTLIST-len(ids)))))
        return tuple(dict(self.attributes[number], age=step-self.pending[number],
                          active_matches=sum(len(self.active.get((not sign, predicate, len(args)), ()))
                                             for sign, predicate, args in self.nodes[number]["clause"]))
                     for number in dict.fromkeys(ids))

    def pick(self):
        step = self.counts["given"]+1
        number = next(iter(self.pending))
        age_slot = step % AGE_PERIOD == 0
        if not age_slot and self.select is not None and len(self.pending) > 1:
            options = self.options(step)
            shortlisted = tuple(option["id"] for option in options)
            self.counts["guided"] += 1
            try:
                index = self.select(options, step)
                if type(index) is not int or not 0 <= index < len(options):
                    raise ValueError("selector returned an out-of-range candidate index")
                number = shortlisted[index]
            except Exception:
                # Advice can fail without losing any baseline work.
                self.counts["selector_errors"] += 1
        self.check_time()
        if age_slot:
            self.counts["age_slots"] += 1
        self.counts["given"] += 1
        del self.pending[number]
        return number

    def offer(self, left, first, right, second, *, factor=False):
        self.check_time()
        if self.counts["offers"] >= self.max_offers:
            raise Limit("offers")
        self.counts["offers"] += 1
        a, b = self.nodes[left]["clause"], self.nodes[right]["clause"]
        if any(clash(x, y) for x, y in zip(a[first][2], b[second][2])):
            self.counts["shallow_skips"] += 1
            return None
        scoped_a = scope(a, "L")
        scoped_b = scoped_a if factor else scope(b, "R")
        self.counts["unifications"] += 1
        bindings = self.unify_arguments(scoped_a[first][2], scoped_b[second][2],
                                        self.counts, self.check_time)
        if bindings is None:
            self.counts["failed_unifications"] += 1
            return None
        if factor:
            self.counts["factors"] += 1
            rest = scoped_a[:second]+scoped_a[second+1:]
            parents = (left,)
        else:
            self.counts["resolutions"] += 1
            rest = scoped_a[:first]+scoped_a[first+1:]+scoped_b[:second]+scoped_b[second+1:]
            parents = (left, right)
        return self.add(apply(rest, bindings),
                        dict(rule="factor" if factor else "resolve", parents=parents,
                             sites=(first, second), substitution=bindings))

    def activate(self, number):
        clause = self.nodes[number]["clause"]
        own = defaultdict(list)
        for index, (sign, predicate, args) in enumerate(clause):
            self.check_time()
            own[sign, predicate, len(args)].append(index)
        for indices in own.values():
            for i, j in combinations(indices, 2):
                result = self.offer(number, i, number, j, factor=True)
                if result is not None:
                    return result
        for i, (sign, predicate, args) in enumerate(clause):
            self.check_time()
            other_key = not sign, predicate, len(args)
            for other, j in self.active[other_key]:
                result = (self.offer(number, i, other, j) if sign
                          else self.offer(other, j, number, i))
                if result is not None:
                    return result
            # A clause may resolve with a second, independently scoped copy.
            if sign:
                for j in own.get(other_key, ()):
                    result = self.offer(number, i, number, j)
                    if result is not None:
                        return result
        for key, indices in own.items():
            self.active[key].extend((number, i) for i in indices)
        return None

    def certificate(self, root):
        needed, frontier = set(), [root]
        while frontier:
            number = frontier.pop()
            if number not in needed:
                needed.add(number)
                frontier.extend(self.nodes[number].get("parents", ()))
        order = sorted(needed)
        ids = {old: new for new, old in enumerate(order)}
        rows = []
        for number in order:
            node = dict(self.nodes[number])
            if "parents" in node:
                node["parents"] = tuple(ids[p] for p in node["parents"])
            rows.append(node)
        return dict(format=FORMAT, steps=rows, root=ids[root])

    def result(self, status, root=None, limit=None):
        return dict(status=status, limit=limit, steps=self.counts["given"], counters=dict(self.counts),
                    proof=self.certificate(root) if root is not None else None)

    def run(self):
        try:
            validate_input(self.clauses, self.check_time)
            if self.clauses:
                self.goal = {(p, len(args)) for _, p, args in self.clauses[-1]}
            for index, clause in enumerate(self.clauses):
                root = self.add(clause, dict(rule="input", source=index),
                                from_goal=index == len(self.clauses)-1)
                if root is not None:
                    return self.result("proved", root)
            while self.pending:
                self.check_time()
                if self.counts["given"] >= self.max_steps:
                    raise Limit("steps")
                root = self.activate(self.pick())
                if root is not None:
                    return self.result("proved", root)
            return self.result("saturated")
        except Limit as stop:
            return self.result("unknown", limit=str(stop))


def search(clauses, *, select=None, max_steps=600, seconds=0.5, seed_hint=0,
           max_offers=65_000, max_nodes=18_000):
    """Select an option by index on advisory turns and expand every legal inference.

    A fourth-step age reservation is independent of the policy.
    `seed_hint` permits uniform runner interfaces; randomness belongs in the
    selector. `saturated` reports queue exhaustion, not a countermodel.
    """
    if min(max_steps, seconds, max_offers, max_nodes) < 0:
        raise ValueError("search budgets must be nonnegative")
    return GivenClauseSearch(clauses, select, max_steps, seconds, max_offers, max_nodes).run()
