"""Independent bounded quantifier inventory, point/CSP trace and model audit.

Does not import the quantified generator, rule compiler or search engines.
Reconstructs every syntax production and checks every block in primitive FOL.
"""
import collections, hashlib, itertools, json, time
from pathlib import Path
import logic as L
from audit_serialized_kernel import freeze,replay
import audit_induction_proofs as I
import audit_induction_clusters as H
from audit_proof_compaction import native_binding
from audit_hilbert_incidence import evaluate,finite_model,clauses,ands,neg,packed,digest,need,pred
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TARGETS={'line-has-point':'732bdec3d1d5887074846d30fbf19591271a1082fdc03347d0b586d87d1e561e','unique-joining-line':'be70cc7adb0a24e3b4b75e296b613c5da8cb0fa7f4363de7cf2b9ff82e4c5515'}

def ex(a):
    return (a[1][1],a[1][2][1]) if a[0]=='not' and a[1][0]=='all' and a[1][2][0]=='not' else None
def size(a):
    if a[0] in ('eq','pred','bot'):return 1
    if a[0]=='all':return 1+size(a[2])
    return 1+sum(size(x) for x in a[1:])
def reconstruct(c):
    conf=c['configuration'];theory=c['theory'];domains=dict(conf['sorts'],object=conf['sorts']['point']+conf['sorts']['line']);source_rows=[];sources=set()
    for name,ax in theory['axioms'].items():
        roles=conf['metadata'][name]['binders'];outer=[];body=ax
        for _ in roles:outer.append(body[1]);body=body[2]
        need(set(outer)==set(roles),'source role/binder agreement')
        for values in itertools.product(*(domains[roles[x]] for x in outer)):
            a=ax
            for value in values:a=L.substitute(a[2],a[1],L.V(value))
            env=dict(zip(outer,values))
            for ci,clause in enumerate(clauses(a)):
                for head,literal in enumerate(clause):
                    rest=[neg(t) for i,t in enumerate(clause) if i!=head]
                    source_rows.append(dict(axiom=name,bindings=env,instance=a,kind='axiom-clause',clause=ci,head=head,premises=[ands(rest)] if rest else [],conclusion=literal))
            if a[0]=='imp' and ex(a[2]):sources.add((a[1],a[2]))
    sources=sorted(sources,key=repr);heads=collections.defaultdict(list)
    for r in source_rows:heads[r['conclusion']].append(r)
    start=L.Imp(conf['hypothesis'],conf['goal']);forms={start};work=[start];contexts={conf['hypothesis']:0};productions=[];known={}
    def taut(a):
        if a not in known:known[a]=L.tautology(a)
        return known[a]
    def child(g,a):
        d=contexts[g]+1
        if d>conf['context_depth']:return None
        t=('and',g,a);contexts[t]=min(contexts.get(t,d),d);return t
    def offer(ps,q,op,**params):
        if max(map(size,ps+[q]))>conf['formula_nodes']:return
        productions.append(dict(inputs=ps,output=q,operation=op,parameters=params))
        for a in ps:
            if a not in forms:forms.add(a);work.append(a)
    i=0
    while i<len(work):
        f=work[i];i+=1
        if taut(f):offer([],f,'tautology');continue
        if f[0]=='all':offer([f[2]],f,'generalize',variable=f[1]);continue
        need(f[0]=='imp' and f[1] in contexts,'context syntax domain');g,q=f[1:]
        if conf['context_transport'] and contexts[g]:offer([L.Imp(g[1],L.Imp(g[2],q))],f,'propositional')
        for row in heads[q]:offer([L.Imp(g,a) for a in row['premises']],f,'axiom-clause',row=row,context=g)
        if q[0]=='and':offer([L.Imp(g,q[1]),L.Imp(g,q[2])],f,'propositional')
        if q[0]=='imp':
            expanded=child(g,q[1])
            if expanded is not None:offer([L.Imp(expanded,q[2])],f,'propositional')
            e=ex(q[1])
            if e is not None and e[0] not in L.free(g)|L.free(q[2]):
                expanded=child(g,e[1])
                if expanded is not None:offer([L.All(e[0],L.Imp(expanded,q[2]))],f,'exists-eliminate',context=g,variable=e[0],body=e[1],conclusion=q[2])
        if q[0]=='all' and q[1] not in L.free(g):
            x,a=q[1:]
            if a[0]=='imp':
                expanded=child(g,a[1])
                if expanded is not None:offer([L.All(x,L.Imp(expanded,a[2]))],f,'forall-scope',context=g,variable=x,body=a[1],conclusion=a[2])
            offer([L.All(x,L.Imp(g,a))],f,'forall-distribute',context=g,variable=x,body=a)
        e=ex(q)
        if e is not None:offer([L.Imp(g,e[1])],f,'exists-introduce',context=g,variable=e[0],body=e[1],term=L.V(e[0]))
        if contexts[g]<conf['context_depth'] and q[0]!='imp':
            available=set(sources);todo=[g]
            while todo:
                a=todo.pop()
                if ex(a):available.add((a,a))
                if a[0]=='and':todo.extend(a[1:])
            for guard,e in sorted(available,key=repr):
                if e!=q and taut(L.Imp(g,guard)) and ex(e)[0] not in L.free(g)|L.free(q):
                    offer([L.Imp(g,e),L.Imp(g,L.Imp(e,q))],f,'propositional')
    unique={packed(r):r for r in productions}
    return list(unique.values()),forms,contexts,len(source_rows),len(sources)

