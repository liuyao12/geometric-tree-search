"""Frozen equality-free clause problems and finite-model verification."""

from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from random import Random
import re


ROOT = Path(__file__).resolve().parent
X, Y, Z = '?X', '?Y', '?Z'


def positive(pred, *args):
    return True, pred, args


def negative(pred, *args):
    return False, pred, args


def route_tree(rng, depth, width):
    """The backbone is one of several routes sharing the same local predicates."""
    edges = [(i, i + 1) for i in range(depth)]
    nxt = depth + 1
    for i in range(depth):
        for _ in range(rng.randint(1, width)):
            edges.append((i, nxt))
            tip = nxt
            nxt += 1
            for _ in range(rng.randrange(3)):
                edges.append((tip, nxt))
                tip = nxt
                nxt += 1
    return edges


def relay(rng, *, depth=None, width=None):
    depth = rng.randint(3, 7) if depth is None else depth
    width = rng.randint(2, 4) if width is None else width
    edges = route_tree(rng, depth, width)

    def site(index):
        return 'site', f'node{index}'

    clauses = [(positive('reached', site(0)),), (negative('reached', site(depth)),)]
    clauses += [(positive('edge', site(a), site(b)),) for a, b in edges]
    clauses.append((negative('reached', X), negative('edge', X, Y), positive('reached', Y)))
    return clauses


def nested(rng):
    depth, width = rng.randint(3, 6), rng.randint(2, 3)
    edges = route_tree(rng, depth, width)

    def state(index, payload):
        return 'config', f'node{index}', payload

    goal = 'start'
    for _ in range(depth):
        goal = 'tick', goal
    clauses = [(positive('at', state(0, 'start')),), (negative('at', state(depth, goal)),)]
    clauses += [(negative('at', state(a, X)), positive('at', state(b, ('tick', X))))
                for a, b in edges]
    return clauses


def join_routes(rng):
    depth = rng.randint(2, 4)
    clauses = [(positive('stage', 'step0', 'key'),), (negative('stage', f'step{depth}', 'key'),)]
    for stage in range(depth):
        start, end = f'step{stage}', f'step{stage + 1}'
        clauses.extend((
            (negative('stage', start, X), positive('left', start, ('pair', X, 'tag'))),
            (negative('stage', start, X), positive('right', start, ('pair', X, 'tag'))),
            (negative('left', start, ('pair', X, Y)), negative('right', start, ('pair', X, Y)),
             positive('stage', end, X))))
        for decoy in range(rng.randint(3, 7)):
            wrong = f'foil{stage}_{decoy}'
            choice = rng.choice(('seed', 'left', 'right'))
            if choice == 'seed':
                clauses.append((positive('stage', start, wrong),))
            else:
                clauses.append((positive(choice, start, ('pair', 'key', wrong)),))
    return clauses


def by_cases(rng):
    branches = rng.randint(2, 4)
    clauses = [(negative('done', 'origin'),)]
    clauses += [tuple(positive('route', f'branch{i}', 'origin') for i in range(branches))]
    for branch in range(branches):
        start = f'branch{branch}'
        for step in range(rng.randint(1, 3)):
            nxt = f'branch{branch}_{step}'
            clauses.append((negative('route', start, X), positive('route', nxt, X)))
            for j in range(rng.randint(1, 4)):
                wrong = f'foil{branch}_{step}_{j}'
                clauses.append((negative('route', start, X), positive('route', wrong, ('tag', X))))
                if rng.choice((True, False)):
                    clauses.append((negative('route', wrong, X), positive('other', X)))
            start = nxt
        clauses.append((negative('route', start, X), positive('done', X)))
    return clauses


