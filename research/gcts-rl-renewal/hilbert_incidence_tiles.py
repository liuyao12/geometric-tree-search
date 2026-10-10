"""Source-pinned planar Hilbert incidence and witness-free proof tiles.

The object language is one-sorted FOL with explicit Point/Line guards. The
three planar incidence axioms are present, including their existence claims.
Exists is the logical abbreviation not-all-not, not a witness constructor.
The finite search grammar grounds all outer binders in the declared two sorts,
orients every resulting propositional clause in every direction, and includes
ordinary equality substitution. No theorem proof or correspondence is input.
"""
import hashlib,itertools,time
import logic as L
import semantic_proof_catalogs as C
from proof_block_search import Proof
from serialized_kernel import canonical
from euclidean_proof_tiles import consume

SOURCE='https://www.maths.tcd.ie/~dwilkins/Courses/MA232A/MA232A_Mich2017/HilbertAxioms_ParallelText.html'

def pred(name,*xs):return ('pred',name,tuple(L.V(x) for x in xs))
def conjunction(xs):
    xs=list(xs)
    if not xs:return L.Imp(('bot',),('bot',))
    out=xs[-1]
    for a in reversed(xs[:-1]):out=('and',a,out)
    return out
def exists(x,a):return L.Not(L.All(x,L.Not(a)))
def close(xs,a):
    for x in reversed(xs):a=L.All(x,a)
    return a
def negate(a):return a[1] if a[0]=='not' else L.Not(a)

def foundation(omit=()):
    P=lambda x:pred('Point',x);R=lambda x:pred('Line',x);I=lambda x,y:pred('Inc',x,y)
    neq=lambda x,y:L.Not(L.Eq(L.V(x),L.V(y)))
    a,b,c,u,v='p0','p1','p2','l0','l1'
    rows=[
      ('sort-cover',{'x':'object'},('or',P('x'),R('x')),'Logical presentation: point/line universe'),
      ('sort-disjoint',{'x':'object'},L.Imp(P('x'),L.Not(R('x'))),'Hilbert section 1: distinct systems of entities'),
      ('incidence-typed',{'x':'object','y':'object'},L.Imp(I('x','y'),conjunction([P('x'),R('y')])),'Incidence relation has point and line arguments'),
      ('I.1-existence',{a:'point',b:'point'},L.Imp(conjunction([P(a),P(b),neq(a,b)]),exists(u,conjunction([R(u),I(a,u),I(b,u)]))),'I.1: a line through any two distinct points'),
      ('I.2-uniqueness',{a:'point',b:'point',u:'line',v:'line'},L.Imp(conjunction([P(a),P(b),R(u),R(v),neq(a,b),I(a,u),I(b,u),I(a,v),I(b,v)]),L.Eq(L.V(u),L.V(v))),'I.1-I.2: two distinct incident points determine their line'),
      ('I.3-line-points',{u:'line'},L.Imp(R(u),exists(a,exists(b,conjunction([P(a),P(b),neq(a,b),I(a,u),I(b,u)])))),'I.3: at least two distinct points on each line'),
      ('I.3-plane-points',{},exists(a,exists(b,exists(c,conjunction([P(a),P(b),P(c),neq(a,b),neq(a,c),neq(b,c),L.Not(exists(u,conjunction([R(u),I(a,u),I(b,u),I(c,u)])))])))),'I.3: at least three noncollinear points in the plane')]
    axioms={name:close(list(sorts),body) for name,sorts,body,_ in rows if name not in omit}
    metadata={name:dict(binders=sorts,source=source) for name,sorts,_,source in rows if name not in omit}
    theory=dict(functions={},predicates=dict(Point=1,Line=1,Inc=2),axioms=axioms,schemas=[])
    L.Kernel(theory['functions'],theory['predicates'],axioms)
    return theory,metadata

def problem(name):
    P=lambda x:pred('Point',x);R=lambda x:pred('Line',x);I=lambda x,y:pred('Inc',x,y)
    eq=lambda x,y:L.Eq(L.V(x),L.V(y));neq=lambda x,y:L.Not(eq(x,y))
    point_names=['a','b','c'];line_names=['u','v']
    h=[P('a'),P('b'),R('u'),R('v'),I('a','u'),I('b','u'),I('a','v'),I('b','v')]
    if name=='intersection-unique':h.append(neq('u','v'));goal=eq('a','b')
    elif name=='incidence-transfer':h.extend([P('c'),neq('a','b'),I('c','u')]);goal=I('c','v')
    elif name=='wrong-intersection':h.append(neq('u','v'));goal=neq('a','b')
    else:raise ValueError(name)
    h=conjunction(h);variables=sorted(L.free(h)|L.free(goal));target=close(variables,L.Imp(h,goal))
    return dict(name=name,hypothesis=h,goal=goal,target=target,variables=variables,sorts=dict(point=point_names,line=line_names),source='Hilbert theorem 1, planar part' if name=='intersection-unique' else 'derived incidence-transfer lemma')

def cnf(a,negative=False):
    """Propositional CNF; quantified subformulas remain opaque atoms."""
    if a[0]=='not':return cnf(a[1],not negative)
    if a[0]=='imp':return cnf(('or',L.Not(a[1]),a[2]),negative)
    if a[0] in ('and','or'):
        left=cnf(a[1],negative);right=cnf(a[2],negative)
        together=(a[0]=='and')!=negative
        return left+right if together else [x+y for x in left for y in right]
    return [[L.Not(a) if negative else a]]

def orientations(body):
    for ci,clause in enumerate(cnf(body)):
        for head,literal in enumerate(clause):
            ps=[negate(a) for i,a in enumerate(clause) if i!=head]
            yield ci,head,[conjunction(ps)] if ps else [],literal

