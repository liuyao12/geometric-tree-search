"""All declared sorted incidence rule groundings, without a target cone.

The compiler creates standard universal-instance and equality-substitution
rules. It supplies no theorem path, proof sequence, or target-conditioned
deduction. Every ground definition still requires unchanged native admission.
"""
import copy,itertools,time
import logic as L
from certificate_boundary_search import canonical,digest
from first_order_receptors import thaw,frozen

SOURCE='https://www.maths.tcd.ie/~dwilkins/Courses/MA232A/MA232A_Mich2017/HilbertAxioms_ParallelText.html'
def V(n):return ['var',n]
def F(n):return ['fun',n,[]]
def P(n,*args):return ['pred',n,list(args)]
def E(s,t):return ['eq',s,t]
def I(p,q):return ['imp',p,q]
def conjunction(xs):
    xs=list(xs);out=xs[-1]
    for x in reversed(xs[:-1]):out=['and',x,out]
    return out
def close(vs,f):
    for v in reversed(vs):f=['all',v,f]
    return f
def condition(a,b,u,v):
    return conjunction([P('Point',a),P('Point',b),P('Line',u),P('Line',v),['not',E(a,b)],
                        P('Incident',a,u),P('Incident',b,u),P('Incident',a,v),P('Incident',b,v)])
def axiom():
    a,b,u,v=map(V,['point0','point1','line0','line1'])
    return close(['point0','point1','line0','line1'],I(condition(a,b,u,v),E(u,v)))
def cases():
    a,b,c,u,v=map(F,['A','B','C','u','v'])
    base=dict(functions={x:0 for x in ['A','B','C','u','v']},predicates=dict(Point=1,Line=1,Incident=2),
              axioms={'I.2-uniqueness':axiom(),'common-distinct-points':condition(a,b,u,v),'extra-incidence':P('Incident',c,u)},schemas=[])
    common=dict(sorts={'point':['A','B','C'],'line':['u','v']},uniqueness_points=['A','B'],scope='One-sorted FOL with explicit Point/Line guards. I.2 uniqueness only; no coordinates, existence, order, congruence, parallel or continuity axioms.')
    positive=dict(id='incidence-transport',title='Transport a further incident point after line uniqueness',theory=base,target=P('Incident',c,v),length=4,**common)
    removed=copy.deepcopy(positive);removed.update(id='transport-no-uniqueness',title='Remove the uniqueness axiom');removed['theory']['axioms'].pop('I.2-uniqueness')
    short=copy.deepcopy(positive);short.update(id='transport-short',title='The same target in three proof rows',length=3)
    return [positive,removed,short]