def factors(rng):
    clauses = [
        (positive('a', ('wrap', X, 'main')), positive('a', ('wrap', Y, 'main'))),
        (negative('b', ('tag', X, 'main')), negative('b', ('tag', Y, 'main'))),
    ]
    middle = rng.randint(1, 3)
    start = 'a'
    for i in range(middle):
        end = 'b' if i == middle - 1 else f'mid{i}'
        inc = 'wrap' if start == 'a' else 'tag'
        clauses.append((negative(start, (inc, X, 'main')), positive(end, ('tag', X, 'main'))))
        for j in range(rng.randint(3, 7)):
            other = f'decoy{i}_{j}'
            clauses.append((negative(start, (inc, X, 'main')), positive(end, ('tag', X, other))))
            if rng.choice((True, False)):
                clauses.append((negative(end, ('tag', X, other)), positive(f'edge{i}', X)))
        start = end
    return clauses


def counterexample(number):
    kind, variant = number % 3, number // 3
    if kind == 0:
        size = 4 + variant
        mid = size - 2
        values = tuple(f'node{i}' for i in range(size))
        clauses = [
            (positive('reached', values[0]),), (negative('reached', values[-1]),),
            (negative('reached', X), negative('road', X, Y), positive('reached', Y)),
        ]
        roads = tuple((i, i + 1) for i in range(mid))
        roads += ((size - 1, 0),)
        clauses += [(positive('road', values[a], values[b]),) for a, b in roads]
        model = dict(size=size, constants=dict(zip(values, range(size))), functions={},
                     predicates={'reached': tuple((i,) for i in range(size - 1)), 'road': roads})
        return 'disconnected-relay', clauses, model
    if kind == 1:
        size = 2 + variant
        clauses = [
            (positive('choose', 'origin'), positive('alternate', 'origin')),
            (negative('choose', X), positive('reached', X)),
            (negative('alternate', X), positive('failed', X)),
            (negative('failed', 'origin'),),
        ]
        constants = {'origin': 0}
        for i in range(1, size):
            other = f'node{i}'
            constants[other] = i
            clauses.append((positive('alternate', other),))
        model = dict(size=size, constants=constants, functions={},
                     predicates={'choose': ((0,),), 'alternate': tuple((i,) for i in range(1, size)),
                                 'reached': ((0,),), 'failed': tuple((i,) for i in range(1, size))})
        return 'open-disjunction', clauses, model
    size = 3 + variant
    clauses = [
        (positive('reached', 'start'),),
        (negative('reached', X), positive('reached', ('f', X))),
        (negative('reached', 'sink'),),
    ]
    term = 'start'
    for _ in range(variant + 1):
        term = 'f', term
    clauses.append((positive('reached', term),))
    model = dict(size=size, constants={'start': 0, 'sink': size - 1},
                 functions={'f': tuple((i + 1) % (size - 1) for i in range(size - 1)) + (size - 1,)},
                 predicates={'reached': tuple((i,) for i in range(size - 1))})
    return 'finite-term-orbit', clauses, model


