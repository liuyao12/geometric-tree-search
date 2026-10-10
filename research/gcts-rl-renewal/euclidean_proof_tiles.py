"""Finite Horn geometry compiled to directed exact point proof tiles.

The vertex grammar contains three distinct free names. It includes every
admissible rule grounding in the complete backward goal cone; no proof path
or triangle correspondence is supplied. Congruence foundations are declared
axioms. Every compiled rule expands to ordinary first-order proof lines.
"""
import hashlib,itertools,time
import logic as L
import semantic_proof_catalogs as C
from semantic_proof_tiles import frozen
from proof_block_search import Proof
from serialized_kernel import canonical,check,problem_hash,PROTOCOL

def pred(name,*xs):return ('pred',name,tuple(L.V(x) for x in xs))
def chain(ps,q):
    for p in reversed(ps):q=L.Imp(p,q)
    return q

def foundation():
    a,b,c,d,e,f=['p'+str(i) for i in range(6)]
    T=lambda *x:pred('Triangle',*x)
    S=lambda *x:pred('SegEq',*x)
    A=lambda *x:pred('AngleEq',*x)
    G=lambda *x:pred('Congruent',*x)
    rows=[
      ('segment-reflexivity',[],S(a,b,a,b)),
      ('segment-reversal',[],S(a,b,b,a)),
      ('segment-symmetry',[S(a,b,c,d)],S(c,d,a,b)),
      ('angle-reflexivity',[T(a,b,c)],A(a,b,c,a,b,c)),
      ('angle-ray-swap',[T(a,b,c)],A(b,a,c,c,a,b)),
      ('angle-symmetry',[A(a,b,c,d,e,f)],A(d,e,f,a,b,c)),
      ('triangle-swap',[T(a,b,c)],T(a,c,b)),
      ('triangle-cycle',[T(a,b,c)],T(b,c,a)),
      ('SAS',[T(a,b,c),T(d,e,f),S(a,b,d,e),S(a,c,d,f),A(b,a,c,e,d,f)],G(a,b,c,d,e,f)),
      ('ASA',[T(a,b,c),T(d,e,f),A(a,b,c,d,e,f),A(a,c,b,d,f,e),S(b,c,e,f)],G(a,b,c,d,e,f)),
      ('corresponding-angle',[G(a,b,c,d,e,f)],A(a,b,c,d,e,f)),
      ('corresponding-side',[G(a,b,c,d,e,f)],S(a,b,d,e))]
    rules=[];axioms={}
    for name,ps,q in rows:
        vs=sorted(set().union(*(L.free(x) for x in ps+[q])))
        ax=chain(ps,q)
        for x in reversed(vs):ax=L.All(x,ax)
        rules.append(dict(name=name,variables=vs,premises=ps,conclusion=q))
        axioms[name]=ax
    return dict(functions={},predicates=dict(Triangle=3,SegEq=4,AngleEq=6,Congruent=6),axioms=axioms,schemas=[]),rules

def problem(name):
    t=pred('Triangle','a','b','c');s=pred('SegEq','a','b','a','c');a=pred('AngleEq','a','b','c','a','c','b')
    premise,goal=(s,a) if name=='I.5' else (a,s)
    h=('and',t,premise)
    if name=='triangle-order':h=t;goal=pred('Triangle','c','b','a')
    body=L.Imp(h,goal);target=body
    for x in reversed(['a','b','c']):target=L.All(x,target)
    return dict(name=name,hypothesis=h,goal=goal,target=target,vertices=['a','b','c'])

def admissible(a):
    xs=[t[1] for t in a[2]]
    if a[1]=='Triangle':return len(set(xs))==3
    if a[1] in ('AngleEq','Congruent'):return len(set(xs[:3]))==3 and len(set(xs[3:]))==3
    return xs[0]!=xs[1] and xs[2]!=xs[3]

def grounded(rules,vertices):
    out=[]
    for r in rules:
        for xs in itertools.product(vertices,repeat=len(r['variables'])):
            env=dict(zip(r['variables'],xs))
            def subst(a):
                for x in r['variables']:a=L.substitute(a,x,L.V(env[x]))
                return a
            ps=[subst(a) for a in r['premises']];q=subst(r['conclusion'])
            if all(admissible(a) for a in ps+[q]):out.append(dict(name=r['name'],bindings=env,premises=ps,conclusion=q))
    return out

