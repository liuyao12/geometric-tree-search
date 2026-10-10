"""Cold discovery, zero-initialized RL and five-way fresh-process comparison."""
import gc,gzip,json,statistics,subprocess,sys,time
from pathlib import Path
import quantifier_family_patterns as P
import movable_proof_regions as M
import budget_family_policy as Policy
from budget_family_cases import registry
from budget_family_worker import HERE,SOURCES,LIMITS,HEURISTIC,sha
from serialized_kernel import canonical

ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
LEDGER=ROOT/'.gcts-active/budget-family-20261010';DEST=DOC/'budget-families-001'
LANES=('budget','families','rl','zero','occupied');EPOCHS=8

def save(path,data):
    tmp=path.with_suffix('.partial');tmp.write_bytes(gzip.compress(canonical(data)+b'\n',mtime=0));tmp.replace(path)

def read(path,pins):
    r=json.loads(gzip.decompress(path.read_bytes()))
    if r['sources']!=pins:raise ValueError('completed stage source binding: '+path.name)
    return r

def reference(path,pins=None):
    DEST.mkdir(parents=True,exist_ok=True);target=DEST/path.name;target.write_bytes(path.read_bytes())
    return dict(path='budget-families-001/'+path.name,sha256=sha(target),bytes=target.stat().st_size,**(dict(sources=pins) if pins else {}))

def worker(group,index,lane,label,pins,library=None,weights=None,stochastic=False,seed=0):
    path=LEDGER/(label+'.json.gz')
    if not path.exists():
        args=[sys.executable,str(HERE/'budget_family_worker.py'),'--group',group,'--case',str(index),'--lane',lane,'--seed',str(seed),'--output',str(path)]
        if library:args+=['--library',str(library)]
        if weights is not None:args+=['--weights',json.dumps(weights)]
        if stochastic:args+=['--stochastic']
        subprocess.run(args,check=True)
    return path,read(path,pins)