def verify_countermodel(clauses, model):
    """Evaluate every universally quantified instance in an explicit finite model."""
    size = model['size']
    if type(size) is not int or size <= 0:
        raise ValueError('empty or invalid model domain')
    domain = range(size)
    constants = model['constants']
    functions = model['functions']
    predicates = {k: set(map(tuple, v)) for k, v in model['predicates'].items()}
    predicate_arities = {}
    function_arities = {}
    required_constants = set()

    def signature(term):
        if isinstance(term, str):
            if not term.startswith('?'):
                required_constants.add(term)
            return
        name, *args = term
        if function_arities.setdefault(name, len(args)) != len(args):
            raise ValueError(f'inconsistent arity for {name}')
        for arg in args:
            signature(arg)

    for clause in clauses:
        for _, pred, args in clause:
            if predicate_arities.setdefault(pred, len(args)) != len(args):
                raise ValueError(f'inconsistent arity for {pred}')
            for arg in args:
                signature(arg)

    def within_domain(element):
        return type(element) is int and element in domain

    if required_constants != constants.keys() or not all(map(within_domain, constants.values())):
        raise ValueError('missing or invalid constant interpretation')
    if function_arities.keys() != functions.keys() or predicate_arities.keys() != predicates.keys():
        raise ValueError('model signature differs from the clauses')
    for name, table in functions.items():
        if len(table) != size ** function_arities[name] or not all(map(within_domain, table)):
            raise ValueError(f'incomplete or invalid function table for {name}')
    for name, relation in predicates.items():
        if any(len(row) != predicate_arities[name] or not all(map(within_domain, row)) for row in relation):
            raise ValueError(f'invalid predicate relation for {name}')

    def variables(term):
        if isinstance(term, str):
            return {term} if term.startswith('?') else set()
        return set().union(*(variables(a) for a in term[1:]))

    def value(term, env):
        if isinstance(term, str):
            return env[term] if term.startswith('?') else constants[term]
        name, *children = term
        offset = 0
        for child in children:
            offset = size * offset + value(child, env)
        return functions[name][offset]

    for clause in clauses:
        vars_ = sorted(set().union(*(variables(t) for _, _, args in clause for t in args)))
        for assignment in product(domain, repeat=len(vars_)):
            env = dict(zip(vars_, assignment))
            if not any((tuple(value(t, env) for t in args) in predicates[pred]) == sign
                       for sign, pred, args in clause):
                raise ValueError(f'finite model falsifies clause {clause} at {env}')
    return True


def anonymize(clauses, goal_index, rng):
    """Randomize opaque symbols and non-goal order. The final clause seeds goal guidance."""
    mapping = {}

    def rename(name):
        if name not in mapping:
            token = f'n{rng.getrandbits(48):012x}'
            if token in mapping.values():
                raise ValueError('synthetic symbol collision')
            mapping[name] = token
        return mapping[name]

    def rename_term(term):
        if isinstance(term, str):
            return term if term.startswith('?') else rename(term)
        head, *args = term
        return rename(head), *(rename_term(t) for t in args)

    def rename_clause(clause):
        literals = [(sign, rename(pred), tuple(rename_term(t) for t in args)) for sign, pred, args in clause]
        rng.shuffle(literals)
        return tuple(literals)

    out = [rename_clause(clause) for clause in clauses]
    goal = out.pop(goal_index)
    rng.shuffle(out)
    return (*out, goal)


def synthetic_cases():
    groups = (
        ('train', 'guarded-relay', relay, 1, 15, 90731),
        ('train', 'nested-transitions', nested, 1, 15, 48317),
        ('calibration', 'parallel-join', join_routes, 1, 12, 23221),
        ('test', 'proof-by-cases', by_cases, 0, 12, 35051),
        ('test', 'resolution-with-factoring', factors, 1, 12, 84017),
    )
    for split, family, builder, goal_index, count, seed in groups:
        for index in range(count):
            rng = Random(seed + index)
            clauses = anonymize(builder(rng), goal_index, rng)
            yield dict(id=f'{family}-{index + 1:02}', family=family, split=split,
                       clauses=clauses, expected='provable', query_seed='negated-goal')
    for i in range(6):
        family, raw, model = counterexample(i)
        goal = raw.pop((1, 3, 2)[i % 3])
        clauses = (*raw, goal)
        verify_countermodel(clauses, model)
        yield dict(id=f'{family}-{i // 3 + 1:02}', family=family, split='test',
                   clauses=clauses, expected='satisfiable', model=model, query_seed='negated-goal')


TOKEN = re.compile(r"\s+|%[^\n]*|[A-Za-z][A-Za-z0-9_]*|[0-9]+|'[A-Za-z0-9_./-]+'|[(),.|~]")
SYMBOL = re.compile(r'[a-z][A-Za-z0-9_]*')
VARIABLE = re.compile(r'[A-Z][A-Za-z0-9_]*')
LABEL = re.compile(r"[a-z][A-Za-z0-9_]*|[0-9]+|'[A-Za-z0-9_./-]+'")


