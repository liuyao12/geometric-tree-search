"""Cold source searches, fresh RL training, and matched held-out cluster ranking."""
import gzip,hashlib,json,resource,time
from pathlib import Path
import induction_proof_catalogs as C,induction_proof_problems as P,induction_proof_tiles as T
import induction_clusters as H,induction_cluster_policy as R
from run_induction_clusters import SOURCES as BASE_SOURCES
from run_semantic_proofs import declaration
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-induction-cluster-policy-001')
LANES=('gcts-fixed','gcts-rl','csp-fixed','csp-rl')
SOURCES=BASE_SOURCES+('induction_cluster_policy.py','audit_induction_cluster_policy.py','run_induction_cluster_policy.py','test_induction_cluster_policy.py','run_induction_cluster_policy_tests.py')
def sha(blob):return hashlib.sha256(blob).hexdigest()
def shard(row,folder,name):
    payload=json.dumps(row,separators=(',',':'),ensure_ascii=True).encode('ascii')+b'\n';blob=gzip.compress(payload,compresslevel=6,mtime=0)
    file=folder+'/'+name+'.json.gz';(DOCS/folder).mkdir(exist_ok=True)
    if len(blob)>=90000000:raise ValueError('compressed shard exceeds publication limit')
    (DOCS/file).write_bytes(blob)
    return dict(file=file,sha256=sha(blob),bytes=len(blob),raw_sha256=sha(payload),raw_bytes=len(payload))