def main():
    LEDGER.mkdir(parents=True,exist_ok=True);pins={n:sha(HERE/n) for n in SOURCES};ds,ts,es=registry()
    path=LEDGER/'discovery.json.gz';asset=LEDGER/'inventory.json.gz'
    if path.exists():discovery=read(path,pins)['data']
    else:
        began=time.perf_counter();donors=[];library=[]
        for i,spec in enumerate(ds):
            save(asset,library)
            _,d=worker('donor',i,'families' if library else 'budget','donor-'+str(i),pins,asset if library else None)
            r=d['result'];library.extend(P.promote(spec,M.freeze(d['catalog']),M.freeze(r),library,maximum=6));donors.append(d)
            print('donor',i,r['status'],r['metrics']['attempts'],'families',len(library),'levels',sorted(set(t['level'] for t in library)),flush=True)
        discovery=dict(donors=donors,library=library,seconds=time.perf_counter()-began)
        save(path,dict(sources=pins,data=discovery))
    library=discovery['library']
    minimal=[{k:v for k,v in t.items() if k!='source'} for t in library];save(asset,minimal)
    baseline_files=[];baselines={};training_seconds=0.
    for i,spec in enumerate(ts):
        stage=LEDGER/('baseline-stage-'+str(i)+'.json.gz')
        if stage.exists():record=read(stage,pins)['data']
        else:
            began=time.perf_counter();_,d=worker('training',i,'budget','baseline-'+str(i),pins)
            record=dict(spec=spec,catalog=d['catalog'],certificate=d['certificate'],result=d['result'],seconds=time.perf_counter()-began)
            save(stage,dict(sources=pins,data=record))
        baselines[spec['id']]=Policy.reward(record['result']);training_seconds+=record['seconds'];baseline_files.append(reference(stage,pins))
    weights=[0.]*12;episode_files=[]
    for epoch in range(EPOCHS):
        indices=list(range(len(ts)));offset=epoch%len(indices);indices=indices[offset:]+indices[:offset]
        for i in indices:
            j=len(episode_files);path=LEDGER/('episode-stage-'+str(j)+'.json.gz');spec=ts[i]
            if path.exists():episode=read(path,pins)['data']
            else:
                began=time.perf_counter();_,d=worker('training',i,'rl','episode-'+str(j),pins,asset,weights,True,57100+j)
                after,next_baseline,u=Policy.update(weights,baselines[spec['id']],d['result'])
                episode=dict(epoch=epoch,training_index=i,spec=spec,catalog=d['catalog'],certificate=d['certificate'],result=d['result'],weights_before=weights,update=u,seconds=time.perf_counter()-began)
                save(path,dict(sources=pins,data=episode))
            if episode['weights_before']!=weights or episode['training_index']!=i:raise ValueError('training checkpoint order')
            weights=episode['update']['weights_after'];baselines[spec['id']]=episode['update']['baseline_after'];training_seconds+=episode['seconds'];episode_files.append(reference(path,pins))
        print('epoch',epoch+1,'weights',weights,flush=True)
    refs=[];elapsed=0.
    for i,spec in enumerate(es):
        path=LEDGER/('case-'+str(i)+'.json.gz')
        if path.exists():record=read(path,pins)
        else:
            began=time.perf_counter();samples={lane:[] for lane in LANES};primary={};digests={}
            for rep in range(len(LANES)):
                off=(i+rep)%len(LANES);order=LANES[off:]+LANES[:off]
                for lane in order:
                    work,d=worker('evaluation',i,lane,'case-'+str(i)+'-'+lane+'-'+str(rep),pins,asset if lane!='budget' else None,weights if lane=='rl' else None)
                    r=d['result'];pin=r['semantic_sha256']
                    if lane not in primary:primary[lane]=reference(work);digests[lane]=pin
                    elif digests[lane]!=pin:raise ValueError('cold repeats changed semantic search; retain differing trees for a revised audit')
                    names=('total_seconds','seconds','preparation_seconds','synthesis_seconds','certification_seconds','library_load_seconds','positive_check_seconds','grammar_seconds')
                    samples[lane].append(dict(repetition=rep,order=order,**{k:r[k] for k in names},semantic_sha256=pin,status=r['status'],attempts=r['metrics']['attempts'],peak_process_rss_bytes=d['peak_process_rss_bytes']))
                    del d,r;gc.collect()
            _,d=worker('evaluation',i,'saturation','saturation-'+str(i),pins);control=d['result'];del d
            timings={lane:dict(samples=v,median_seconds=statistics.median(t['total_seconds'] for t in v),min_seconds=min(t['total_seconds'] for t in v),max_seconds=max(t['total_seconds'] for t in v)) for lane,v in samples.items()}
            record=dict(spec=spec,run_files=primary,timings=timings,controls=dict(saturation=control),sources=pins,seconds=time.perf_counter()-began)
            save(path,record)
        refs.append(reference(path));elapsed+=record['seconds']
        print(spec['id'],{lane:(record['timings'][lane]['samples'][0]['status'],record['timings'][lane]['samples'][0]['attempts'],round(1000*record['timings'][lane]['median_seconds'],2)) for lane in LANES},flush=True)
    out=dict(version='budget-families-001',sources=pins,discovery_file=reference(LEDGER/'discovery.json.gz',pins),
        donor_seconds=discovery['seconds'],training=dict(specs=ts,initial_weights=[0.]*12,weights=weights,baselines=baselines,features=Policy.FEATURES,rate=Policy.RATE,epochs=EPOCHS,seconds=training_seconds,baseline_files=baseline_files,episode_files=episode_files),
        case_files=refs,lanes=LANES,heuristic_weights=HEURISTIC,limits=LIMITS,repetitions=5,evaluation_seconds=elapsed,
        seconds=discovery['seconds']+training_seconds+elapsed,
        scope='Cold necessary-formula marking synthesis and hierarchical parameterized receptor families mined only from fresh donor proofs. Shared zero-initialized sampled attention uses justified dependency progress. Every transition is an original placement under the complete marked graph, global dead/forced/generation scheduler, exact copy rollback and full fallback. Finite positional adaptation; no supplied proof, new axiom, learned logical pruning, native universal tile execution or general first-order completeness.',
        timing_scope='Five independent fresh-process observations per lane/goal, each lane in every execution position. Solve clocks include statement construction, inventory loading, grammar, synthesis, independent necessity certification, policy support, all joins/scoring/search and positive source/point/primitive checks. Startup/module imports, serialization and parent loading are outside solve clocks. Completed discovery/training/evaluation stage clocks include those costs. Audit and validation remain separate; saturation is one independently scheduled observation.')
    (DOC/'budget-families-001.json').write_bytes(canonical(out)+b'\n');print('complete',out['seconds'],flush=True)

if __name__=='__main__':main()