def parse_tptp_cnf(source, *, with_roles=False):
    """Parse the plain, self-contained equality-free CNF exercised by the cohort."""
    tokens = []
    end = 0
    for token in TOKEN.finditer(source):
        if token.start() != end:
            raise ValueError(f'unsupported TPTP syntax at offset {end}')
        end = token.end()
        word = token.group()
        if not word.isspace() and not word.startswith('%'):
            tokens.append(word)
    if end != len(source):
        raise ValueError(f'unsupported TPTP syntax at offset {end}')
    stream = iter(tokens)
    current = next(stream, None)
    functions, predicates, labels = {}, {}, set()

    def take(expected=None):
        nonlocal current
        word = current
        if word is None or (expected is not None and word != expected):
            raise ValueError(f'expected {expected!r}, got {word!r}')
        current = next(stream, None)
        return word

    def arity(symbols, name, args):
        if symbols.setdefault(name, len(args)) != len(args):
            raise ValueError(f'inconsistent arity for {name}')

    def args():
        if current != '(':
            return ()
        take('(')
        out = [term()]
        while current == ',':
            take(',')
            out.append(term())
        take(')')
        return tuple(out)

    def term():
        name = take()
        if VARIABLE.fullmatch(name):
            return '?' + name
        if not SYMBOL.fullmatch(name):
            raise ValueError(f'unsupported TPTP term {name!r}')
        children = args()
        arity(functions, name, children)
        return (name, *children) if children else name

    def literal():
        sign = current != '~'
        if not sign:
            take('~')
        name = take()
        if not SYMBOL.fullmatch(name):
            raise ValueError(f'unsupported TPTP predicate {name!r}')
        children = args()
        arity(predicates, name, children)
        return sign, name, children

    clauses, roles = [], []
    while current is not None:
        take('cnf')
        take('(')
        label = take()
        if not LABEL.fullmatch(label) or label in labels:
            raise ValueError(f'invalid or duplicate TPTP label {label!r}')
        labels.add(label)
        take(',')
        role = take()
        if role not in ('axiom', 'hypothesis', 'negated_conjecture'):
            raise ValueError(f'unsupported TPTP role {role!r}')
        take(',')
        wrapped = current == '('
        if wrapped:
            take('(')
        out = [literal()]
        while current == '|':
            take('|')
            out.append(literal())
        if wrapped:
            take(')')
        take(')')
        take('.')
        clauses.append(tuple(out))
        roles.append(role)
    if not clauses or functions.keys() & predicates.keys():
        raise ValueError('unexpected empty problem or shared term and predicate symbol')
    return (tuple(clauses), tuple(roles)) if with_roles else tuple(clauses)


def external_cases():
    """Read the byte-pinned original texts, with TPTP's unsatisfiable labels."""
    data = ROOT / 'data'
    manifest = json.loads((data / 'tptp-manifest.json').read_text())
    for filename, source in manifest['files'].items():
        raw = (data / filename).read_bytes()
        if len(raw) != source['bytes'] or sha256(raw).hexdigest() != source['sha256']:
            raise ValueError(f'TPTP input changed: {filename}')
        content = raw.decode()
        if not re.search(r'^% Status\s*:\s*Unsatisfiable\s*$', content, re.MULTILINE):
            raise ValueError(f'TPTP status changed: {filename}')
        clauses, roles = parse_tptp_cnf(content, with_roles=True)
        if len(clauses) != source['clauses']:
            raise ValueError(f'TPTP clause count changed: {filename}')
        marked = [i for i, role in enumerate(roles) if role == 'negated_conjecture']
        if marked and marked[-1] != len(clauses) - 1:
            goal = marked[-1]
            clauses = (*clauses[:goal], *clauses[goal + 1:], clauses[goal])
        yield dict(id=Path(filename).stem, family=f'TPTP-{filename[:3]}', split='external',
                   clauses=clauses, expected='provable', source=source,
                   query_seed='last-negated-conjecture' if marked else 'last-input-fallback',
                   negated_conjectures=len(marked))


def cases():
    return tuple(synthetic_cases()) + tuple(external_cases())