def inventory(c):
    c=freeze(c);conf=c['configuration'];rows,fs,ctx,clause_count,source_count=reconstruct(c)
    need(c['theory']['functions']=={} and c['theory']['predicates']==dict(Point=1,Line=1,Inc=2) and c['theory']['schemas']==(),'uninterpreted pure signature')
    need(len(rows)==conf['productions'],'production count')
    need(clause_count==conf['clauses'] and source_count==conf['existential_sources'],'all source substitutions and orientations')
    need(set(c['formulas'])==fs and len(c['formulas'])==len(fs),'complete needed syntax including cycles')
    need(ctx=={x['formula']:x['depth'] for x in conf['contexts']},'complete context grammar')
    expected=[]
    for r in rows:
        op=r['operation'];params=r['parameters']
        recipe=dict(kind='primitive',witness=dict(rule=op,formula=r['output'],**params)) if op in ('tautology','generalize') else dict(kind='block',operation=op,inference=params)
        expected.append((tuple(r['inputs']),r['output'],recipe))
    expected.extend(((a,),a,dict(kind='copy')) for a in fs)
    actual=[];definitions={}
    for r in c['rules']:
        ps=tuple(c['formulas'][i] for i in r['inputs']);q=c['formulas'][r['output']];recipe=dict(r['recipe'])
        if recipe['kind']=='block':
            b=recipe.pop('definition');need(b['premises']==ps and b['conclusion']==q,'compiled interface');need(b['name'] not in definitions or definitions[b['name']]==b,'block identity');definitions[b['name']]=b
        actual.append((ps,q,recipe))
    need(collections.Counter(map(packed,actual))==collections.Counter(map(packed,expected)),'all and only bounded productions and copies')
    target=L.Imp(c['target'],c['target']);probe=dict(protocol='gcts-fol-1',theory=c['theory'],target=target,blocks=list(definitions.values()),proof=[dict(rule='tautology',formula=target)])
    proof=replay(packed(probe));need(proof['status']=='accepted','every block primitive check: '+proof.get('reason',''))
    return dict(status='passed',formulas=len(fs),rules=len(actual),blocks=len(definitions),primitive_block_lines=sum(b['expanded_lines'] for b in proof['blocks']),source_clause_instances=clause_count,contexts=len(ctx))

