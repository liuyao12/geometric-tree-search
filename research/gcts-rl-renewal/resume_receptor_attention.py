"""Stream saved training and freeze fresh-process evaluation artifacts.

Evaluation has the same fifty-thousand-attempt limit in all lanes and a sixty
second wall limit. Training keeps its original ten-second limit and returns.
No evaluation result changes weights, features, inventory or training records.
"""
import gc
import gzip
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from run_receptor_attention import HERE,DOC,LEDGER,LANES,HEURISTIC,sha
from receptor_attention_cases import registry
from run_resumable_clusters import control
from serialized_kernel import canonical

DEST=DOC/'receptor-attention-001'
def stage(path,pins):
    value=json.loads(gzip.decompress(path.read_bytes()))
    if value['sources']!=pins:raise ValueError('saved source pins')
    return value['data']
def reference(path,pins=None):
    DEST.mkdir(parents=True,exist_ok=True);target=DEST/path.name
    target.write_bytes(path.read_bytes());r=dict(path='receptor-attention-001/'+path.name,sha256=sha(target),bytes=target.stat().st_size)
    if pins is not None:r['sources']=pins
    return r
def main():
    discovery_path=LEDGER/'discovery.json.gz';saved=json.loads(gzip.decompress(discovery_path.read_bytes()));pins=saved['sources'];discovery=saved['data']
    for name,pin in pins.items():
        if sha(HERE/name)!=pin:raise ValueError('measured source changed: '+name)
    ds,ts,es=registry();donor_seconds=discovery['seconds'];del saved,discovery;gc.collect()
    baseline_files=[];episode_files=[];training_seconds=0.;weights=[0.]*12;baselines={};counts={};observed_draws=0
    for i,spec in enumerate(ts):
        p=LEDGER/('baseline-'+str(i)+'.json.gz');b=stage(p,pins);r=b['result']
        from receptor_attention import reward
        baselines[spec['id']]=reward(r);training_seconds+=b['seconds'];baseline_files.append(reference(p,pins));del b,r;gc.collect()
    for i in range(48):
        p=LEDGER/('episode-'+str(i)+'.json.gz');e=stage(p,pins)
        if e['weights_before']!=weights:raise ValueError('saved training weights')
        weights=e['update']['weights_after'];baselines[e['spec']['id']]=e['update']['baseline_after'];training_seconds+=e['seconds']
        counts[e['result']['status']]=counts.get(e['result']['status'],0)+1;observed_draws+=len(e['result']['policy_events'])
        episode_files.append(reference(p,pins));del e;gc.collect()
    frozen=dict(weights=weights,sources=pins,training_seconds=training_seconds,observed_draws=observed_draws,episode_statuses=counts)
    policy_path=LEDGER/'frozen-policy.json';policy_path.write_bytes(canonical(frozen)+b'\n')
    recovery_pins={n:sha(HERE/n) for n in ('resume_receptor_attention.py','receptor_attention_worker.py','receptor_attention_artifact.py')}
    case_files=[];evaluation_seconds=0.
    for i,spec in enumerate(es):
        case_path=LEDGER/('isolated-case-'+str(i)+'.json.gz')
        if case_path.exists():
            c=json.loads(gzip.decompress(case_path.read_bytes()))
            if c['recovery_sources']!=recovery_pins or c['policy_pin']!=sha(policy_path):raise ValueError('evaluation recovery binding')
        else:
            start=time.perf_counter();timings={k:[] for k in LANES};primary={};pins_by_lane={};statuses={}
            for repetition in range(5):
                offset=(i+repetition)%5;order=LANES[offset:]+LANES[:offset]
                for lane in order:
                    output=LEDGER/('isolated-'+str(i)+'-'+lane+'-'+str(repetition)+'.json.gz')
                    if not output.exists():
                        subprocess.run([sys.executable,str(HERE/'receptor_attention_worker.py'),'--case',str(i),'--lane',lane,'--output',str(output)],check=True)
                    part=json.loads(gzip.decompress(output.read_bytes()));r=part['result'];pin=r['semantic_sha256']
                    if lane not in primary:primary[lane]=reference(output);pins_by_lane[lane]=pin
                    elif pin!=pins_by_lane[lane]:raise ValueError('isolated cold repeat semantics: '+spec['id']+' '+lane)
                    statuses[lane]=r['status']
                    timings[lane].append(dict(repetition=repetition,order=order,seconds=r['total_seconds'],search_seconds=r['seconds'],grammar_seconds=r['grammar_seconds'],
                        positive_check_seconds=r.get('positive_check_seconds',0),attention_prep_seconds=r['attention_prep_seconds'],worker_setup_seconds=r['worker_setup_seconds'],
                        index_build_seconds=r['index']['build_seconds'] if r['index'] else 0,proposal_seconds=r['metrics'].get('proposal_seconds',0),semantic_sha256=pin))
                    del part,r;gc.collect()
            summaries={lane:dict(samples=v,median_seconds=statistics.median(x['seconds'] for x in v),min_seconds=min(x['seconds'] for x in v),max_seconds=max(x['seconds'] for x in v)) for lane,v in timings.items()}
            c=dict(spec=spec,run_files=primary,timings=summaries,controls={k:control(spec,k) for k in ('chronological','saturation')},seconds=time.perf_counter()-start,
                recovery_sources=recovery_pins,policy_pin=sha(policy_path),outcomes=statuses)
            case_path.write_bytes(gzip.compress(canonical(c)+b'\n',mtime=0))
        evaluation_seconds+=c['seconds'];case_files.append(reference(case_path));print('case complete',spec['id'],{k:round(1000*t['median_seconds'],2) for k,t in c['timings'].items()},flush=True)
    out=dict(version='receptor-attention-001',sources=pins,recovery_sources=recovery_pins,discovery_file=reference(discovery_path,pins),donor_seconds=donor_seconds,
        training=dict(specs=ts,baseline_files=baseline_files,episode_files=episode_files,initial_weights=[0.]*12,weights=weights,baselines=baselines,
            features=('family','cells','concludes_target','goal_gain','last_goal','internal_fraction','hypothesis_fraction','compactness','level','progress_family','guard_fraction','defer'),epochs=8,rate=2.,seconds=training_seconds,episode_statuses=counts,observed_draws=observed_draws),
        case_files=case_files,heuristic_weights=HEURISTIC,lanes=LANES,evaluation_seconds=evaluation_seconds,seconds=donor_seconds+training_seconds+evaluation_seconds,
        budgets=dict(training=dict(attempts=50000,seconds=10),evaluation=dict(attempts=50000,seconds=60)),
        timing_scope='Five independent fresh-process evaluation solves per lane/goal, all five positions balanced. Recorded solve cost includes input/library setup, grammar, model, relaxed support, joins, attention, search and positive checks. Python startup and raw trace serialization are separate; recorded case-stage clocks include them. Training retains all prior primary traces in its original producer; evaluation workers retain none. Failed initial evaluation, checkpoint loading and audit are excluded from completed-stage sums.',
        scope='Sampled, zero-initialized branch-local softmax over exact validated cluster proposals and defer, with shared relational distant-premise and relaxed backward-goal features. Full point graph, scheduler, exact original markings and fallback remain. No supplied proof, theorem-specific learned parameter, learned pruning, new native universal tile execution or general FOL completeness.')
    (DOC/'receptor-attention-001.json').write_bytes(canonical(out)+b'\n');print('complete manifest',len(case_files),out['seconds'],flush=True)
if __name__=='__main__':main()
