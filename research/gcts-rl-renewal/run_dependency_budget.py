"""Checkpointed, matched cold comparison; no supplied proof or marking table."""
import gc
import gzip
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from dependency_budget_worker import HERE,SOURCES,sha
from dependency_budget_cases import registry
from serialized_kernel import canonical

ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
LEDGER=ROOT/'.gcts-active/dependency-budget-20261010';DEST=DOC/'dependency-budget-001'
LANES=('base','budget')


def read(path,pins):
    record=json.loads(gzip.decompress(path.read_bytes()))
    if record['sources']!=pins:raise ValueError('completed checkpoint source binding')
    return record


def reference(path):
    DEST.mkdir(parents=True,exist_ok=True);target=DEST/path.name;target.write_bytes(path.read_bytes())
    return dict(path='dependency-budget-001/'+path.name,sha256=sha(target),bytes=target.stat().st_size)


def worker(index,lane,repetition,pins):
    path=LEDGER/('case-'+str(index)+'-'+lane+'-'+str(repetition)+'.json.gz')
    if not path.exists():
        subprocess.run([sys.executable,str(HERE/'dependency_budget_worker.py'),'--case',str(index),
                        '--lane',lane,'--output',str(path)],check=True)
    return path,read(path,pins)


def main():
    LEDGER.mkdir(parents=True,exist_ok=True);pins={n:sha(HERE/n) for n in SOURCES}
    refs=[];elapsed=0.
    for i,spec in enumerate(registry()):
        case_path=LEDGER/('case-'+str(i)+'.json.gz')
        if case_path.exists():
            record=read(case_path,pins)
        else:
            began=time.perf_counter();timings={k:[] for k in LANES};primary={};digests={};cert=None
            for repetition in range(4):
                order=LANES if (i+repetition)%2==0 else tuple(reversed(LANES))
                for lane in order:
                    path,part=worker(i,lane,repetition,pins);r=part['result'];digest=r['semantic_sha256']
                    if lane not in primary:primary[lane]=reference(path);digests[lane]=digest
                    elif digests[lane]!=digest:raise ValueError('cold repeated search changed semantics')
                    if lane=='budget' and cert is None:cert=part['certificate']
                    timings[lane].append(dict(repetition=repetition,order=order,seconds=r['total_seconds'],
                        search_seconds=r['seconds'],preparation_seconds=r['preparation_seconds'],
                        synthesis_seconds=r['synthesis_seconds'],certification_seconds=r['certification_seconds'],
                        positive_check_seconds=r['positive_check_seconds'],peak_process_rss_bytes=part['peak_process_rss_bytes'],
                        semantic_sha256=digest,status=r['status'],attempts=r['metrics'].get('attempts',0)))
                    del part,r;gc.collect()
            path,part=worker(i,'saturation',0,pins);control=part['result'];del part
            summary={lane:dict(samples=values,median_seconds=statistics.median(v['seconds'] for v in values),
                min_seconds=min(v['seconds'] for v in values),max_seconds=max(v['seconds'] for v in values)) for lane,values in timings.items()}
            record=dict(spec=spec,certificate=cert,run_files=primary,timings=summary,controls=dict(saturation=control),
                        sources=pins,seconds=time.perf_counter()-began)
            case_path.write_bytes(gzip.compress(canonical(record)+b'\n',mtime=0))
        elapsed+=record['seconds'];refs.append(reference(case_path))
        print(spec['id'],'necessary',record['certificate']['required'][record['certificate']['target']],
              {lane:(record['timings'][lane]['samples'][0]['status'],record['timings'][lane]['samples'][0]['attempts'],
                     round(1000*record['timings'][lane]['median_seconds'],3)) for lane in LANES},flush=True)
    out=dict(version='dependency-budget-001',sources=pins,case_files=refs,lanes=LANES,
             limits=dict(attempts=50000,seconds=60),repetitions=4,seconds=elapsed,
             scope='Cold synthesis of a certified redundant distant binary marking layer over the original finite grammar, hypotheses and bound. Complete point domains, global dead/forced/generation scheduling, exact rollback and original candidates remain. No empirical label, supplied proof, learned rule table, new axiom, RL update, unrestricted FOL completeness or infinite tiling claim.',
             timing_scope='Four independent fresh-process solves per lane and goal, balanced in both execution positions. Solve clocks include input construction, grammar, synthesis, independent certificate validation, model, search and positive proof verification. Module import/startup, trace serialization, parent loading and separate audit are outside solve clocks; completed case-stage clocks include startup/serialization/loading. Saturation is one separately labeled cold observation and uses its own finite-closure schedule.')
    (DOC/'dependency-budget-001.json').write_bytes(canonical(out)+b'\n');print('complete',len(refs),elapsed,flush=True)


if __name__=='__main__':main()
