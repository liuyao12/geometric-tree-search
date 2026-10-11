"""Injective AST-to-TPTP inputs; no target proof sequences are supplied."""
import copy, hashlib, json

def canonical(x): return json.dumps(x, sort_keys=True, separators=(',', ':'))
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()

class Symbols:
    def __init__(self,theory):
        self.functions={n:'f'+str(i) for i,n in enumerate(sorted(theory['functions']))}
        self.predicates={n:'p'+str(i) for i,n in enumerate(sorted(theory['predicates']))}
    def term(self,t,env):
        if t[0]=='var': return env[t[1]]
        if t[0]!='fun': raise ValueError('term AST')
        h=self.functions[t[1]]
        return h+('('+','.join(self.term(a,env) for a in t[2])+')' if t[2] else '')
    def formula(self,f,env=None):
        env={} if env is None else env
        h=f[0]
        if h=='bot':return '$false'
        if h=='pred':
            n=self.predicates[f[1]]
            return n+('('+','.join(self.term(t,env) for t in f[2])+')' if f[2] else '')
        if h=='eq':return '('+self.term(f[1],env)+'='+self.term(f[2],env)+')'
        if h in ('imp','and','or'):
            return '('+self.formula(f[1],env)+{'imp':'=>','and':'&','or':'|'}[h]+self.formula(f[2],env)+')'
        if h=='not':return '~('+self.formula(f[1],env)+')'
        if h in ('all','forall','exists'):
            v='X'+str(1+max([-1]+[int(v[1:]) for v in env.values()]));updated={**env,f[1]:v}
            return ('!' if h in ('all','forall') else '?')+'['+v+']:('+self.formula(f[2],updated)+')'
        raise ValueError('formula AST '+h)

def lemma_formula(definition):
    f=copy.deepcopy(definition['conclusion'])
    for p in reversed(definition['premises']):f=['imp',copy.deepcopy(p),f]
    return f

def make_input(case,library):
    spec=case['spec'];sy=Symbols(spec['theory']);entries=[]
    for i,(n,f) in enumerate(sorted(spec['theory']['axioms'].items())):
        entries.append(dict(name='a'+str(i),role='axiom',original_name=n,formula=f))
    if library:
        if case['inventory']['status']!='native_accepted':raise ValueError('library not admitted')
        defs=case['inventory']['native_blocks']
        admissions={a['name']:a['query'] for a in case['inventory']['admissions']}
        for i,d in enumerate(defs):
            entries.append(dict(name='l'+str(i),role='lemma',original_name=d['name'],formula=lemma_formula(d),native_admission=admissions[d['name']]))
    entries.append(dict(name='goal',role='conjecture',original_name='target',formula=spec['target']))
    lines=['% Injective renaming; ordinary constants do not imply distinctness.']
    for e in entries:lines.append('fof('+e['name']+','+e['role']+','+sy.formula(e['formula'])+').')
    text='\n'.join(lines)+'\n'
    return dict(case=spec['id'],lane='theory-and-all-admitted-ground-lemmas' if library else 'theory-only',
                functions=sy.functions,predicates=sy.predicates,
                function_arities={sy.functions[n]:a for n,a in spec['theory']['functions'].items()},
                predicate_arities={sy.predicates[n]:a for n,a in spec['theory']['predicates'].items()},
                entries=entries,text=text,sha256=sha(text),
                gcts_row_boundary=spec['length'],external_row_boundary=None,
                scope='Identical theory/target and optionally every admitted ground lemma interface. E has unrestricted first-order calculus, not the finite GCTS catalog.')
