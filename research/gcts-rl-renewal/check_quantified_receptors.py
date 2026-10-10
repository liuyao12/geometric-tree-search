"""Independent explicit first-order inventory and point/tree verifier.

Uses serialized_kernel's separately implemented syntax/substitution, not the
producer's logic.py or its domain/mask/count implementation.
"""
import collections,itertools,json
from serialized_kernel import Checker

def need(ok,msg):
    if not ok:raise ValueError(msg)
def freeze(a):return tuple(freeze(v) for v in a) if isinstance(a,(tuple,list)) else {k:freeze(v) for k,v in a.items()} if isinstance(a,dict) else a
def packed(a):return json.dumps(a,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def word(a):return packed(a).decode('ascii')+'#'
def parser(theory):
    c=Checker(None);c.functions=theory['functions'];c.predicates=theory['predicates'];return c
def children(a):
    yield a
    if a[0]=='all':yield from children(a[2])
    elif a[0] in ('imp','and','or','not'):
        for b in a[1:]:yield from children(b)
def replace(a,binding,c):
    if a[0]=='pred' and a[1] in binding:
        need(len(a[2])==1,'family predicate arity');return c.subst(binding[a[1]],'x',a[2][0])
    if a[0]=='all':return ('all',a[1],replace(a[2],binding,c))
    if a[0] in ('imp','and','or','not'):return (a[0],)+tuple(replace(v,binding,c) for v in a[1:])
    return a
def inventory(spec,family=None,bindings=()):
    d=freeze(spec);c=parser(d['theory']);forms=set()
    for a in list(d['theory']['axioms'].values())+list(d['hypotheses']):forms.update(children(a))
    for _ in range(d['rounds']):
        new=set()
        for a in forms:
            if a[0]=='all':
                for t in d['terms']:new.update(children(c.subst(a[2],a[1],t)))
        forms|=new
    for a in tuple(forms):
        if a[0]=='imp' and a[2][0]=='and':
            for b in a[2][1:]:forms.update(children(('imp',a[1],b)))
    for _ in range(d['generalization_rounds']):forms|={('all',x,a) for a in forms for x in d['variables']}
    rows=[]
    def add(k,ps,a,guards=(),**p):rows.append(dict(kind=k,inputs=tuple(ps),output=a,guards=tuple(guards),parameters=p))
    for name,a in d['theory']['axioms'].items():add('axiom',(),a,name=name)
    for a in forms:
        if a[0]=='all':
            for t in d['terms']:
                b=c.subst(a[2],a[1],t)
                if b in forms:add('forall-elim',(a,),b,universal=a,term=t)
        if a[0]=='imp':add('mp',(a[1],a),a[2])
        if a[0]=='imp' and a[2][0]=='and':
            for side,b in enumerate(a[2][1:]):add('projection',(a,),('imp',a[1],b),side=side)
        for x in d['variables']:
            b=('all',x,a)
            if b in forms:add('generalize',(a,),b,(x,),variable=x)
    if family:
        family=freeze(family)
        for binding in freeze(bindings):
            proof=[dict(r,formula=replace(r['formula'],binding,c),parameters={k:replace(v,binding,c) if k=='universal' else v for k,v in r['parameters'].items()}) for r in family['proof']]
            add('family',[replace(a,binding,c) for a in family['premises']],replace(family['conclusion'],binding,c),family['guards'],name=family['name'],binding=binding,expansion=proof)
    unique={packed(r):r for r in rows};return [unique[k] for k in sorted(unique)],sorted(forms,key=word)
def proof(rows,target,hypotheses,theory,allow_family=True):
    rows=freeze(rows);target=freeze(target);hypotheses=freeze(hypotheses);c=parser(theory);known={j:a for j,a in enumerate(hypotheses,-len(hypotheses))};forbidden=set().union(*(c.free(a) for a in hypotheses));cost=0
    for j,r in enumerate(rows):
        a=r['formula'];p=r['parameters'];refs=r['refs'];k=r['kind'];c.formula(json.loads(packed(a)))
        need(all(type(i) is int and i in known and i<j for i in refs),'backward source references');inputs=[known[i] for i in refs]
        if k=='axiom':need(not refs and a==freeze(theory['axioms'][p['name']]),'declared axiom');cost+=1
        elif k=='forall-elim':
            u=p['universal'];need(len(refs)==1 and inputs[0]==u and u[0]=='all' and a==c.subst(u[2],u[1],p['term']),'capture-avoiding universal elimination');cost+=2
        elif k=='mp':need(len(refs)==2 and inputs[1]==('imp',inputs[0],a),'modus ponens');cost+=1
        elif k=='generalize':need(len(refs)==1 and p['variable'] not in forbidden and a==('all',p['variable'],inputs[0]),'eigenvariable restriction');cost+=1
        elif k=='projection':
            need(len(inputs)==1 and inputs[0][0]=='imp' and inputs[0][2][0]=='and' and p['side'] in (0,1) and a==('imp',inputs[0][1],inputs[0][2][p['side']+1]),'implication conjunction projection');cost+=2
        elif k=='family':
            need(allow_family,'nonrecursive learned family');need(not forbidden.intersection(v['parameters']['variable'] for v in p['expansion'] if v['kind']=='generalize'),'expanded ambient scope');cost+=proof(p['expansion'],a,inputs,theory,False)['primitive_lines']
        else:raise ValueError('unknown source rule')
        known[j]=a
    need(rows and rows[-1]['formula']==target,'source target');return dict(status='accepted',primitive_lines=cost,commands=len(rows))
def ports(rules,spec,chosen):
    d=freeze(spec);known={d['length']-1:d['target']}|{j:a for j,a in enumerate(d['hypotheses'],-len(d['hypotheses']))};filled=set();c=parser(d['theory']);bad=set().union(*(c.free(a) for a in d['hypotheses']))
    for j,rid,refs in freeze(chosen):
        need(0<=j<d['length'] and j not in filled and 0<=rid<len(rules),'placement identity');r=rules[rid]
        need(len(refs)==len(r['inputs']) and all(type(i) is int and -len(d['hypotheses'])<=i<j for i in refs),'reference domain')
        need(not bad.intersection(r['guards']),'scope marking disagreement')
        for i,a in [(j,r['output'])]+list(zip(refs,r['inputs'])):need(i not in known or known[i]==a,'global port disagreement');known[i]=a
        filled.add(j)
    return filled,known,bad
def domains(rules,spec,chosen):
    d=freeze(spec);filled,known,bad=ports(rules,d,chosen);ds={}
    for j in range(d['length']):
        if j in filled:continue
        keys=[]
        for rid,r in enumerate(rules):
            if bad.intersection(r['guards']) or (j in known and known[j]!=r['output']):continue
            choices=([i for i in range(-len(d['hypotheses']),j) if i not in known or known[i]==a] for a in r['inputs'])
            for refs in itertools.product(*choices):
                if any(refs[a]==refs[b] and r['inputs'][a]!=r['inputs'][b] for a in range(len(refs)) for b in range(a)):continue
                keys.append((j,rid,refs))
        ds[(2*j,0)]=keys
    return ds
def decide(ds):
    dead=sorted(p for p,k in ds.items() if not k);forced=sorted(p for p,k in ds.items() if len(k)==1)
    if dead:return 'dead',dead[0],()
    if forced:return 'forced',forced[0],ds[forced[0]]
    if not ds:return 'empty',None,()
    p=min(ds,key=lambda p:(len(ds[p]),p));return 'branch',p,ds[p]
def tree(rules,spec,result):
    totals=collections.Counter();leaf=None
    def visit(t,chosen):
        nonlocal leaf
        ds=domains(rules,spec,chosen);kind,p,keys=decide(ds);totals['nodes']+=1;totals['peak_candidates']=max(totals['peak_candidates'],sum(map(len,ds.values())))
        need((t['kind'],freeze(t['point']))==(kind,p),'complete global scheduler')
        if kind=='dead':totals['dead']+=1;return False
        if kind=='empty':leaf=chosen;return True
        totals[kind]+=1;seen=set();ok=False
        for child in t['children']:
            key=freeze(child['key']);need(not ok and key in keys and key not in seen,'unique legal candidate');seen.add(key);totals['attempts']+=1;ok=visit(child['tree'],chosen+(key,))
            if not ok:totals['backtracks']+=1
        need(ok or len(seen)==len(keys),'all alternatives before exhaustion');return ok
    if result['search_tree'] is None:need(result['status']=='unknown_search_budget','unknown only without terminal tree');return dict(status='unknown')
    ok=visit(result['search_tree'],());need(ok==(result['status']=='finite_exact_proof_tiling'),'tree outcome');need(not ok or leaf==freeze(result['placements']),'actual positive leaf')
    for k,v in totals.items():need(result['metrics'].get(k,0)==v,'tree counter '+k)
    h=len(spec['hypotheses']);expected=0
    for j in range(spec['length']):
        for r in rules:
            expected+=sum(1 for refs in itertools.product(range(-h,j),repeat=len(r['inputs'])) if all(refs[a]!=refs[b] or r['inputs'][a]==r['inputs'][b] for a in range(len(refs)) for b in range(a)))
    need(result['candidate_universe']==expected,'complete universe cardinality');return dict(status='complete_tree_replayed',nodes=totals['nodes'])
def certificate(rules,spec,result,tiles):
    d=freeze(spec);keys=freeze(result['placements']);tiles=freeze(tiles);need(len(keys)==d['length'] and {k[0] for k in keys}==set(range(d['length'])),'complete slots')
    c=parser(d['theory']);bad=set().union(*(c.free(a) for a in d['hypotheses']));vi={x:j for j,x in enumerate(d['variables'])}
    def port(j,a):return [((2*j,2+k),v) for k,v in enumerate(word(a))]+[((2*j,1),0)]
    initial=dict(port(d['length']-1,d['target']))
    for j,a in enumerate(d['hypotheses'],-len(d['hypotheses'])):initial.update(port(j,a))
    initial.update(((-1000,j),int(x in bad)) for x,j in vi.items());allmarks=initial.copy();totals=collections.Counter();rows=[None]*d['length'];need(len(tiles)==len(keys),'whole tile witness')
    for key,tile in zip(keys,tiles):
        j,rid,refs=key;r=rules[rid];marks={}
        for i,a in [(j,r['output'])]+list(zip(refs,r['inputs'])):
            for p,v in port(i,a):need(p not in marks or marks[p]==v,'single-valued tile');marks[p]=v
        marks.update(((-1000,vi[x]),0) for x in r['guards']);need(tile['key']==key and tile['occupancy']==(((2*j,0),12),) and tile['marks']==tuple(sorted(marks.items())),'complete actual tile values')
        for p,v in marks.items():need(p not in allmarks or allmarks[p]==v,'point marking agreement');allmarks[p]=v
        totals[(2*j,0)]+=12;rows[j]=dict(kind=r['kind'],formula=r['output'],refs=refs,parameters=r['parameters'])
    need(all(totals[(2*j,0)]==12 for j in range(d['length'])),'exact capacity');need(freeze(rows)==freeze(result['proof']),'displayed source proof')
    ports(rules,d,keys);checked=proof(rows,d['target'],d['hypotheses'],d['theory']);return dict(checked,points=len(allmarks),assigned_values=sum(len(t['marks']) for t in tiles))
