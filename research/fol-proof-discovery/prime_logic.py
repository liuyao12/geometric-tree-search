"""Formula geometry and the declared elementary arithmetic boundary."""

from itertools import product
from heapq import heappop, heappush

from kernel import GivenClauseSearch, Limit, geometry, is_variable, occurs, substitute, validate_input


def atom(name, *args):
    return 'atom', name, args


def all_(name, body):
    return 'all', name, body


def some(name, body):
    return 'some', name, body


def both(*forms):
    return 'and', *forms


def either(*forms):
    return 'or', *forms


def neg(form):
    return 'not', form


def implies(left, right):
    return either(neg(left), right)


ZERO, ONE = 'zero', 'one'
N, P, D, M = '@n', '@p', '@d', '@m'
X, Y, Z = '@x', '@y', '@z'


def lt(a, b):
    return atom('lt', a, b)


def le(a, b):
    return atom('le', a, b)


def eq(a, b):
    return atom('eq', a, b)


def divides(a, b):
    return atom('divides', a, b)


def prime(a):
    return atom('prime', a)


def add(a, b):
    return 'plus', a, b


def successor(a):
    return add(a, ONE)


def multiply(a, b):
    return 'mul', a, b


def close(form, *names):
    for name in reversed(names):
        form = all_(name, form)
    return form


def law(premises, conclusion, *names):
    return close(implies(both(*premises), conclusion), *names)


def arithmetic_boundary():
    # These are trusted boundary laws of ordered natural arithmetic. This
    # experiment does not derive them from the Peano successor axioms.
    return {
        'positive-one': lt(ZERO, ONE),
        'positive-successor': all_(X, lt(ZERO, successor(X))),
        'greater-than-one-is-positive': law((lt(ONE, X),), lt(ZERO, X), X),
        'successor-of-positive': law((lt(ZERO, X),), lt(ONE, successor(X)), X),
        'no-positive-below-zero': law((lt(ZERO, X),), neg(le(X, ZERO)), X),
        'positive-product': law((lt(ZERO, X), lt(ZERO, Y)), lt(ZERO, multiply(X, Y)), X, Y),
        'order-totality': close(either(le(X, Y), lt(Y, X)), X, Y),
        'successor-order-split': law((le(X, successor(Y)),), either(le(X, Y), eq(X, successor(Y))), X, Y),
        'divides-product-left': close(divides(X, multiply(X, Y)), X, Y),
        'divides-product-right': close(divides(Y, multiply(X, Y)), X, Y),
        'divides-reflexive': all_(X, divides(X, X)),
        'divides-product-extension': law((divides(D, X),), divides(D, multiply(X, Y)), D, X, Y),
        'divides-transitive': law((divides(X, Y), divides(Y, Z)), divides(X, Z), X, Y, Z),
        'divisor-substitution': law((eq(X, Y), divides(Y, Z)), divides(X, Z), X, Y, Z),
        'one-has-no-larger-divisor': law((lt(ONE, D),), neg(divides(D, ONE)), D),
        'prime-greater-than-one': law((prime(X),), lt(ONE, X), X),
        # Classical case form of prime(x) iff x > 1 and x has no
        # divisor strictly between 1 and x.
        'prime-definition-cases': law((lt(ONE, X),), either(prime(X),
            some(D, both(lt(ONE, D), lt(D, X), divides(D, X)))), X),
        'prime-definition-exclusion': law((prime(X), lt(ONE, D), lt(D, X)),
                                           neg(divides(D, X)), X, D),
        'divides-additive-cancellation': law((divides(D, X), divides(D, add(X, Y))),
                                             divides(D, Y), D, X, Y),
    }


PRIME_DIVISOR = all_(N, implies(lt(ONE, N), some(P, both(prime(P), divides(P, N)))))
UNBOUNDED_PRIMES = all_(N, some(P, both(prime(P), lt(N, P))))


def auxiliary_goals():
    """Enumerate a fixed bounded-universal witness grammar."""
    for relation in ('divides', 'le', 'lt', 'eq'):
        for bound in ('le', 'lt'):
            yield f'bounded-positive-{bound}-{relation}', all_(N, some(M, both(
                lt(ZERO, M), all_(D, implies(both(lt(ZERO, D), atom(bound, D, N)),
                                              atom(relation, D, M))))))


def replace(form, name, value):
    """Substitute an eigenconstant or bound variable for a free name."""
    tag = form[0]
    if tag == 'atom':
        return atom(form[1], *(substitute(t, {name: value}) for t in form[2]))
    if tag in ('all', 'some'):
        return form if name == form[1] else (tag, form[1], replace(form[2], name, value))
    return (tag, *(replace(f, name, value) for f in form[1:]))


def obligations(goal, method):
    if method == 'direct':
        return (((), goal),)
    if goal[0] != 'all':
        raise ValueError('induction requires a universal natural-number variable')
    _, name, body = goal
    n, i = '_induction_n', '@induction_i'
    if method == 'strong-induction':
        hyp = all_(i, implies(lt(i, n), replace(body, name, i)))
        return (((hyp,), replace(body, name, n)),)
    if method == 'induction':
        return (((), replace(body, name, ZERO)),
                ((replace(body, name, n),), replace(body, name, successor(n))))
    raise ValueError('unknown proof method')


