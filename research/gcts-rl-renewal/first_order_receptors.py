"""Native-admitted first-order axiom schemes in a complete bounded point grammar.

The producer constructs syntax; only the unchanged native checker admits scheme
and tautology guards. Search has no logical callback, proof script or old failure
constraints. Historical five/six-rule producers remain untouched.
"""
import collections,copy,math,time
import logic as L
from certificate_boundary_search import canonical,digest,choices
from native_receptor_points import assignment
from semantic_receptor_points import Model as Factored,mode_point

def thaw(v):return [thaw(x) for x in v] if isinstance(v,tuple) else v
def frozen(v):return tuple(frozen(x) for x in v) if isinstance(v,list) else v
def syntax(spec):
    """Two finite instantiation rounds; atomic templates abstract seed terms.

    Terms are input/target subterms whose free variables are free in the target.
    Equality operand pairs are equality subformulas whose operands are closed
    members of that same fixed pool. All atomic
    subformulas after instantiation are abstracted at every closed subterm; the
    placeholder is fresh. Equality schemes add one layer, without recursive
    resynthesis. Subformulas of every added scheme are included.
    """
    L.Kernel(spec['theory']['functions'],spec['theory']['predicates'],
             {k:frozen(v) for k,v in spec['theory']['axioms'].items()}).formula(frozen(spec['target']))
    fs={};terms={};names=set();schemes={}
    def term(t):
        terms[canonical(t)]=copy.deepcopy(t)
        if t[0]=='var':names.add(t[1])
        else:
            for a in t[2]:term(a)
    def visit(a,collect=False):
        fs[canonical(a)]=copy.deepcopy(a)
        if a[0]=='all':names.add(a[1]);visit(a[2],collect)
        elif a[0] in ('imp','and','or','not'):
            for b in a[1:]:visit(b,collect)
        elif a[0] in ('pred','eq'):
            for t in a[2] if a[0]=='pred' else a[1:]:
                if collect:term(t)
                else:names.update(L.term_free(frozen(t)))
    for a in [spec['target'],*spec['theory']['axioms'].values()]:visit(a,True)
    free=L.free(frozen(spec['target']))
    pool=[terms[k] for k in sorted(terms) if L.term_free(frozen(terms[k]))<=free]
    closed=[t for t in pool if not L.term_free(frozen(t))]
    for _ in range(spec.get('instantiation_rounds',2)):
        universals=[a for _,a in sorted(fs.items()) if a[0]=='all']
        for u in universals:
            for t in pool:
                f=['imp',u,thaw(L.substitute(frozen(u[2]),u[1],frozen(t)))]
                c=dict(rule='instantiate',formula=f,universal=u,term=t)
                schemes[canonical(c)]=c;visit(f)
    hole='hole0';n=0
    while hole in names:n+=1;hole='hole'+str(n)
    templates={}
    def replace(t,old):
        if t==old:return ['var',hole]
        return t if t[0]=='var' else ['fun',t[1],[replace(a,old) for a in t[2]]]
    def contains(t,old):return t==old or t[0]=='fun' and any(contains(a,old) for a in t[2])
    for a in list(fs.values()):
        if a[0] not in ('pred','eq'):continue
        args=a[2] if a[0]=='pred' else a[1:]
        for t in closed:
            if any(contains(s,t) for s in args):
                p=['pred',a[1],[replace(s,t) for s in args]] if a[0]=='pred' else ['eq',*[replace(s,t) for s in args]]
                templates[canonical(p)]=p
    closed_keys={canonical(t) for t in closed}
    pairs={canonical(a[1:]):a[1:] for a in fs.values() if a[0]=='eq' and all(canonical(t) in closed_keys for t in a[1:])}
    for _,p in sorted(templates.items()):
        for _,(s,t) in sorted(pairs.items()):
                f=['imp',['eq',s,t],['imp',thaw(L.substitute(frozen(p),hole,frozen(s))),thaw(L.substitute(frozen(p),hole,frozen(t)))]]
                c=dict(rule='eq_subst',formula=f,variable=hole,template=p,left=s,right=t)
                schemes[canonical(c)]=c;visit(f)
    return dict(basis=[fs[k] for k in sorted(fs)],variables=sorted(names),terms=pool,
                equality_terms=closed,equality_pairs=[pairs[k] for k in sorted(pairs)],template_variable=hole,templates=[templates[k] for k in sorted(templates)],
                schemes=[schemes[k] for k in sorted(schemes)],rounds=spec.get('instantiation_rounds',2))

