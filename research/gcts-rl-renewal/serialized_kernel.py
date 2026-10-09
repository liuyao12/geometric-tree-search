"""Fixed JSON certificate checker, with exact lemma interfaces and induction.

No syntax catalog, Python eval, dynamic rules, or import from logic.py. The
input declares the theory; acceptance is relative to those axioms and the
explicitly enabled nat-induction schema. This is a host checker, not a literal
TM. Native parser/recursion/memory limits and explicit work/byte limits return
unknown rather than refuting a certificate or a mathematical statement.
"""
import hashlib
import itertools
import json
import time

PROTOCOL = 'gcts-fol-1'

class Invalid(ValueError): pass
class Resource(Exception): pass

def canonical(request):
    return json.dumps(request, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('ascii')

def problem_hash(request):
    """Caller pins the agreed theory and target, excluding proof proposals."""
    problem={key:request[key] for key in ('protocol','theory','target')}
    return hashlib.sha256(canonical(problem)).hexdigest()

class Checker:
    def __init__(self, max_work):
        self.max_work = max_work
        self.stats = dict(work=0, ast_visits=0, rule_checks=0,
                          truth_assignments=0, blocks_checked=0, block_calls=0)
        self.blocks = {}

    def tick(self, kind=None):
        self.stats['work'] += 1
        if kind: self.stats[kind] += 1
        if self.max_work is not None and self.stats['work'] > self.max_work:
            raise Resource('work limit')

    def fields(self, d, keys):
        self.tick()
        if type(d) is not dict or set(d) != set(keys):
            raise Invalid('unexpected or missing fields')

    def string(self, x):
        self.tick()
        if type(x) is not str: raise Invalid('name must be a string')
        return x

    def sequence(self, x):
        self.tick()
        if type(x) is not list: raise Invalid('list required')
        return x

    def natural(self, x):
        self.tick()
        if type(x) is not int or x < 0: raise Invalid('nonnegative integer required')
        return x

    def signature(self, d):
        if type(d) is not dict: raise Invalid('signature object required')
        for name, arity in d.items(): self.string(name); self.natural(arity)
        return d

    def term(self, raw):
        self.tick('ast_visits'); a = self.sequence(raw)
        if len(a) == 2 and a[0] == 'var': return ('var', self.string(a[1]))
        if len(a) == 3 and a[0] == 'fun':
            name = self.string(a[1]); args = self.sequence(a[2])
            if name not in self.functions or self.functions[name] != len(args):
                raise Invalid('unknown function or wrong arity')
            return ('fun', name, tuple(self.term(t) for t in args))
        raise Invalid('malformed term')

    def formula(self, raw):
        self.tick('ast_visits'); a = self.sequence(raw)
        if not a: raise Invalid('empty formula')
        if len(a) == 3 and a[0] == 'eq': return ('eq', self.term(a[1]), self.term(a[2]))
        if len(a) == 3 and a[0] == 'pred':
            name = self.string(a[1]); args = self.sequence(a[2])
            if name not in self.predicates or self.predicates[name] != len(args):
                raise Invalid('unknown predicate or wrong arity')
            return ('pred', name, tuple(self.term(t) for t in args))
        if len(a) == 3 and a[0] == 'all':
            return ('all', self.string(a[1]), self.formula(a[2]))
        if len(a) == 2 and a[0] == 'not': return ('not', self.formula(a[1]))
        if len(a) == 3 and a[0] in ('imp', 'and', 'or'):
            return (a[0], self.formula(a[1]), self.formula(a[2]))
        if a == ['bot']: return ('bot',)
        raise Invalid('malformed formula')

    def term_free(self, t):
        self.tick()
        if t[0] == 'var': return {t[1]}
        return set().union(*(self.term_free(a) for a in t[2]))

    def free(self, a, bound=False):
        self.tick(); tag = a[0]
        if tag == 'all':
            found = self.free(a[2], bound)
            return found | {a[1]} if bound else found - {a[1]}
        if tag == 'eq': return self.term_free(a[1]) | self.term_free(a[2])
        if tag == 'pred': return set().union(*(self.term_free(t) for t in a[2]))
        if tag == 'bot': return set()
        return set().union(*(self.free(b, bound) for b in a[1:]))

    def subst_term(self, t, x, replacement):
        self.tick()
        if t[0] == 'var': return replacement if t[1] == x else t
        return ('fun', t[1], tuple(self.subst_term(a, x, replacement) for a in t[2]))

    def subst(self, a, x, replacement):
        self.tick(); tag = a[0]
        if tag == 'all':
            y, body = a[1:]
            if x == y or x not in self.free(body): return a
            if y in self.term_free(replacement):
                occupied = self.free(body, True) | self.term_free(replacement) | {x, y}
                j = 0
                while 'fresh' + str(j) in occupied: self.tick(); j += 1
                name = 'fresh' + str(j)
                body = self.subst(body, y, ('var', name)); y = name
            return ('all', y, self.subst(body, x, replacement))
        if tag == 'eq':
            return ('eq', self.subst_term(a[1], x, replacement), self.subst_term(a[2], x, replacement))
        if tag == 'pred':
            return ('pred', a[1], tuple(self.subst_term(t, x, replacement) for t in a[2]))
        if tag == 'bot': return a
        return (tag,) + tuple(self.subst(b, x, replacement) for b in a[1:])

    def tautology(self, a):
        atoms = set()
        def collect(b):
            self.tick()
            if b[0] in ('imp', 'and', 'or', 'not'):
                for child in b[1:]: collect(child)
            elif b[0] != 'bot': atoms.add(b)
        collect(a); atoms = sorted(atoms, key=repr)
        def truth(b, env):
            self.tick(); k = b[0]
            if k == 'bot': return False
            if k == 'not': return not truth(b[1], env)
            if k == 'imp': return not truth(b[1], env) or truth(b[2], env)
            if k == 'and': return truth(b[1], env) and truth(b[2], env)
            if k == 'or': return truth(b[1], env) or truth(b[2], env)
            return env[b]
        for bits in itertools.product((False, True), repeat=len(atoms)):
            self.tick('truth_assignments')
            if not truth(a, dict(zip(atoms, bits))): return False
        return True

    def induction(self, x, p):
        if 'nat-induction' not in self.schemas: raise Invalid('induction schema is not enabled')
        if self.functions.get('zero') != 0 or self.functions.get('succ') != 1:
            raise Invalid('induction requires zero and successor in the declared signature')
        base = self.subst(p, x, ('fun', 'zero', ()))
        step = ('all', x, ('imp', p, self.subst(p, x, ('fun', 'succ', (('var', x),)))))
        result = ('imp', ('and', base, step), ('all', x, p))
        for y in reversed(sorted(self.free(p) - {x})): result = ('all', y, result)
        return result

    def proof(self, lines, target, assumptions=()):
        self.sequence(lines)
        if not lines: raise Invalid('empty proof')
        proved = []; forbidden = set().union(*(self.free(a) for a in assumptions))
        for line in lines:
            self.tick('rule_checks')
            if type(line) is not dict or 'rule' not in line or 'formula' not in line:
                raise Invalid('proof line required')
            a = self.formula(line['formula']); rule = line['rule']; valid = False
            def fields(*parameters): self.fields(line, ('rule', 'formula') + parameters)
            def prior(index):
                self.natural(index)
                if index >= len(proved): raise Invalid('reference must strictly precede its use')
                return proved[index]
            if rule == 'axiom':
                fields('name'); name = self.string(line['name'])
                valid = name in self.axioms and a == self.axioms[name]
            elif rule == 'tautology': fields(); valid = self.tautology(a)
            elif rule == 'refl': fields(); valid = a[0] == 'eq' and a[1] == a[2]
            elif rule == 'instantiate':
                fields('universal', 'term'); u = self.formula(line['universal']); t = self.term(line['term'])
                valid = u[0] == 'all' and a == ('imp', u, self.subst(u[2], u[1], t))
            elif rule == 'distribute':
                fields('variable', 'antecedent', 'consequent')
                x = self.string(line['variable']); p = self.formula(line['antecedent']); q = self.formula(line['consequent'])
                valid = x not in self.free(p) and a == ('imp', ('all', x, ('imp', p, q)), ('imp', p, ('all', x, q)))
            elif rule == 'eq_subst':
                fields('variable', 'template', 'left', 'right')
                x = self.string(line['variable']); p = self.formula(line['template'])
                s = self.term(line['left']); t = self.term(line['right'])
                valid = a == ('imp', ('eq', s, t), ('imp', self.subst(p, x, s), self.subst(p, x, t)))
            elif rule == 'mp':
                fields('antecedent', 'implication')
                valid = prior(line['implication']) == ('imp', prior(line['antecedent']), a)
            elif rule == 'generalize':
                fields('variable', 'source'); x = self.string(line['variable'])
                valid = x not in forbidden and a == ('all', x, prior(line['source']))
            elif rule == 'induction':
                fields('variable', 'template'); x = self.string(line['variable']); p = self.formula(line['template'])
                valid = a == self.induction(x, p)
            elif rule == 'assumption':
                fields('index'); i = self.natural(line['index'])
                valid = i < len(assumptions) and a == assumptions[i]
            elif rule == 'block':
                fields('name', 'inputs'); name = self.string(line['name']); indices = self.sequence(line['inputs'])
                if name not in self.blocks: raise Invalid('block must be checked earlier; no recursion')
                premises, conclusion = self.blocks[name]
                valid = len(indices) == len(premises) and tuple(prior(i) for i in indices) == premises and a == conclusion
                self.tick('block_calls')
            else: raise Invalid('unknown proof rule')
            if not valid: raise Invalid('invalid ' + str(rule) + ' instance')
            proved.append(a)
        if proved[-1] != target: raise Invalid('last line differs from the target')

    def request(self, request):
        self.fields(request, ('protocol', 'theory', 'blocks', 'proof', 'target'))
        if request['protocol'] != PROTOCOL: raise Invalid('unknown protocol')
        theory = request['theory']; self.fields(theory, ('functions', 'predicates', 'axioms', 'schemas'))
        self.functions = self.signature(theory['functions']); self.predicates = self.signature(theory['predicates'])
        schemas = self.sequence(theory['schemas'])
        if any(s != 'nat-induction' for s in schemas) or len(schemas) != len(set(schemas)):
            raise Invalid('unknown or duplicate theory schema')
        self.schemas = tuple(schemas)
        if type(theory['axioms']) is not dict: raise Invalid('axiom object required')
        self.axioms = {}
        for name, raw in theory['axioms'].items():
            self.string(name); a = self.formula(raw)
            if self.free(a): raise Invalid('theory axioms must be closed')
            self.axioms[name] = a
        for block in self.sequence(request['blocks']):
            self.fields(block, ('name', 'premises', 'conclusion', 'proof')); name = self.string(block['name'])
            if name in self.blocks: raise Invalid('duplicate block name')
            premises = tuple(self.formula(a) for a in self.sequence(block['premises']))
            conclusion = self.formula(block['conclusion'])
            self.proof(block['proof'], conclusion, premises)
            self.blocks[name] = (premises, conclusion); self.tick('blocks_checked')
        target = self.formula(request['target']); self.proof(request['proof'], target)

def check(payload, max_work=2000000, max_bytes=10000000, expected_problem_sha256=None):
    """Check bytes, never execute proof data. Rejection is certificate-relative."""
    started = time.perf_counter(); checker = Checker(max_work); digest = problem_digest = None
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result: raise Invalid('duplicate JSON key')
            result[name] = value
        return result
    def bad_number(_): raise Invalid('floating-point and nonfinite numbers are forbidden')
    try:
        if type(payload) is not bytes: raise Invalid('serialized bytes required')
        if max_bytes is not None and len(payload) > max_bytes: raise Resource('byte limit')
        digest = hashlib.sha256(payload).hexdigest()
        request = json.loads(payload.decode('utf-8'), object_pairs_hook=pairs,
                             parse_float=bad_number, parse_constant=bad_number)
        problem_digest = problem_hash(request)
        if expected_problem_sha256 is not None and problem_digest != expected_problem_sha256:
            raise Invalid('certificate changed the externally pinned theory or target')
        checker.request(request); status = 'accepted'; reason = 'all declared interfaces and primitive rules checked'
    except (Resource, RecursionError, MemoryError) as exc:
        status = 'unknown_resource_budget'; reason = str(exc) or type(exc).__name__
    except (Invalid, ValueError, TypeError, KeyError, IndexError, UnicodeError) as exc:
        status = 'rejected'; reason = str(exc)
    return dict(status=status, reason=reason, certificate_sha256=digest, problem_sha256=problem_digest,
                certificate_bytes=len(payload) if type(payload) is bytes else None,
                seconds=time.perf_counter()-started, **checker.stats)
