"""Literal reconstruction of the request controller and every saved base move."""
import copy,hashlib,json,math,random,resource,time
from collections import defaultdict
from pathlib import Path
from boundary_responses import declarations
from response_resolution import training_boundaries
from audit_boundary_macros import Oracle
from audit_boundary_responses import normal,matched_execution

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
MODES=('base','small','hierarchy')
def declared_features(b):
    spans=[max(p[i] for p in b.required)-min(p[i] for p in b.required)+1 for i in range(3)]
    return [{f'mode:{mode}:bias':1.,f'mode:{mode}:area':len(b.required)/300,
             f'mode:{mode}:density':len(b.required)/(min(spans)*max(spans)),
             f'mode:{mode}:exterior':float(bool(b.exterior)),f'mode:{mode}:span':max(spans)/24} for mode in MODES]
def scores(weights,fs):return [sum(weights.get(k,0)*v for k,v in f.items()) for f in fs]
def chosen_valid(row,b,weights,zero=False):
    fs=declared_features(b);ss=scores({} if zero else weights,fs);top=max(ss)
    i=random.Random(row['result']['seed']).choice([j for j,v in enumerate(ss) if v==top])
    return row['features']==fs and row['scores']==ss and row['mode']==MODES[i]

def main():
    start=time.monotonic();path=DOCS/'response-resolution-001.json';d=json.loads(path.read_text());p=json.loads((DOCS/d['source_artifact']).read_text())
    for name,s in d['sources'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==s
    assert hashlib.sha256(json.dumps(p['library'],separators=(',',':')).encode()).hexdigest()==d['library_sha256']
    raw={k:v for k,v in p.items() if k not in ('independent_audit','semantic_tests')}
    assert hashlib.sha256((json.dumps(raw,separators=(',',':'))+'\n').encode()).hexdigest()==d['source_sha256_before_audit']
    evals=declarations();train=training_boundaries(evals[0].allowed);bs={b.identity:b for b in (*train,*evals)}
    assert d['training_problems']==normal([b.packed() for b in train]) and d['problems']==normal([b.packed() for b in evals])
    assert d['training']['initial_weights']=={} and not d['training']['initial_policy_imported']
    oracle=Oracle(evals[0].allowed);weights=defaultdict(float);baseline=0.;checked=moves=complete=matched=0
    def replay(row,b):
        nonlocal checked,moves,complete,matched
        r=row['result'];assert oracle.replay(r,b)
        if row['mode']!='base':
            assert matched_execution(r,b,oracle,p['library'],True);matched+=1
            if row['mode']=='small':assert all(s['proposal_size']<=4 for s in r['execution'])
        else:assert all(s['response']=='singleton' for s in r['execution'])
        checked+=1;moves+=len(r['execution']);complete+=r['status']=='finite_exact_region'
    for i,row in enumerate(d['training']['episodes']):
        b=train[i%len(train)];assert row['problem']==b.identity and row['result']['seed']==120000+i
        fs=declared_features(b);assert row['features']==fs;ss=scores(weights,fs);top=max(ss);vs=[math.exp(x-top) for x in ss];prob=[x/sum(vs) for x in vs]
        action=random.Random(120000+i).choices(range(3),weights=prob)[0];assert row['mode']==MODES[action]
        reward=2*float(row['result']['status']=='finite_exact_region')+row['result']['coverage_fraction']-row['result']['seconds']
        assert row['reward']==reward
        expected=defaultdict(float)
        for q,f in zip(prob,fs):
            for k,v in f.items():expected[k]+=q*v
        advantage=reward-baseline;baseline=.9*baseline+.1*reward
        for k in fs[action].keys()|expected.keys():weights[k]+=.03*advantage*(fs[action].get(k,0)-expected.get(k,0))
        replay(row,b)
    assert set(weights)==set(d['training']['weights']) and all(abs(v-d['training']['weights'][k])<1e-12 for k,v in weights.items())
    assert abs(baseline-d['training']['baseline'])<1e-12 and d['training']['updates']==42
    for row in d['evaluation']:
        b=bs[row['problem']]
        if row['lane']=='base':assert row['mode']=='base'
        else:assert chosen_valid(row,b,d['training']['weights'],row['lane'].endswith('+zero'))
        replay(row,b)
    tamper=[];row=next(r for r in d['evaluation'] if r['lane']=='resolution+RL');b=bs[row['problem']]
    for kind in ('wrong-resolution','altered-features','altered-score'):
        bad=copy.deepcopy(row)
        if kind=='wrong-resolution':bad['mode']=next(m for m in MODES if m!=bad['mode'])
        if kind=='altered-features':bad['features'][0]['mode:base:area']+=1
        if kind=='altered-score':bad['scores'][0]+=1
        assert not chosen_valid(bad,b,d['training']['weights']);tamper.append(kind)
    d['independent_audit']={'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                           'response_helper_sha256':hashlib.sha256((HERE/'audit_boundary_responses.py').read_bytes()).hexdigest(),
                           'states':checked,'complete_states':complete,'scheduled_moves':moves,'response_states':matched,
                           'reconstructed_policy_updates':42,'tamper_rejections':tamper,'seconds':time.monotonic()-start,
                           'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                           'scope':'fixed externally declared targets, literal schedule, local response preconditions and recorded policy learning; timings remain measured observations'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps(d['independent_audit']),flush=True)

if __name__=='__main__':main()