def ground_axioms(theory,metadata,sorts):
    domains=dict(sorts,object=sorts['point']+sorts['line']);rows=[]
    for name,ax in theory['axioms'].items():
        vs=list(metadata[name]['binders']);body=ax
        for x in vs:
            if body[0]!='all' or body[1]!=x:raise ValueError('source binder mismatch')
            body=body[2]
        for values in itertools.product(*(domains[metadata[name]['binders'][x]] for x in vs)):
            bindings=dict(zip(vs,values));instance=body
            for x,y in bindings.items():instance=L.substitute(instance,x,L.V(y))
            for ci,head,ps,q in orientations(instance):
                rows.append(dict(kind='axiom-clause',axiom=name,bindings=bindings,clause=ci,head=head,premises=ps,conclusion=q,instance=instance))
    return rows

def equality_rows(sorts):
    rows=[];hole='equalityHole'
    for sort,domain in sorts.items():
        templates=[pred('Point' if sort=='point' else 'Line',hole)]
        templates += [pred('Inc',hole,u) for u in sorts['line']] if sort=='point' else [pred('Inc',a,hole) for a in sorts['point']]
        templates += [L.Eq(L.V(hole),L.V(x)) for x in domain]+[L.Eq(L.V(x),L.V(hole)) for x in domain]
        for left,right,template in itertools.product(domain,domain,templates):
            before=L.substitute(template,hole,L.V(left));after=L.substitute(template,hole,L.V(right))
            rows.append(dict(kind='equality-substitution',sort=sort,left=left,right=right,variable=hole,template=template,premises=[L.Eq(L.V(left),L.V(right)),before],conclusion=after))
    return rows

def cone(rows,goal):
    needed={goal};selected=[];rest=list(rows)
    while True:
        added=[r for r in rest if r['conclusion'] in needed]
        if not added:break
        selected.extend(added);needed.update(a for r in added for a in r['premises'])
        rest=[r for r in rest if r not in added]
    return selected,needed

def definition(theory,row,h):
    out=Proof();inputs=[L.Imp(h,a) for a in row['premises']]
    indices=[out.emit('assumption',p,index=i) for i,p in enumerate(inputs)]
    if row['kind']=='axiom-clause':
        ax=theory['axioms'][row['axiom']];j=out.emit('axiom',ax,name=row['axiom'])
        for x,y in row['bindings'].items():
            next_a=L.substitute(ax[2],x,L.V(y));k=out.emit('instantiate',L.Imp(ax,next_a),universal=ax,term=L.V(y))
            j=out.mp(j,k);ax=next_a
        if ax!=row['instance']:raise ValueError('source instantiation mismatch')
        a=row['conclusion']
        for p in reversed(row['premises']):a=L.Imp(p,a)
        k=out.emit('tautology',L.Imp(ax,a));j=out.mp(j,k)
    else:
        s,t=L.V(row['left']),L.V(row['right']);a=L.Imp(row['premises'][0],L.Imp(row['premises'][1],row['conclusion']))
        j=out.emit('eq_subst',a,variable=row['variable'],template=row['template'],left=s,right=t)
    k=out.emit('tautology',L.Imp(a,L.Imp(h,a)));j=out.mp(j,k)
    for i in indices:j=consume(out,h,j,i)
    q=L.Imp(h,row['conclusion'])
    if out.lines[j]['formula']!=q:raise ValueError('compiled conclusion')
    digest=hashlib.sha256(canonical([inputs,q,out.lines])).hexdigest()[:24]
    return dict(name='hilbert-'+digest,premises=inputs,conclusion=q,proof=out.lines)

def catalog(p,omit=()):
    began=time.perf_counter();theory,metadata=foundation(omit)
    ax_rows=ground_axioms(theory,metadata,p['sorts']);eq_rows=equality_rows(p['sorts'])
    rows,atoms=cone(ax_rows+eq_rows,p['goal']);h=p['hypothesis'];fs={L.Imp(h,a) for a in atoms};rules=[]
    for a in sorted(atoms,key=repr):
        q=L.Imp(h,a)
        if L.tautology(q):rules.append(([],q,dict(kind='primitive',witness=dict(rule='tautology',formula=q))))
        elif a[0]=='eq' and a[1]==a[2]:
            out=Proof();j=out.emit('refl',a);k=out.emit('tautology',L.Imp(a,q));out.mp(j,k)
            b=dict(name='hilbert-refl-'+hashlib.sha256(canonical(a)).hexdigest()[:16],premises=[],conclusion=q,proof=out.lines)
            rules.append(([],q,dict(kind='block',operation='hilbert-reflexivity',definition=b)))
    for row in rows:
        b=definition(theory,row,h);recipe={k:v for k,v in row.items() if k not in ('premises','conclusion','instance')}
        rules.append((b['premises'],b['conclusion'],dict(kind='block',operation='hilbert-rule',inference=recipe,definition=b)))
    c=C.catalog(theory,p['target'],fs,rules,close=p['variables'],configuration=dict(kind='Hilbert-planar-incidence-sorted-clause-orientations-and-atomic-equality',sorts=p['sorts'],metadata=metadata,hypothesis=h,goal=p['goal'],omit=list(omit),source=SOURCE,axiom_instances=len(ax_rows),equality_instances=len(eq_rows),cone_rules=len(rows),cone_formulas=len(atoms),orientation='identity; fixed proof direction; translation only; no rotation/reflection',scope='Complete outer-binder grounding and all propositional clause orientations, plus declared atomic equality templates, then complete backward dependency cone including cycles. Quantified subformulas are opaque; no existential witness elimination in this search grammar.'))
    c['build_seconds']=time.perf_counter()-began
    return c