def goal_cone(rows,goal):
    needed={goal};selected=[];rest=list(rows)
    while True:
        new=[r for r in rest if r['conclusion'] in needed]
        if not new:break
        selected.extend(new)
        for r in new:needed.update(r['premises'])
        rest=[r for r in rest if r not in new]
    return sorted(selected,key=lambda r:repr((r['name'],r['bindings']))),needed

def block(ps,q,lines):
    digest=hashlib.sha256(canonical([ps,q,lines])).hexdigest()[:24]
    return dict(name='geometry-'+digest,premises=ps,conclusion=q,proof=lines)

def consume(out,condition,index,premise_index):
    a=out.lines[index]['formula'][2];p=out.lines[premise_index]['formula'][2]
    if a[0]!='imp' or a[1]!=p:raise ValueError('geometry compiler premise')
    schema=L.Imp(L.Imp(condition,a),L.Imp(L.Imp(condition,p),L.Imp(condition,a[2])))
    j=out.emit('tautology',schema)
    return out.mp(premise_index,out.mp(index,j))

def start_definition(theory,rule,h,take):
    ps=rule['premises'];q=rule['conclusion'];out=Proof()
    inputs=[L.Imp(h,p) for p in ps[:take]]
    indices=[out.emit('assumption',p,index=i) for i,p in enumerate(inputs)]
    ax=frozen(theory['axioms'][rule['name']]);j=out.emit('axiom',ax,name=rule['name'])
    while ax[0]=='all':
        x=ax[1];t=L.V(rule['bindings'][x]);next_a=L.substitute(ax[2],x,t)
        k=out.emit('instantiate',L.Imp(ax,next_a),universal=ax,term=t)
        j=out.mp(j,k);ax=next_a
    if ax!=chain(ps,q):raise ValueError('ground axiom mismatch')
    k=out.emit('tautology',L.Imp(ax,L.Imp(h,ax)));j=out.mp(j,k)
    for i in indices:j=consume(out,h,j,i)
    conclusion=L.Imp(h,chain(ps[take:],q))
    return block(inputs,conclusion,out.lines)

def join_definition(h,p,rest):
    q=L.Imp(h,rest);inputs=[L.Imp(h,L.Imp(p,rest)),L.Imp(h,p)]
    out=Proof();a=out.emit('assumption',inputs[0],index=0);b=out.emit('assumption',inputs[1],index=1)
    consume(out,h,a,b)
    return block(inputs,q,out.lines)

def catalog(p,omit=()):
    began=time.perf_counter();theory,rs=foundation()
    for name in omit:theory['axioms'].pop(name)
    rs=[r for r in rs if r['name'] not in omit]
    all_rows=grounded(rs,p['vertices']);rows,atoms=goal_cone(all_rows,p['goal']);h=p['hypothesis']
    fs={L.Imp(h,a) for a in atoms};rules=[]
    for a in (h[1:] if h[0]=='and' else (h,)):
        q=L.Imp(h,a);fs.add(q);rules.append(([],q,dict(kind='primitive',witness=dict(rule='tautology',formula=q))))
    for row in rows:
        ps=row['premises'];q=row['conclusion'];take=min(2,len(ps));b=start_definition(theory,row,h,take)
        out=b['conclusion'];fs.add(out);fs.update(b['premises'])
        recipe=dict(kind='block',operation='geometry-rule',axiom=row['name'],bindings=row['bindings'],phase=0,definition=b)
        rules.append((b['premises'],out,recipe))
        for i in range(take,len(ps)):
            rest=chain(ps[i+1:],q);b=join_definition(h,ps[i],rest);fs.update(b['premises']);fs.add(b['conclusion'])
            rules.append((b['premises'],b['conclusion'],dict(kind='block',operation='geometry-join',axiom=row['name'],bindings=row['bindings'],phase=i-take+1,definition=b)))
    c=C.catalog(theory,p['target'],fs,rules,close=p['vertices'],configuration=dict(kind='three-distinct-vertex-positive-Horn-backward-cone',vertices=p['vertices'],hypothesis=h,goal=p['goal'],omit=list(omit),ground_rules=len(all_rows),cone_rules=len(rows),cone_atoms=len(atoms),orientation='identity; directed displacements; translation only; no rotation/reflection',max_rule_arity=2))
    c['build_seconds']=time.perf_counter()-began
    return c