def models(theory,problems):
    base=finite_model();empty=json.loads(json.dumps(base));empty['universe'].append('empty-line');empty['relations']['Line'].append(['empty-line'])
    removed=json.loads(json.dumps(base));line=removed['relations']['Line'][0][0];removed['universe'].remove(line);removed['relations']['Line'].remove([line]);removed['relations']['Inc']=[a for a in removed['relations']['Inc'] if a[1]!=line]
    cases=[]
    for name,m,failed in [('full-incidence',base,None),('empty-line',empty,'I.3-line-points'),('missing-joining-line',removed,'I.1-existence'),('nonunique-line',finite_model(True),'I.2-uniqueness')]:
        ax={n:evaluate(a,m) for n,a in theory['axioms'].items()};ts={n:evaluate(p['target'],m) for n,p in problems.items()}
        need(all(v if n!=failed else not v for n,v in ax.items()),'exact omitted axiom in model '+name)
        if failed is None:need(all(ts.values()),'positive model statements')
        elif name=='empty-line':need(not ts['line-has-point'],'empty-line counterexample')
        else:need(not ts['unique-joining-line'],'joining-line counterexample')
        cases.append(dict(id=name,model=m,axioms=ax,theorems=ts))
    return dict(status='passed',cases=cases,scope='Abstract finite incidence models, separate from every search input; no coordinates and no claim to full Hilbert geometry.')

def main():
    path=DOCS/'hilbert-quantified-001.json';d=json.loads(path.read_text());began=time.perf_counter()
    need(digest([d['foundation'],d['foundation_metadata']])=='92bb283fb033ab6048565d1f09ffc19ac441fe0a82f108e82e30f30b443a6f01','reviewed published incidence foundation')
    need([(r['id'],r['lane']) for r in d['runs']]==[(n,l) for n in ('line-has-point','unique-joining-line','line-no-I3','joining-no-I1','joining-no-I2','line-short','joining-short') for l in ('gcts','csp')],'complete matched trial matrix')
    for name,pin in d['sources'].items():need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==pin,'frozen source '+name)
    cache={};runs=[]
    for row in d['runs']:
        c=freeze(row['catalog']);p=freeze(row['problem']);r=freeze(row['result']);key=digest([c['configuration'],c['theory'],c['target']])
        need(digest(p)==TARGETS[p['name']]==d['problem_pins'][p['name']],'declared external target')
        need(c['target']==p['target'] and c['configuration']['hypothesis']==p['hypothesis'] and c['configuration']['goal']==p['goal'],'exact target binding')
        # The source theory is the exact published foundation minus omissions.
        original=d['foundation'];expected=dict(original,axioms={n:a for n,a in original['axioms'].items() if n not in c['configuration']['omit']})
        need(packed(c['theory'])==packed(expected),'published Hilbert foundation')
        if key not in cache:cache[key]=inventory(c)
        trace=I.point_run(c,row['length'],r) if row['lane']=='gcts' else H.csp_run(c,row['length'],r,())
        if 'decoded' in r:
            request=r['decoded']['request'];proof=replay(packed(request));need(proof['status']=='accepted','selected primitive proof')
            need(packed(proof['proof'])==packed(row['primitive_proof']) and proof['expanded_lines']==row['primitive_lines'],'reader primitive binding')
            native_binding(d['native_program'],request,row['native']);need(row['native']['status']=='accepted','complete native gate');trace['primitive_lines']=proof['expanded_lines']
        runs.append(dict(id=row['id'],lane=row['lane'],audit=trace));print('audited',row['id'],row['lane'],flush=True)
    problems={r['problem']['name']:r['problem'] for r in d['runs']};semantic=models(d['foundation'],problems);need(semantic==d['model_controls'],'model record')
    d['independent_audit']=dict(status='passed',seconds=time.perf_counter()-began,inventories=list(cache.values()),runs=runs,models='passed',scope='Independent complete grammar reconstruction, all primitive blocks including eigenvariable conditions, full point/CSP trace and rollback, exact target/source/native bindings, separate finite countermodels. No performance or complete-Hilbert claim.')
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print('complete audit',round(d['independent_audit']['seconds'],3),flush=True)
if __name__=='__main__':main()
