"""Fresh sampled branch attention, complete fallback and paired cold controls.

Every completed stage is checkpointed. Re-entry consumes only source-pinned
completed stages; it does not restart a live process or retrain a frozen model.
"""
import gzip
import hashlib
import json
import resource
import statistics
import time
from pathlib import Path
import receptor_attention as A
import receptor_attention_search as S
from receptor_attention_cases import registry
import quantifier_family_patterns as P
import movable_proof_regions as M
from run_quantifier_families import SOURCES as OLD_SOURCES
from run_adaptive_clusters import inventory
from run_resumable_clusters import decorate,control
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
LEDGER=ROOT/'.gcts-active/receptor-attention-20261010'
SOURCES=tuple(dict.fromkeys(('run_receptor_attention.py','receptor_attention.py','receptor_attention_search.py','receptor_attention_cases.py',*OLD_SOURCES)))
LANES=('base','fixed','attention','zero','goal_heuristic')
HEURISTIC=(0.,0.,2.,1.,2.,0.,0.,0.,0.,0.,0.,0.)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events','attention_support','weights','stochastic','seed','mode')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def run(spec,library=(),mode='base',weights=None,stochastic=False,seed=0):
    began=time.perf_counter();cat=inventory(spec);grammar=time.perf_counter()-began
    model=M.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    result=S.search(model,library,mode,weights,stochastic,seed,attempts=50000,seconds=10,proposal_limit=32)
    result['grammar_seconds']=grammar;decorate(spec,cat,result);result['total_seconds']=time.perf_counter()-began
    return cat,result
def load_stage(name,pins):
    path=LEDGER/(name+'.json.gz')
    if not path.exists():return None
    record=json.loads(gzip.decompress(path.read_bytes()))
    if record['sources']!=pins:raise ValueError('checkpoint source mismatch: '+name)
    print('loaded completed stage',name,flush=True);return record['data']
def save_stage(name,pins,data):
    path=LEDGER/(name+'.json.gz');tmp=path.with_suffix('.partial')
    tmp.write_bytes(gzip.compress(canonical(dict(sources=pins,data=data))+b'\n',mtime=0));tmp.replace(path)

def main():
    LEDGER.mkdir(parents=True,exist_ok=True);pins={n:sha(HERE/n) for n in SOURCES};ds,ts,es=registry()
    discovery=load_stage('discovery',pins)
    if discovery is None:
        began=time.perf_counter();donors=[];library=[]
        for i,spec in enumerate(ds):
            cat,r=run(spec,library,'fixed' if library else 'base')
            library.extend(P.promote(spec,cat,r,library,maximum=6 if i==2 else 5))
            donors.append(dict(spec=spec,catalog=cat,result=r))
        discovery=dict(donors=donors,library=library,seconds=time.perf_counter()-began)
        save_stage('discovery',pins,discovery)
    library=discovery['library'];baselines={};initial=[];training_seconds=0.
    for j,spec in enumerate(ts):
        name='baseline-'+str(j);record=load_stage(name,pins)
        if record is None:
            started=time.perf_counter();cat,r=run(spec)
            record=dict(spec=spec,catalog=cat,result=r,seconds=time.perf_counter()-started)
            save_stage(name,pins,record)
        baselines[spec['id']]=A.reward(record['result']);initial.append(record);training_seconds+=record['seconds']
    weights=[0.]*len(A.FEATURES);episodes=[]
    for epoch in range(A.EPOCHS):
        indices=list(range(len(ts)));offset=epoch%len(indices);indices=indices[offset:]+indices[:offset]
        for j in indices:
            i=len(episodes);name='episode-'+str(i);e=load_stage(name,pins);spec=ts[j]
            if e is None:
                started=time.perf_counter();cat,r=run(spec,library,'policy',weights,True,17900+i)
                after,next_baseline,u=A.update(weights,baselines[spec['id']],r)
                e=dict(epoch=epoch,training_index=j,spec=spec,catalog=cat,result=r,weights_before=weights,
                    update=u,seconds=time.perf_counter()-started)
                save_stage(name,pins,e)
            if e['weights_before']!=weights or e['training_index']!=j:raise ValueError('checkpoint training order')
            weights=e['update']['weights_after'];baselines[spec['id']]=e['update']['baseline_after'];episodes.append(e);training_seconds+=e['seconds']
        print('epoch',epoch+1,'weights',weights,'sampled_actions',sum(len(e['result']['policy_events']) for e in episodes),flush=True)
    print('training complete; run resume_receptor_attention.py for fresh-process evaluation',flush=True)
SOURCES=tuple(dict.fromkeys((*SOURCES,'train_receptor_attention.py')))
if __name__=='__main__':main()