def syntax_and_definitions(spec):
    started=time.perf_counter();basis={};definitions=[];recipes=[]
    def include(f):basis[canonical(f)]=copy.deepcopy(f)
    for f in [spec['target'],*spec['theory']['axioms'].values()]:include(f)
    # All 16 point/point/line/line substitutions, including coincident names.
    universal=axiom();variables=['point0','point1','line0','line1']
    for names in itertools.product(spec['uniqueness_points'],spec['uniqueness_points'],spec['sorts']['line'],spec['sorts']['line']):
        terms=list(map(F,names));premise=condition(*terms);goal=E(terms[2],terms[3]);include(premise);include(goal)
        if 'I.2-uniqueness' not in spec['theory']['axioms']:continue
        proof=[dict(rule='assumption',formula=premise,index=0),dict(rule='axiom',formula=universal,name='I.2-uniqueness')];current=universal;last=1
        for term in terms:
            nxt=thaw(L.substitute(frozen(current[2]),current[1],frozen(term)))
            proof.append(dict(rule='instantiate',formula=I(current,nxt),universal=current,term=term));q=len(proof)-1
            proof.append(dict(rule='mp',formula=nxt,antecedent=last,implication=q));last=len(proof)-1;current=nxt
        if current!=I(premise,goal):raise ValueError('ground universal mismatch')
        proof.append(dict(rule='mp',formula=goal,antecedent=0,implication=last))
        d=dict(premises=[premise],conclusion=goal,proof=proof);name='hilbert-'+digest(d)
        definitions.append(dict(name=name,level=1,family='universal-uniqueness',arguments=names,definition=dict(name=name,**d)))
        recipes.append(dict(name=name,kind='universal-uniqueness',bindings=dict(zip(variables,names))))
    # All 12 incidence transports at the line argument: every point and pair.
    hole='incidenceHole'
    for point,left,right in itertools.product(spec['sorts']['point'],spec['sorts']['line'],spec['sorts']['line']):
        s,t=F(left),F(right);template=P('Incident',F(point),V(hole));before=P('Incident',F(point),s);after=P('Incident',F(point),t);eq=E(s,t)
        for f in [eq,before,after]:include(f)
        schema=I(eq,I(before,after));proof=[dict(rule='assumption',formula=eq,index=0),dict(rule='assumption',formula=before,index=1),
            dict(rule='eq_subst',formula=schema,variable=hole,template=template,left=s,right=t),
            dict(rule='mp',formula=I(before,after),antecedent=0,implication=2),dict(rule='mp',formula=after,antecedent=1,implication=3)]
        d=dict(premises=[eq,before],conclusion=after,proof=proof);name='hilbert-'+digest(d)
        definitions.append(dict(name=name,level=1,family='incidence-equality-transport',arguments=[point,left,right],definition=dict(name=name,**d)))
        recipes.append(dict(name=name,kind='incidence-equality-transport',point=point,left=left,right=right))
    fs=[basis[k] for k in sorted(basis)]
    catalog=dict(basis=fs,variables=[],schemes=[],scope='Complete 16 uniqueness and 12 incidence-line-transport grounding grammar, no cone restriction. Formula outputs are the declared rule interfaces, input axioms and target; no target proof is supplied.')
    return dict(catalog=catalog,definitions=definitions,recipes=recipes,construction_seconds=time.perf_counter()-started)

def prepare(spec,oracle,limit):
    built=syntax_and_definitions(spec);started=time.perf_counter();records=[];tauts=[];taut=['imp',['bot'],['bot']]
    def submit(proof,target,blocks,purpose):
        q=oracle.request(dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=blocks,proof=proof,target=target),limit,purpose)
        records.append(q['id']);return q
    q=submit([dict(rule='tautology',formula=taut)],taut,[],'hilbert_theory_admission')
    if q['result']['status']!='accepted':raise ValueError('theory native admission unfinished')
    theory_query=q['id']
    for f in built['catalog']['basis']:
        q=submit([dict(rule='tautology',formula=f)],f,[],'hilbert_tautology_guard')
        if q['result']['status']=='accepted':tauts.append(f)
        elif q['result']['status']!='rejected':raise ValueError('native tautology compilation unfinished')
    compiled=dict(status='complete',catalog=built['catalog'],basis=built['catalog']['basis'],variables=[],admitted_schemes=[],tautologies=tauts,queries=list(records),theory_query=theory_query)
    compiled['seconds']=time.perf_counter()-started;admissions=[];admit_start=time.perf_counter()
    for d in built['definitions']:
        q=submit([dict(rule='tautology',formula=taut)],taut,[d['definition']],'hilbert_definition_admission')
        if q['result']['status']!='accepted':raise ValueError('definition native admission unfinished '+d['name'])
        admissions.append(dict(name=d['name'],query=q['id']))
    inventory=dict(status='native_accepted',definitions=built['definitions'],interfaces=[d['name'] for d in built['definitions']],native_blocks=[d['definition'] for d in built['definitions']],admissions=admissions,recipes=built['recipes'],admission_seconds=time.perf_counter()-admit_start)
    return compiled,inventory,built['construction_seconds']
