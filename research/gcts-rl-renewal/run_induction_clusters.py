"""Fresh proof-DAG motif learning and matched point/classical transfer trials.

Reads statements and source code, never an earlier proof, library or result.
The two source proofs are searched first, and all connected two/three-cell
fragments are mined automatically. Both recipient solvers receive the same
proposal schemas and the same certified redundant resource constraints.
"""
import gzip,hashlib,json,resource,time
from pathlib import Path
import induction_proof_catalogs as C,induction_proof_problems as P,induction_proof_tiles as T
import induction_clusters as H
from run_induction_proofs import SOURCES as BASE_SOURCES
from run_semantic_proofs import declaration
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-induction-clusters-001')
LANES=('gcts-base','gcts-motifs','csp-base','csp-motifs')
SOURCES=BASE_SOURCES+('induction_clusters.py','audit_induction_clusters.py','run_induction_clusters.py','test_induction_clusters.py','run_induction_cluster_tests.py')
def sha(blob):return hashlib.sha256(blob).hexdigest()
def shard(row,folder):
    payload=json.dumps(row,separators=(',',':'),ensure_ascii=True).encode('ascii')+b'\n';blob=gzip.compress(payload,compresslevel=6,mtime=0)
    file=folder+'/'+row['problem']['id']+'.json.gz'
    if len(blob)>=90000000:raise ValueError('compressed shard exceeds publication limit')
    (DOCS/folder).mkdir(exist_ok=True);(DOCS/file).write_bytes(blob)
    return dict(problem=row['problem'],file=file,sha256=sha(blob),bytes=len(blob),raw_sha256=sha(payload),raw_bytes=len(payload))
def check(p,result,code):
    request=result['decoded']['request'];expected=problem_hash(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target']))
    native=tree_native.check(canonical(request),code,TMP,expected,steps=100000000)
    if native['status']!='accepted':raise ValueError('complete native gate '+str(native))
    return native
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);pins={n:sha((HERE/n).read_bytes()) for n in SOURCES};code=program()
    data=dict(sources=pins,program_sha256=sha(canonical(code)),initial_library=[],policy=None,donors=[],cases=[],
      configuration=dict(seconds=20,donor_seconds=20,base_attempts=50000,native_steps=100000000,replicas=2,lanes=LANES,motif_sizes=(2,3),marked=True),
      scope='Fresh induction proof-DAG fragment transfer. All connected two/three-cell fragments from two newly searched complete source proofs become rule-family plus translated premise-geometry schemas. Literal formulas, variables, hypothesis bodies and rewrite AST paths are not copied as instance restrictions. All exact recipient formula-port matches and original primitive placements remain available. Motifs are checked proposal metatiles, not imported universally quantified lemmas or learned pruning. Generalization stays a checked closed-root inference. This is a bounded positional proof grammar, not unrestricted PA or a uniform finite four-edge Wang system. No RL policy is used in this experiment.',
      comparison='Two rotating replicas of four lanes. All lanes use the same original theory, target, complete primitive grammar, proof-cell bound and certified redundant resource constraints. Both motif lanes receive the identical fresh learned library; both base lanes receive no motifs. A 20-second wall includes point/classical construction, support certification, motif instantiation, propagation and lossless trace instrumentation. Cold query time additionally includes complete catalog validation, proof decoding and native checking. Point costs count expanded constituent placements; classical costs count explicit constituent assignments after arc consistency, so these units differ. Atomic metatiles preserve exact solution sets and change the graph scheduler; no equality with the original primitive decision trace is claimed. A separate fresh-training cost is charged once to either motif lane for first-query/lifecycle comparisons, with reused-library timings explicitly separated. Full closed/open traces are kept. Two replicas are exploratory timing evidence, not a general speedup result.')
    data['compile_seconds']=tree_native.compile_tool(TMP);training_start=time.perf_counter();library=[]
    for p in P.problems()[:2]:
        start=time.perf_counter();c=C.catalog(p['theory'],p['target'],p['term_bound'],p['enable_induction']);decl=declaration(c);pin=sha(canonical(decl))
        r=T.search(c,p['length'],support=True,seconds=20,attempt_limit=50000)
        if r['status']!='finite_exact_proof_tiling':raise ValueError('source proof was not discovered '+p['id'])
        native=check(p,r,code);cold=time.perf_counter()-start;mining_start=time.perf_counter();mined=H.mine(c,r,p);library=H.merge(library,mined)
        row=dict(problem=p,catalog=decl,catalog_sha256=pin,run=dict(catalog_sha256=pin,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds'],result=r,native=native,cold_seconds=cold),mined=mined,mining_seconds=time.perf_counter()-mining_start)
        data['donors'].append(shard(row,'induction-cluster-donors-001'));print('source',p['id'],r['nodes'],r['base_attempts'],round(cold,4),'patterns',len(library),flush=True)
    data.update(library=library,library_sha256=H.digest(library),training_seconds=time.perf_counter()-training_start)
    (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    for i,p in enumerate(P.problems()[2:]):
        row=dict(problem=p,runs=[]);binding=None
        for replica in range(2):
            shift=(i+replica)%4
            for lane in LANES[shift:]+LANES[:shift]:
                start=time.perf_counter();c=C.catalog(p['theory'],p['target'],p['term_bound'],p['enable_induction']);decl=declaration(c);pin=sha(canonical(decl))
                if binding is None:row.update(catalog=decl,catalog_sha256=pin);binding=pin
                if pin!=binding:raise ValueError('matched catalog changed between lanes')
                active=library if lane.endswith('motifs') else ()
                r=(H.csp_search if lane.startswith('csp') else H.search)(c,p['length'],active,seconds=20,attempt_limit=50000,marked=True)
                run=dict(lane=lane,replica=replica,catalog_sha256=pin,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds'],result=r)
                if 'decoded' in r:run['native']=check(p,r,code)
                run['cold_seconds']=time.perf_counter()-start;row['runs'].append(run)
                print('transfer',p['id'],replica,lane,r['status'],r['nodes'],r['base_attempts'],r['macro_attempts'],round(run['cold_seconds'],4),flush=True)
        data['cases'].append(shard(row,'induction-cluster-cases-001'));(TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
        print('shard',p['id'],data['cases'][-1]['raw_bytes'],data['cases'][-1]['bytes'],flush=True)
    if any(sha((HERE/n).read_bytes())!=pin for n,pin in pins.items()):raise ValueError('measured source changed during experiment')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (DOCS/'induction-clusters-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('complete',round(data['total_seconds'],4),'training',round(data['training_seconds'],4),flush=True)
if __name__=='__main__':main()