def native(p,r,code):
    request=r['decoded']['request'];expected=problem_hash(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target']))
    result=tree_native.check(canonical(request),code,TMP,expected,steps=100000000)
    if result['status']!='accepted':raise ValueError('complete native acceptance required')
    return result
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);pins={n:sha((HERE/n).read_bytes()) for n in SOURCES};code=program()
    data=dict(sources=pins,program_sha256=sha(canonical(code)),initial_library=[],imported_policy=None,donors=[],episodes=[],cases=[],
      configuration=dict(seconds=20,donor_seconds=20,base_attempts=50000,training_seconds=3,training_attempts=2000,episodes=20,seed_base=36100,rate=0.2,native_steps=100000000,replicas=2,lanes=LANES,marked=True,motif_sizes=(2,3)),
      scope='Fresh source discovery and all connected two/three-cell fragment mining, then zero-initialized episodic REINFORCE ordering of validated macro proposals. The policy never prunes, bypasses propagation, changes the candidate universe, or supplies a proof sequence. Integer state/action features and quantized weights give exact greedy rankings. Sampling and policy-gradient arithmetic are numerical research controls, not part of the proof kernel. The bounded goal-derived induction grammar and fixed two/three-cell proposal resolution remain authored restrictions. This experiment learns selection; unrestricted composition/hierarchical cluster synthesis and universal Wang expressiveness remain open.',
      comparison='All four recipient lanes receive the same newly mined library, complete primitive inventory, necessary resource constraints, target/bounds, 20-second search wall, 50000 expanded-attempt cap and complete lossless trace instrumentation. Both RL lanes receive the identical frozen source-trained policy; both fixed lanes retain macro-first goal/size ordering. GCTS preserves its full point graph and scheduler; classical AC/MRV retains all ordinary values after macro proposals. Training catalog construction is charged once and reused across source episodes only. Each recipient catalog and model is fresh. Cold query time pays for catalog validation, all features/ranking, search, decoding and native checking. Add all source discovery/mining/training/native/trace-storage cost once to either RL lane for lifecycle comparisons; fixed-cluster lanes pay discovery/mining cost only. Point attempts and explicit classical assignments are different units. No cutoff is a negative label or non-provability claim. Two rotated replicas remain exploratory.')
    data['compile_seconds']=tree_native.compile_tool(TMP);training_start=time.perf_counter();library=[];donors=[]
    for p in P.problems()[:2]:
        start=time.perf_counter();c=C.catalog(p['theory'],p['target'],p['term_bound'],p['enable_induction']);decl=declaration(c);pin=sha(canonical(decl))
        r=T.search(c,p['length'],support=True,seconds=20,attempt_limit=50000)
        if r['status']!='finite_exact_proof_tiling':raise ValueError('fresh donor discovery failed '+p['id'])
        check=native(p,r,code);cold=time.perf_counter()-start;mining_start=time.perf_counter();mined=H.mine(c,r,p);library=H.merge(library,mined)
        row=dict(problem=p,catalog=decl,catalog_sha256=pin,run=dict(result=r,native=check,cold_seconds=cold,catalog_sha256=pin,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds']),mined=mined,mining_seconds=time.perf_counter()-mining_start)
        desc=shard(row,'induction-cluster-policy-donors-001',p['id']);data['donors'].append(dict(problem=p,**desc));donors.append((p,c,decl,pin))
        print('fresh donor',p['id'],r['nodes'],r['base_attempts'],round(cold,4),flush=True)
    data.update(library=library,library_sha256=H.digest(library),discovery_seconds=time.perf_counter()-training_start)
    policy=R.initial_policy(library);data['initial_policy']=policy;learning_start=time.perf_counter()
    for episode in range(20):
        p,c,decl,pin=donors[episode%2];start=time.perf_counter()
        if sha(canonical(declaration(c)))!=pin:raise ValueError('training catalog changed')
        r=R.point_search(c,p['length'],library,seconds=3,attempt_limit=2000,policy=policy,stochastic=True,seed=36100+episode)
        run=dict(result=r)
        if 'decoded' in r:run['native']=native(p,r,code)
        policy,record=R.update(policy,r);run.update(update=record,cold_seconds=time.perf_counter()-start)
        row=dict(episode=episode,problem=p,problem_id=p['id'],catalog_sha256=pin,run=run)
        data['episodes'].append(dict(episode=episode,problem=p,problem_id=p['id'],**shard(row,'induction-cluster-policy-training-001',f'episode-{episode:02d}')))
        print('learning',episode,p['id'],r['status'],r['base_attempts'],record['events'],round(record['reward'],4),round(run['cold_seconds'],4),flush=True)
    data.update(policy=policy,policy_sha256=H.digest(policy),rl_learning_seconds=time.perf_counter()-learning_start,training_seconds=time.perf_counter()-training_start)
    (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    for i,p in enumerate(P.problems()[2:]):
        row=dict(problem=p,runs=[]);binding=None
        for replica in range(2):
            shift=(i+replica)%4
            for lane in LANES[shift:]+LANES[:shift]:
                start=time.perf_counter();c=C.catalog(p['theory'],p['target'],p['term_bound'],p['enable_induction']);decl=declaration(c);pin=sha(canonical(decl))
                if binding is None:row.update(catalog=decl,catalog_sha256=pin);binding=pin
                if pin!=binding:raise ValueError('matched recipient catalogs differ')
                r=(R.csp_search if lane.startswith('csp') else R.point_search)(c,p['length'],library,seconds=20,attempt_limit=50000,marked=True,policy=policy if lane.endswith('rl') else None)
                run=dict(lane=lane,replica=replica,catalog_sha256=pin,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds'],result=r)
                if 'decoded' in r:run['native']=native(p,r,code)
                run['cold_seconds']=time.perf_counter()-start;row['runs'].append(run)
                print('recipient',p['id'],replica,lane,r['status'],r['nodes'],r['base_attempts'],r['macro_attempts'],round(run['cold_seconds'],4),flush=True)
        data['cases'].append(dict(problem=p,**shard(row,'induction-cluster-policy-cases-001',p['id'])))
        (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    if any(sha((HERE/n).read_bytes())!=pin for n,pin in pins.items()):raise ValueError('measured source changed during experiment')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (DOCS/'induction-cluster-policy-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('complete',round(data['total_seconds'],4),'training',round(data['training_seconds'],4),'weights',policy['weights'],flush=True)
if __name__=='__main__':main()
