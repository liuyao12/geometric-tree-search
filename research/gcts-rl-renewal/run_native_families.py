"""Cold donor mining, zero-start sampled learning and balanced native controls."""
import gzip,hashlib,json,statistics,subprocess,time
from pathlib import Path
from shared_wang_inventory import Inventory,TABLE_PIN
from native_family_catalog import mine
from native_family_cases import donors,training,evaluation
from native_family_policy import FEATURES,update
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-native-families-20261010');LANES=('marks','families','rl','zero');EPOCHS=4
SOURCES=('native_family_catalog.py','native_family_policy.py','native_family_search.py','native_family_cases.py','native_family_worker.py','check_native_family_points.py','run_native_families.py','native_wang_domains.cpp','native_wang_search.py','native_wang_cases.py','shared_wang_inventory.py','check_native_rectangle.py','serialized_kernel.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);folder=DOC/'native-families-001';folder.mkdir(exist_ok=True);pins={n:sha(HERE/n) for n in SOURCES};raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());inventory=Inventory(raw);(TMP/'table.bin').write_bytes(raw)
    before=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'native_wang_domains.cpp'),'-o',str(TMP/'domains')],check=True);compile_seconds=time.perf_counter()-before
    def run(spec,name,library=(),mode='base',weights=None,stochastic=False,seed=0):
        request=TMP/'request.json';request.write_bytes(canonical(dict(spec=spec,library=library,mode=mode,weights=weights,stochastic=stochastic,seed=seed)));out=folder/(name+'.json.gz');started=time.perf_counter();subprocess.run(['python3',str(HERE/'native_family_worker.py'),str(request),str(out),str(TMP/'domains'),str(TMP/'table.bin')],check=True);row=json.loads(gzip.decompress(out.read_bytes()));ref=dict(file=str(out.relative_to(DOC)),sha256=sha(out),bytes=out.stat().st_size,stage_seconds=time.perf_counter()-started,semantic_sha256=row['semantic_sha256'],status=row['result']['status'],attempts=row['result']['attempts'],total_seconds=row['result']['total_seconds']);return row,ref
    donor_rows=[];library=[];donor_refs=[];stage=time.perf_counter()
    for index,spec in enumerate(donors(inventory,DOC)):
        row,ref=run(spec,'donor-'+str(index),library,'fixed' if library else 'base');donor_rows.append(row);donor_refs.append(dict(spec=spec,raw=ref,input_library=library));library,mining=mine(donor_rows,inventory)
    donor_seconds=time.perf_counter()-stage;specs=training(inventory);weights=[0.]*len(FEATURES);baselines={s['id']:0. for s in specs};episodes=[];stage=time.perf_counter()
    for epoch in range(EPOCHS):
        for index,spec in enumerate(specs):
            before=weights[:];row,ref=run(spec,'episode-'+str(len(episodes)),library,'policy',weights,True,59000+len(episodes));weights,baseline,change=update(weights,baselines[spec['id']],row['result']);baselines[spec['id']]=baseline;episodes.append(dict(epoch=epoch,index=index,weights_before=before,raw=ref,update=change));(TMP/'training-progress.json').write_bytes(canonical(dict(episodes=episodes,weights=weights)))
    train_seconds=time.perf_counter()-stage;cases=[];stage=time.perf_counter()
    for index,spec in enumerate(evaluation(inventory,DOC)):
        runs=[]
        for rep in range(4):
            off=(index+rep)%4;order=LANES[off:]+LANES[:off]
            for lane in order:
                mode='base' if lane=='marks' else 'fixed' if lane=='families' else 'policy';ws=weights if lane=='rl' else [0.]*len(FEATURES) if lane=='zero' else None;row,ref=run(spec,'case-'+str(index)+'-'+lane+'-'+str(rep),() if lane=='marks' else library,mode,ws);ref.update(lane=lane,repetition=rep,order=order);runs.append(ref)
        timings={lane:dict(median_seconds=statistics.median(r['total_seconds'] for r in runs if r['lane']==lane),samples=[r for r in runs if r['lane']==lane]) for lane in LANES};cases.append(dict(spec=spec,runs=runs,timings=timings));(TMP/'evaluation-progress.json').write_bytes(canonical(cases));print('EVALUATION COMPLETE',spec['id'],flush=True)
    for n,pin in pins.items():assert sha(HERE/n)==pin,'measured source changed '+n
    data=dict(version='native-families-001',sources=pins,reused_inputs={n:sha(DOC/n) for n in ('proof-boundary-machine-001.bin.gz','proof-boundary-001.json','shared-wang-reader-001.json')},literal_table_sha256=TABLE_PIN,inventory_fingerprint=inventory.fingerprint,tile_types=sum(inventory.counts.values()),A=inventory.A,Q=inventory.Q,D=inventory.D,lanes=LANES,repetitions=4,donors=donor_refs,library=library,mining=mining,donor_seconds=donor_seconds,training=dict(specs=specs,epochs=EPOCHS,features=FEATURES,initial_weights=[0.]*len(FEATURES),weights=weights,baselines=baselines,episodes=episodes,seconds=train_seconds),cases=cases,evaluation_seconds=time.perf_counter()-stage,compile_seconds=compile_seconds,seconds=time.perf_counter()-began,limits=dict(attempts=350,seconds=60,proposal_limit=8),scope='Guarded variable native families mined only from fresh native rectangles; branch-local concurrent ordering hints with complete original fallback and the unchanged point scheduler. Cold sampled shared policy, separately matched fixed and zero controls. Still local native engine fixtures, not full mathematical proof discovery or a universal compiler proof.',timing_scope='Fresh process per native solve. Cold clocks include input/table reading, pin checks, oracle startup, complete native graph, cone synthesis, optional family validation and all matching/scoring/reviews, rollback, original/decorated point checks and completed-cluster checking. Module import/startup, raw serialization and parent loading are outside solve clocks; all worker stages, cold donor mining, training, compile and complete suite clocks are recorded. OS caches are not cleared; RSS is Python-worker only.')
    (DOC/'native-families-001.json').write_bytes(canonical(data)+b'\n');print('SUITE COMPLETE',data['seconds'],flush=True)
if __name__=='__main__':main()
