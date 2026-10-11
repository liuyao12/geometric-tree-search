"""Cold evaluation and fresh native-feedback inventory-policy training."""
import copy,gzip,hashlib,json,sys,time
from pathlib import Path
from certificate_boundary_search import Oracle,canonical,digest
from native_receptor_points import Model,compile_guards,search as donor_search
from native_inference_inventory import mine,combine
from native_inventory_search import search
from native_inventory_policy import FEATURES,EPISODES,RATE,reward,update
from proof_boundary import boundary_words
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def oracle_for(job):
    directory=Path(job['directory']);directory.mkdir(parents=True,exist_ok=True);micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));old=json.loads((DOC/'proof-boundary-001.json').read_text())
    if digest(micro)!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM:raise ValueError('fixed checker binding')
    (directory/'code.bin').write_bytes(code_bytes(micro));return Oracle(micro,old['cases'][0]['initial'],job['executable'],directory/'code.bin',directory)
def verify(oracle,spec,proof,purpose):
    rec=oracle.query(spec,proof,True,10**9);rec['purpose']=purpose
    if rec['result']['status']=='rejected':raise ValueError('point proof rejected by the native kernel')
    return rec
def train(job,oracle):
    stage=time.perf_counter();donors=[];catalog={};mined=[];cache={}
    for spec in job['donors']:
        compiled=compile_guards(spec,oracle);model=Model(spec,compiled);found=donor_search(model,attempts=2000);rec=verify(oracle,spec,found['proof'],'new_inventory_donor')
        if rec['result']['status']!='accepted':raise ValueError('unverified donor cannot enter inventory')
        catalog[spec['id']]=compiled;cache[rec['request_sha256']]=rec['id'];mined+=mine(model,found['placements'],spec['id']);donors.append(dict(case=spec,compiled=compiled,model=model.record(),search=found,verification_query=rec['id']))
    library=combine(mined);weights=[0.]*len(FEATURES);baseline=0.;episodes=[]
    for index in range(EPISODES):
        spec=job['donors'][index%len(job['donors'])];model=Model(spec,catalog[spec['id']]);before=weights.copy();out=search(model,library,'learned',weights=before,stochastic=True,seed=10000+index,attempts=2000,seconds=30);accepted=False;query=None;cached=False
        if out['proof']:
            request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=out['proof'],target=spec['target']);key=digest(request)
            if key in cache:query=cache[key];accepted=True;cached=True
            else:
                rec=verify(oracle,spec,out['proof'],'training_feedback');query=rec['id'];accepted=rec['result']['status']=='accepted'
                if accepted:cache[key]=query
        value=reward(out,accepted);weights,baseline,learning=update(weights,out['events'],value,baseline);episodes.append(dict(id=index,case=spec['id'],search=out,accepted=accepted,verification_query=query,cached_native_acceptance=cached,weights_before=before,weights_after=weights.copy(),baseline_after=baseline,learning=learning));print('episode',index,spec['id'],out['metrics'].get('attempts',0),round(value,6),cached,flush=True)
    return dict(version='native-inventory-training-001',donors=donors,library=library,features=FEATURES,rate=RATE,episodes=episodes,weights=weights,baseline=baseline,training_seconds=time.perf_counter()-stage,scope='Fresh zero-start policy and newly native-checked GCTS donors. No prior proof sequence, inventory, policy weight or evaluation assertion is imported. Each unique successful training certificate receives whole native checking; repeated identical accepted certificates use an explicitly recorded training-only cache. Models and graphs start fresh per rollout; native tautology catalogs are reused only within training.')
def evaluate(job,oracle):
    policy_path=Path(job['policy']);raw=policy_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=job['policy_sha256']:raise ValueError('frozen inventory and weights')
    policy=json.loads(raw);spec=job['case'];compiled=compile_guards(spec,oracle)
    if compiled['status']!='complete':return dict(status=compiled['status'],proof=None,case=spec,compiled=compiled,model=None,search=None,mode=job['mode'])
    model=Model(spec,compiled);out=search(model,policy['library'],job['mode'],weights=policy['weights'],stochastic=False,seed=job['seed'],attempts=spec.get('attempts',2000),seconds=30);result=dict(status=out['status'],proof=out['proof'],case=spec,compiled=compiled,model=model.record(),search=out,mode=job['mode'],policy_sha256=job['policy_sha256'],repetition=job['repetition'],method_order=job['method_order'])
    if out['proof']:
        rec=verify(oracle,spec,out['proof'],'frozen_evaluation_without_search_hints');result['verification_query']=rec['id'];result['status']='native_proof_discovered' if rec['result']['status']=='accepted' else 'unknown_native_verification'
    return result
def main():
    began=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text());oracle=oracle_for(job)
    try:
        result=train(job,oracle) if job['kind']=='training' else evaluate(job,oracle)
        for rec in oracle.records:
            fixed,free=boundary_words(rec['request']);rec['boundary_words']=dict(fixed=fixed,free=free)
        result['records']=oracle.records;result['queries']=len(oracle.records)
    finally:
        oracle.close()
        for stream in (oracle.process.stdin,oracle.process.stdout,oracle.process.stderr):stream.close()
    result['cold_seconds']=time.perf_counter()-began;Path(sys.argv[2]).write_text(json.dumps(result,separators=(',',':'))+'\n');print('worker complete',job['kind'],result['queries'],round(result['cold_seconds'],3),flush=True)
if __name__=='__main__':main()
