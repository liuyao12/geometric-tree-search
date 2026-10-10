"""Independent finite geometry inventory, full-prefix and primitive replay.

Imports no geometry generator, search engine or point model. The declared
congruence axioms are the explicit foundation, not conclusions of this audit.
"""
import collections,hashlib,itertools,json,time
from pathlib import Path
import logic as L
from audit_serialized_kernel import freeze,replay
import audit_semantic_proofs as A
import audit_induction_proofs as I
import audit_induction_clusters as H
from audit_proof_compaction import native_binding
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
THEORY_PINS={'full': '3d952072ba89ff39b6522cff13733d947e62b7045674cdf2c1480318ee9108ec', 'no-SAS': '6ebd3e51b4f63beabc68b3c1214824c651fd0461781edeb5a64fe1b31dafe390', 'no-ASA': '1d60bbaa04440be9d951451720ca3b0506dcb1843eb856a08d1f12391ad76706'}
# Pins bind the explicitly reviewed congruence foundation; they do not prove it.
def need(v,s):
    if not v:raise ValueError(s)
def packed(a):return json.dumps(a,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def chain(ps,q):
    for p in reversed(ps):q=L.Imp(p,q)
    return q

def inventory(c):
    c=freeze(c);conf=c['configuration'];vertices=conf['vertices'];h=conf['hypothesis'];goal=conf['goal']
    key='no-SAS' if conf['omit']==('SAS',) else 'no-ASA' if conf['omit']==('ASA',) else 'full'
    need(hashlib.sha256(packed(c['theory'])).hexdigest()==THEORY_PINS[key],'agreed geometry foundation')
    need(vertices==('a','b','c') and c['theory']['schemas']==() and c['theory']['functions']=={},'geometry-only signature')
    rows=[]
    for name,ax in c['theory']['axioms'].items():
        vs=[];body=ax
        while body[0]=='all':vs.append(body[1]);body=body[2]
        ps=[]
        while body[0]=='imp':ps.append(body[1]);body=body[2]
        for values in itertools.product(vertices,repeat=len(vs)):
            env=dict(zip(vs,values))
            def subst(a):
                for v in vs:a=L.substitute(a,v,L.V(env[v]))
                return a
            inputs=tuple(map(subst,ps));q=subst(body)
            def valid(a):
                need(a[0]=='pred' and all(x[0]=='var' for x in a[2]),'positive geometric atom')
                x=[t[1] for t in a[2]]
                if a[1]=='Triangle':return len(set(x))==3
                if a[1] in ('AngleEq','Congruent'):return len(set(x[:3]))==3 and len(set(x[3:]))==3
                need(a[1]=='SegEq','known predicate');return x[0]!=x[1] and x[2]!=x[3]
            if all(valid(a) for a in inputs+(q,)):rows.append((name,env,inputs,q))
    needed={goal};chosen=[]
    while True:
        selected=[r for r in rows if r[3] in needed and r not in chosen]
        if not selected:break
        chosen.extend(selected)
        needed.update(p for r in selected for p in r[2])
    need(conf['ground_rules']==len(rows) and conf['cone_rules']==len(chosen) and conf['cone_atoms']==len(needed),'complete grounded backward cone')
    fs={L.Imp(h,a) for a in needed};expected=[]
    for a in (h[1:] if h[0]=='and' else (h,)):
        q=L.Imp(h,a);fs.add(q);expected.append(((),q,dict(kind='primitive',witness=dict(rule='tautology',formula=q))))
    for name,env,ps,q in chosen:
        take=min(2,len(ps));inputs=tuple(L.Imp(h,a) for a in ps[:take]);out=L.Imp(h,chain(ps[take:],q));fs.update(inputs);fs.add(out)
        expected.append((inputs,out,dict(kind='block',operation='geometry-rule',axiom=name,bindings=env,phase=0)))
        for j in range(take,len(ps)):
            tail=chain(ps[j+1:],q);inputs=(L.Imp(h,L.Imp(ps[j],tail)),L.Imp(h,ps[j]));out=L.Imp(h,tail);fs.update(inputs);fs.add(out)
            expected.append((inputs,out,dict(kind='block',operation='geometry-join',axiom=name,bindings=env,phase=j-take+1)))
    expected.extend(((a,),a,dict(kind='copy')) for a in fs)
    need(set(c['formulas'])==fs and len(c['formulas'])==len(fs),'entire formula language')
    actual=[];blocks={}
    for r in c['rules']:
        inputs=tuple(c['formulas'][i] for i in r['inputs']);out=c['formulas'][r['output']];recipe=dict(r['recipe'])
        if recipe['kind']=='block':
            b=recipe.pop('definition');need(b['premises']==inputs and b['conclusion']==out,'compiled block interface')
            need(b['name'] not in blocks or blocks[b['name']]==b,'consistent block identity');blocks[b['name']]=b
        actual.append((inputs,out,recipe))
    need(collections.Counter(packed(a) for a in actual)==collections.Counter(packed(a) for a in expected),'all and only finite rule instances, including all copies')
    probe=dict(protocol='gcts-fol-1',theory=c['theory'],target=L.Imp(c['target'],c['target']),blocks=list(blocks.values()),proof=[dict(rule='tautology',formula=L.Imp(c['target'],c['target']))])
    check=replay(packed(probe));need(check['status']=='accepted','every compiled block primitive replay: '+check.get('reason',''))
    return dict(formulas=len(fs),rules=len(actual),definitions=len(blocks),ground_rules=len(rows),cone_rules=len(chosen))

def run_audit(row):
    c=freeze(row['catalog']);r=freeze(row['result']);n=row['length']
    p=freeze(row['problem']);need(c['target']==p['target'] and c['configuration']['hypothesis']==p['hypothesis'] and c['configuration']['goal']==p['goal'],'external statement binding')
    target=L.Imp(p['hypothesis'],p['goal'])
    for x in reversed(('a','b','c')):target=L.All(x,target)
    need(target==p['target'],'closed conditional statement')
    result=I.point_run(c,n,r) if row['lane']=='gcts' else H.csp_run(c,n,r,())
    if 'decoded' in r:
        primitive=replay(packed(r['decoded']['request']));need(primitive['status']=='accepted','complete root primitive replay')
        need(row['native']['status']=='accepted','native gate')
        code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program']
        native_binding(code,r['decoded']['request'],row['native'])
        result['primitive_lines']=primitive['expanded_lines']
    return result

def main():
    path=DOCS/'euclidean-proofs-001.json';d=json.loads(path.read_text());began=time.perf_counter()
    for name,pin in d['sources'].items():need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==pin,'source pin '+name)
    need([(r['id'],r['lane'],r['length']) for r in d['runs']]==[(name,lane,n) for name,n in [('I.5',10),('I.6',10),('triangle-order',3),('I.5-no-SAS',10),('I.6-no-ASA',10),('I.5-short',9)] for lane in ('gcts','csp')],'complete pilot/control matrix')
    counts={};runs=[]
    for row in d['runs']:
        pin=hashlib.sha256(packed(row['catalog'])).hexdigest()
        if pin not in counts:counts[pin]=inventory(row['catalog'])
        runs.append(dict(id=row['id'],lane=row['lane'],audit=run_audit(row)))
    d['independent_audit']=dict(status='passed',seconds=time.perf_counter()-began,inventories=list(counts.values()),runs=runs,scope='independent grounding and backward cone; all compiled block interfaces and primitive expansions; every point or AC prefix, graph decisions and rollback; source pins and native code/input bindings; finite geometry fragment only')
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps(d['independent_audit'],indent=2))
if __name__=='__main__':main()
