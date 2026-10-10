"""Cold, matched transfer of families mined from one freshly searched proof.

No prior certificate, library, model or policy is an input. This experiment
varies formulas and translations, retaining learned relative contact offsets.
Receptor-dependent deformation and recursive family composition are future
experiments, not claims made by this producer.
"""
import gzip,hashlib,json,resource,time
from pathlib import Path
import hilbert_witness_clusters as P
import hilbert_quantified_tiles as Q
import hilbert_incidence_tiles as F
import induction_proof_tiles as T
import induction_clusters as H
import indexed_proof_clusters as J
from run_hilbert_quantified import SOURCES as BASE
from run_semantic_proofs import declaration
from audit_serialized_kernel import replay
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native

HERE=Path(__file__).resolve().parent
DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-hilbert-witness-clusters-001')
LANES=('gcts-base','gcts-motifs','csp-base','csp-motifs')
SOURCES=BASE+('indexed_proof_clusters.py','hilbert_witness_clusters.py','test_indexed_proof_clusters.py','run_hilbert_witness_clusters.py','audit_hilbert_witness_clusters.py')

def sha(blob):return hashlib.sha256(blob).hexdigest()
def shard(row,folder):
    payload=json.dumps(row,separators=(',',':')).encode()+b'\n'
    blob=gzip.compress(payload,compresslevel=6,mtime=0)
    if len(blob)>=90000000:raise ValueError('publication shard limit')
    file=folder+'/'+row['id']+'.json.gz'
    (DOCS/folder).mkdir(exist_ok=True);(DOCS/file).write_bytes(blob)
    return dict(id=row['id'],problem=row['problem'],file=file,sha256=sha(blob),bytes=len(blob),raw_sha256=sha(payload),raw_bytes=len(payload))
def check(c,r,code):
    request=r['decoded']['request'];primitive=replay(canonical(request))
    if primitive['status']!='accepted':raise ValueError(primitive)
    expected=problem_hash(dict(protocol='gcts-fol-1',theory=c['theory'],target=c['target']))
    native=tree_native.check(canonical(request),code,TMP,expected,steps=1000000000)
    if native['status']!='accepted':raise ValueError(native)
    return dict(native=native,primitive_proof=primitive['proof'],primitive_lines=primitive['expanded_lines'])

def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True)
    pins={n:sha((HERE/n).read_bytes()) for n in SOURCES};code=program()
    foundation,metadata=F.foundation()
    data=dict(version='hilbert-witness-clusters-001',date='2026-10-10',sources=pins,native_program=code,initial_library=[],policy=None,donors=[],cases=[],foundation=foundation,foundation_metadata=metadata,
        configuration=dict(seconds=30,donor_seconds=30,base_attempts=10000,native_steps=1000000000,lanes=LANES,motif_sizes=(2,3),marked=True),
        scope='Planar symbolic Hilbert incidence only. One freshly searched line/point witness proof teaches every connected two/three-cell motif. Recipient instances vary literal formulas and use translations of learned contact offsets. Exact aggregate t/m values, distinct constituents and complete original base fallback preserve solutions. Atomic macro scheduling is an adaptation: no equality to the primitive decision trace is claimed. This is an authored bounded proof grammar, not a uniform four-edge Wang set, unrestricted first-order prover or recursively composed receptor-family engine. No RL is used.',
        comparison='Two rotating replicas for each positive recipient; one four-lane replica for each negative control. Each lane rebuilds its complete syntax catalog. Search has a fixed 30-second/10,000-expanded-attempt budget including model, resource, family instantiation and trace instrumentation. Cold time also includes catalog construction, decode, primitive replay and complete native acceptance. Training is charged once to either family lane for the first query. Generic native compilation and independent audit are additional shared costs. GCTS expanded placements and CSP assignments have different units. Two replicas are exploratory evidence.',
        development='Earlier probes selected these declared proof lengths and the same context-transport settings as quantified experiment 001. An exact indexed join replaced a slow Cartesian join; its complete instances are independently reconstructed. No development proof or library enters this fresh run.')
    data['compile_seconds']=tree_native.compile_tool(TMP)
    training_start=time.perf_counter();p=P.source();cold=time.perf_counter()
    c=Q.catalog(p,context_transport=p['transport']);decl=declaration(c);pin=sha(canonical(decl))
    r=T.search(c,p['length'],support=True,seconds=30,attempt_limit=10000)
    if r['status']!='finite_exact_proof_tiling':raise ValueError('fresh source not solved')
    run=dict(catalog_sha256=pin,catalog_build_seconds=c['build_seconds'],result=r,**check(c,r,code))
    run['cold_seconds']=time.perf_counter()-cold
    mining_start=time.perf_counter();mined=H.mine(c,r,p);library=H.merge([],mined)
    row=dict(id=p['id'],problem=p,catalog=decl,catalog_sha256=pin,run=run,mined=mined,mining_seconds=time.perf_counter()-mining_start)
    data['donors'].append(shard(row,'hilbert-cluster-donors-001'))
    data.update(library=library,library_sha256=H.digest(library),training_seconds=time.perf_counter()-training_start)
    print('source',p['id'],r['nodes'],r['base_attempts'],round(run['cold_seconds'],4),'families',len(library),'training',round(data['training_seconds'],4),flush=True)
    for i,(name,base,n,omit,replicas) in enumerate(P.cases()):
        p=P.problem(base);row=dict(id=name,problem=p,length=n,omit=omit,replicas=replicas,runs=[]);binding=None
        for replica in range(replicas):
            shift=(i+replica)%4
            for lane in LANES[shift:]+LANES[:shift]:
                start=time.perf_counter();c=Q.catalog(p,omit,context_transport=p['transport']);decl=declaration(c);pin=sha(canonical(decl))
                if binding is None:row.update(catalog=decl,catalog_sha256=pin);binding=pin
                if pin!=binding:raise ValueError('matched catalog changed')
                active=library if lane.endswith('motifs') else ()
                r=(J.csp_search if lane.startswith('csp') else J.search)(c,n,active,seconds=30,attempt_limit=10000,marked=True)
                run=dict(lane=lane,replica=replica,catalog_sha256=pin,catalog_build_seconds=c['build_seconds'],result=r)
                if 'decoded' in r:run.update(check(c,r,code))
                run['cold_seconds']=time.perf_counter()-start;row['runs'].append(run)
                print('recipient',name,replica,lane,r['status'],r['nodes'],r['base_attempts'],r['macro_attempts'],round(run['cold_seconds'],4),flush=True)
        data['cases'].append(shard(row,'hilbert-cluster-cases-001'))
        (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    if any(sha((HERE/n).read_bytes())!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (DOCS/'hilbert-witness-clusters-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('complete',round(data['total_seconds'],4),flush=True)
if __name__=='__main__':main()