def domains(spec,catalog,slot):
    rows=choices(spec,slot,catalog['basis'],catalog['variables'])
    # A scheme's output is determined by its parameters. Keep all original
    # five-rule command fields; the new scheme catalog adds one positional
    # command per parameter instance, without an artificial output product.
    for scheme in catalog['schemes']:
        if slot+1<spec['length'] or scheme['formula']==spec['target']:rows.append(copy.deepcopy(scheme))
    rows.sort(key=lambda c:(c['rule'],canonical(c['formula']),canonical(c)))
    if len({canonical(c) for c in rows})!=len(rows):raise ValueError('duplicate first-order command')
    return rows

def compile_guards(spec,oracle,limit=5*10**9,queries=512):
    catalog=syntax(spec);began=time.perf_counter();ids=[];tauts=[];schemes=[]
    def submit(command,purpose):
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=[command],target=command['formula'])
        q=oracle.request(request,limit,purpose);ids.append(q['id']);return q
    seed=dict(rule='tautology',formula=['imp',['bot'],['bot']])
    q=submit(seed,'first_order_theory_admission')
    theory=q['id']
    if q['result']['status']!='accepted':return dict(status='unknown_or_rejected_theory',catalog=catalog,queries=ids,theory_query=theory,seconds=time.perf_counter()-began)
    for c,purpose in [(dict(rule='tautology',formula=f),'first_order_tautology') for f in catalog['basis']]+[(c,'first_order_scheme') for c in catalog['schemes']]:
        if len(ids)>=queries:return dict(status='unknown_compile_budget',catalog=catalog,queries=ids,theory_query=theory,seconds=time.perf_counter()-began)
        q=submit(c,purpose)
        if q['result']['status']=='accepted':
            (tauts if purpose=='first_order_tautology' else schemes).append(c['formula'] if purpose=='first_order_tautology' else c)
        elif q['result']['status']!='rejected':return dict(status='unknown_native_compilation',catalog=catalog,queries=ids,theory_query=theory,seconds=time.perf_counter()-began)
    return dict(status='complete',catalog=catalog,basis=catalog['basis'],variables=catalog['variables'],tautologies=tauts,
                admitted_schemes=schemes,queries=ids,theory_query=theory,seconds=time.perf_counter()-began)

class Model(Factored):
    def __init__(self,spec,compiled):
        if compiled['status']!='complete':raise ValueError('unfinished compilation is not authority')
        self.spec=spec;self.compiled=compiled;self.arity=0;self.interfaces=[];self.mode={};self.mode_names={}
        self.inventory=dict(status='native_accepted',definitions=[],interfaces=[],native_blocks=[])
        self.metrics=collections.Counter();self.dependencies=collections.defaultdict(set);self.cache={};self.align_cache={};self.metadata={};self.conflicts=[]
        self.domains=[];start=time.perf_counter();tauts={canonical(f) for f in compiled['tautologies']};schemes={canonical(c) for c in compiled['admitted_schemes']}
        for j in range(spec['length']):
            for r in (0,1):self.align_cache[4*j,r]=[]
            rows=domains(spec,compiled['catalog'],j);self.domains.append(rows)
            for k,c in enumerate(rows):
                entries=assignment(j,'command',c)+assignment(j,'formula',c['formula'])+[(mode_point(j),0)]
                self.add((j,0,k,0),entries,c,[],'command');f=c['formula'];r=c['rule'];req=[]
                if r=='mp':
                    for v,imp in enumerate(compiled['basis']):
                        if imp[0]=='imp' and imp[2]==f:
                            wanted=[(c['antecedent'],imp[1]),(c['implication'],imp)]
                            self.add((j,1,k,v),entries+[e for i,a in wanted for e in assignment(i,'formula',a)],c,wanted,'guard')
                    continue
                if r=='axiom':valid=spec['theory']['axioms'][c['name']]==f
                elif r=='refl':valid=f[0]=='eq' and f[1]==f[2]
                elif r=='tautology':valid=canonical(f) in tauts
                elif r=='generalize':
                    valid=f[0]=='all' and f[1]==c['variable']
                    if valid:req=[(c['source'],f[2])]
                else:valid=canonical(c) in schemes
                if valid:self.add((j,1,k,0),entries+[e for i,a in req for e in assignment(i,'formula',a)],c,req,'guard')
        self.compile_seconds=time.perf_counter()-start
        for p in self.align_cache:self.align_cache[p]=tuple(self.align_cache[p])
    def record(self):
        r=super().record();r.update(complete_words=math.prod(map(len,self.domains)),initial_marks=sorted(self.initial().marks.items()),
            scope='New bounded first-order adapter: all original command outputs and parameter instances, native-admitted instantiate/eq_subst guards, full C/G roots, no registered lemmas or old failure overlays. Equality templates are atomic and operands closed. Reference point search above the unchanged primitive palette.')
        return r