def clauses(form, scope, positive=True):
    """Clausify one closed formula with its own fresh variables and Skolems."""
    symbols = iter(range(10_000))

    def expand(node, sign, env, universals):
        tag, *parts = node
        if tag == 'atom':
            name, args = parts
            return (((sign, name, tuple(substitute(t, env) for t in args)),),)
        if tag == 'not':
            return expand(parts[0], not sign, env, universals)
        if tag in ('all', 'some'):
            name, body = parts
            index = next(symbols)
            if (tag == 'all') == sign:
                letter = f'?u{scope}_{index}'
                return expand(body, sign, {**env, name: letter}, (*universals, letter))
            symbol = f'_sk{scope}_{index}'
            witness = (symbol, *universals) if universals else symbol
            return expand(body, sign, {**env, name: witness}, universals)
        if tag not in ('and', 'or'):
            raise ValueError(f'unsupported formula: {tag}')
        arms = [expand(part, sign, env, universals) for part in parts]
        if (tag == 'and') == sign:
            return tuple(clause for arm in arms for clause in arm)
        return tuple(tuple(literal for row in combination for literal in row)
                     for combination in product(*arms))

    return expand(form, positive, {}, ())


def marked_arguments(left, right, counts, check_time):
    """Join two nested term diagrams at corresponding lattice addresses.

    A port is a root in row zero. Descending an argument moves to the next
    row and extends the horizontal address by one radix digit. A variable
    can fill a whole subdiagram and must agree at every occurrence.
    """
    def sockets(args, col, row):
        if len(args) >= 16:
            raise ValueError('mark arity exceeds the lattice radix')
        return {(16*col+i, row): term for i, term in enumerate(args, 1)}

    left_marks, right_marks = sockets(left, 0, 0), sockets(right, 0, 0)
    if left_marks.keys() != right_marks.keys():
        return None
    bindings = {}
    while left_marks:
        check_time()
        address, a = left_marks.popitem()
        b = right_marks.pop(address)
        col, row = address
        x, y = substitute(a, bindings), substitute(b, bindings)
        counts['marked_point_joins'] += 1
        counts['solved_equations'] += 1
        if x == y:
            continue
        if not is_variable(x) and is_variable(y):
            x, y = y, x
        if is_variable(x):
            if occurs(x, y):
                return None
            fill = {x: y}
            bindings = {v: substitute(t, fill) for v, t in bindings.items()}
            bindings[x] = y
            continue
        if not isinstance(x, tuple) or not isinstance(y, tuple) or (x[0], len(x)) != (y[0], len(y)):
            counts['marked_point_conflicts'] += 1
            return None
        left_marks.update(sockets(x[1:], col, row+1))
        right_marks.update(sockets(y[1:], col, row+1))
    return bindings


class MarkedSearch(GivenClauseSearch):
    unify_arguments = staticmethod(marked_arguments)


class FocusedSearch(MarkedSearch):
    """Keep the geometry of the boundary in place and grow from the goal."""

    def __init__(self, inputs, support_start, seconds, width, depth, *,
                 max_steps, max_offers, max_nodes, preference):
        super().__init__(inputs, None, max_steps, seconds, max_offers, max_nodes)
        self.support_start = support_start
        self.width = width
        self.depth = depth
        self.heap = []
        self.preference = preference

    def add(self, row, record, *, from_goal=False):
        if record['rule'] != 'input':
            _, depth = geometry(row)
            if depth > self.depth or len(set(row)) > self.width:
                self.counts['bounded_placements'] += 1
                return None
        before = len(self.nodes)
        root = super().add(row, record, from_goal=from_goal)
        if root is None and len(self.nodes) > before:
            a = self.attributes[before]
            if self.preference == 'goal':
                key = (a['symbols']-2*a['goal_overlap'], a['literals'], before)
            else:
                key = (a['symbols'], a['literals'], before)
            heappush(self.heap, (key, before))
        return root

    def pick(self):
        self.check_time()
        if self.counts['given'] % 5 == 4:
            number = next(iter(self.pending))
            self.counts['age_slots'] += 1
        else:
            while self.heap:
                _, number = heappop(self.heap)
                if number in self.pending:
                    break
            else:
                raise RuntimeError('support frontier and priority queue diverged')
        self.counts['given'] += 1
        del self.pending[number]
        return number

    def run(self):
        try:
            validate_input(self.clauses, self.check_time)
            self.goal = {(p, len(args)) for row in self.clauses[self.support_start:]
                         for _, p, args in row}
            for i, clause in enumerate(self.clauses):
                active_before = len(self.nodes)
                root = self.add(clause, dict(rule='input', source=i), from_goal=i >= self.support_start)
                if root is not None:
                    return self.result('proved', root)
                if i < self.support_start and len(self.nodes) > active_before:
                    for j, (sign, name, args) in enumerate(self.nodes[active_before]['clause']):
                        self.active[sign, name, len(args)].append((active_before, j))
                    del self.pending[active_before]
            while self.pending:
                self.check_time()
                if self.counts['given'] >= self.max_steps:
                    raise Limit('steps')
                root = self.activate(self.pick())
                if root is not None:
                    return self.result('proved', root)
            return self.result('unknown', limit='bounded-support')
        except Limit as limit:
            return self.result('unknown', limit=str(limit))
