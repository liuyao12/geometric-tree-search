"""Independent incidence grammar, search, native binding and finite models.

Imports no Hilbert generator, point model or search engine. Theory pins bind
the reviewed formalization, not a proof of faithfulness to Hilbert's prose.
The finite models are separate semantic controls, never proof-search inputs.
"""
import collections,hashlib,itertools,json,time
from pathlib import Path
import logic as L
from audit_serialized_kernel import freeze,replay
import audit_induction_proofs as I
import audit_induction_clusters as H
from audit_proof_compaction import native_binding
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
FOUNDATIONS={(): '92bb283fb033ab6048565d1f09ffc19ac441fe0a82f108e82e30f30b443a6f01',('I.2-uniqueness',):'5e857470973f5c77e68cd117a632966d285e832f28c12c0359ba799736282133'}
PROBLEMS={'intersection-unique':'8ef660df5f66fb3bc8bab64c49528b9cec4803526a3f0c7f892aacabd1572834','incidence-transfer':'6704a8a0d949deed74f85f9473c145b7c88c13043c0b45178d84d082c34ff61e','wrong-intersection':'6199e908d12dce53a598a2d2438ffc644c486c238e9333ddbdb1698089ff0dc3'}
def packed(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def digest(x):return hashlib.sha256(packed(x)).hexdigest()
def need(x,s):
    if not x:raise ValueError(s)
def ands(xs):
    out=xs[-1] if xs else L.Imp(('bot',),('bot',))
    for a in reversed(xs[:-1]):out=('and',a,out)
    return out
def neg(a):return a[1] if a[0]=='not' else L.Not(a)
def clauses(a,positive=True):
    op=a[0]
    if op=='not':return clauses(a[1],not positive)
    if op=='imp':return clauses(('or',L.Not(a[1]),a[2]),positive)
    if op in ('and','or'):
        x,y=clauses(a[1],positive),clauses(a[2],positive)
        if (op=='and' and positive) or (op=='or' and not positive):return x+y
        return [p+q for p in x for q in y]
    return [[a if positive else L.Not(a)]]
def subst(a,env):
    for x,y in env.items():a=L.substitute(a,x,L.V(y))
    return a
def pred(n,*xs):return ('pred',n,tuple(L.V(x) for x in xs))

def inventory(c):
    c=freeze(c);conf=c['configuration'];theory=c['theory'];metadata=conf['metadata'];sorts=conf['sorts'];h=conf['hypothesis'];goal=conf['goal']
    need(digest([theory,metadata])==FOUNDATIONS[conf['omit']],'reviewed source foundation and binder sorts')
    need(theory['functions']=={} and theory['predicates']==dict(Point=1,Line=1,Inc=2) and theory['schemas']==(),'pure incidence signature')
    need(sorts==dict(point=('a','b','c'),line=('u','v')),'declared finite sorted names')
    domains=dict(sorts,object=sorts['point']+sorts['line']);rows=[]
    for name,ax in theory['axioms'].items():
        vs=list(metadata[name]['binders']);body=ax
        for x in vs:need(body[0]=='all' and body[1]==x,'outer binders');body=body[2]
        for values in itertools.product(*(domains[metadata[name]['binders'][x]] for x in vs)):
            env=dict(zip(vs,values));instance=subst(body,env)
            for ci,clause in enumerate(clauses(instance)):
                for j,out in enumerate(clause):
                    rest=[neg(a) for i,a in enumerate(clause) if i!=j];ps=(ands(rest),) if rest else ()
                    recipe=dict(kind='axiom-clause',axiom=name,bindings=env,clause=ci,head=j)
                    rows.append((ps,out,recipe))
    need(len(rows)==conf['axiom_instances'],'all source clause orientations')
    ax_count=len(rows);hole='equalityHole'
    for sort,domain in sorts.items():
        ts=[pred('Point' if sort=='point' else 'Line',hole)]
        ts += [pred('Inc',hole,x) for x in sorts['line']] if sort=='point' else [pred('Inc',x,hole) for x in sorts['point']]
        ts += [L.Eq(L.V(hole),L.V(x)) for x in domain]+[L.Eq(L.V(x),L.V(hole)) for x in domain]
        for left,right,t in itertools.product(domain,domain,ts):
            a=subst(t,{hole:left});b=subst(t,{hole:right});recipe=dict(kind='equality-substitution',sort=sort,left=left,right=right,variable=hole,template=t)
            rows.append(((L.Eq(L.V(left),L.V(right)),a),b,recipe))
    need(len(rows)-ax_count==conf['equality_instances'],'all equality templates and substitutions')
    needed={goal};chosen=[]
    while True:
        more=[r for r in rows if r[1] in needed and r not in chosen]
        if not more:break
        chosen+=more;needed.update(a for r in more for a in r[0])
    need(len(chosen)==conf['cone_rules'] and len(needed)==conf['cone_formulas'],'full cyclic backward cone')
    fs={L.Imp(h,a) for a in needed};expected=[]
    for a in needed:
        q=L.Imp(h,a)
        if L.tautology(q):expected.append(((),q,dict(kind='primitive',witness=dict(rule='tautology',formula=q))))
        elif a[0]=='eq' and a[1]==a[2]:expected.append(((),q,dict(kind='block',operation='hilbert-reflexivity')))
    for ps,q,recipe in chosen:expected.append((tuple(L.Imp(h,a) for a in ps),L.Imp(h,q),dict(kind='block',operation='hilbert-rule',inference=recipe)))
    expected.extend(((a,),a,dict(kind='copy')) for a in fs)
    need(set(c['formulas'])==fs and len(c['formulas'])==len(fs),'complete formula inventory')
    actual=[];blocks={}
    for r in c['rules']:
        ps=tuple(c['formulas'][j] for j in r['inputs']);q=c['formulas'][r['output']];recipe=dict(r['recipe'])
        if recipe['kind']=='block':
            b=recipe.pop('definition');need(b['premises']==ps and b['conclusion']==q,'block interface')
            need(b['name'] not in blocks or blocks[b['name']]==b,'unambiguous block identity');blocks[b['name']]=b
        actual.append((ps,q,recipe))
    need(collections.Counter(map(packed,actual))==collections.Counter(map(packed,expected)),'all and only grammar inferences and copies')
    probe=dict(protocol='gcts-fol-1',theory=theory,target=L.Imp(c['target'],c['target']),blocks=list(blocks.values()),proof=[dict(rule='tautology',formula=L.Imp(c['target'],c['target']))])
    checked=replay(packed(probe));need(checked['status']=='accepted','all primitive compiled types: '+checked.get('reason',''))
    return dict(formulas=len(fs),rules=len(actual),definitions=len(blocks),axiom_instances=ax_count,equality_instances=len(rows)-ax_count,cone_rules=len(chosen),primitive_checks=checked['expanded_lines'])

def run_audit(row,code):
    c=freeze(row['catalog']);p=freeze(row['problem']);r=freeze(row['result']);n=row['length']
    need(digest(p)==PROBLEMS[p['name']],'external theorem binding')
    need(c['target']==p['target'] and c['configuration']['hypothesis']==p['hypothesis'] and c['configuration']['goal']==p['goal'],'catalog theorem binding')
    result=I.point_run(c,n,r) if row['lane']=='gcts' else H.csp_run(c,n,r,())
    if 'decoded' in r:
        request=r['decoded']['request'];proof=replay(packed(request));need(proof['status']=='accepted','primitive root replay')
        need(packed(proof['proof'])==packed(row['primitive_proof']) and proof['expanded_lines']==row['primitive_lines'],'displayed primitive expansion')
        native_binding(code,request,row['native']);need(row['native']['status']=='accepted','complete native acceptance')
        result['primitive_lines']=proof['expanded_lines']
    return result

def finite_model(duplicate=False):
    points=['P'+str(i) for i in range(1,8)]
    triples=sorted({tuple(sorted((a,b,a^b))) for a in range(1,8) for b in range(a+1,8)})
    lines=['L'+str(i) for i in range(len(triples))]
    inc=[['P'+str(p),line] for line,triple in zip(lines,triples) for p in triple]
    if duplicate:
        lines.append('extra-line');inc.extend([['P'+str(p),'extra-line'] for p in triples[0][:2]])
    return dict(universe=points+lines,relations=dict(Point=[[p] for p in points],Line=[[x] for x in lines],Inc=inc))

def evaluate(formula,model,env=None):
    relations={name:{tuple(x) for x in rows} for name,rows in model['relations'].items()};universe=model['universe']
    def truth(a,e):
        k=a[0]
        if k=='all':return all(truth(a[2],dict(e,**{a[1]:x})) for x in universe)
        if k=='not':return not truth(a[1],e)
        if k=='and':return truth(a[1],e) and truth(a[2],e)
        if k=='or':return truth(a[1],e) or truth(a[2],e)
        if k=='imp':return not truth(a[1],e) or truth(a[2],e)
        if k=='bot':return False
        if k=='eq':return e[a[1][1]]==e[a[2][1]]
        if k=='pred':return tuple(e[t[1]] for t in a[2]) in relations[a[1]]
        raise ValueError('unsupported model syntax')
    return truth(freeze(formula),env or {})

def model_controls(theory,problems):
    models=[finite_model(),finite_model(True)];rows=[]
    for i,m in enumerate(models):
        axioms={n:evaluate(a,m) for n,a in theory['axioms'].items()}
        theorems={n:evaluate(p['target'],m) for n,p in problems.items()}
        rows.append(dict(id='seven-point-incidence-model' if i==0 else 'two-point-overlap-countermodel',model=m,axioms=axioms,theorems=theorems))
    need(all(rows[0]['axioms'].values()),'finite full-incidence model')
    need(rows[0]['theorems']['intersection-unique'] and rows[0]['theorems']['incidence-transfer'] and not rows[0]['theorems']['wrong-intersection'],'finite model theorem controls')
    need(not rows[1]['axioms']['I.2-uniqueness'] and all(v for n,v in rows[1]['axioms'].items() if n!='I.2-uniqueness'),'only uniqueness axiom fails in countermodel')
    need(not rows[1]['theorems']['intersection-unique'] and not rows[1]['theorems']['incidence-transfer'],'weakened-foundation counterexamples')
    return dict(status='passed',cases=rows,scope='Abstract finite incidence interpretations of this fragment only; not models of order, congruence or the complete Hilbert plane. No model enters proof search.')

def main():
    path=DOCS/'hilbert-incidence-001.json';d=json.loads(path.read_text());began=time.perf_counter()
    for n,pin in d['sources'].items():need(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==pin,'frozen source '+n)
    need([(r['id'],r['lane']) for r in d['runs']]==[(name,lane) for name in ('intersection-unique','incidence-transfer','intersection-no-I2','transfer-no-I2','intersection-short','transfer-short','wrong-intersection') for lane in ('gcts','csp')],'complete matched trial matrix')
    cache={};runs=[]
    for row in d['runs']:
        key=digest(row['catalog'])
        if key not in cache:cache[key]=inventory(row['catalog'])
        runs.append(dict(id=row['id'],lane=row['lane'],audit=run_audit(row,d['native_program'])))
    theory=d['runs'][0]['catalog']['theory'];problems={r['problem']['name']:r['problem'] for r in d['runs']}
    models=model_controls(theory,problems);need(models==d['model_controls'],'recorded model controls')
    d['independent_audit']=dict(status='passed',seconds=time.perf_counter()-began,inventories=list(cache.values()),runs=runs,model_controls=models['status'],scope='Independent complete sorted grounding, clause orientations and equality templates; all primitive type expansions; every point/AC prefix and rollback; exact theorem/source/native bindings; separate finite semantic models. Source correspondence remains an explicitly reviewed formalization.')
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps(d['independent_audit'],indent=2))
if __name__=='__main__':main()
