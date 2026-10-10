"""One fresh evaluation solve; no retained training/search trees in memory."""
import argparse
import gzip
import hashlib
import json
import resource
import time
from pathlib import Path
import receptor_attention_search as S
from receptor_attention_cases import registry
from run_receptor_attention import LEDGER,HEURISTIC,semantic
from run_adaptive_clusters import inventory
from run_resumable_clusters import decorate
import movable_proof_regions as M
from serialized_kernel import canonical

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',type=int,required=True)
    parser.add_argument('--lane',choices=('base','fixed','attention','zero','goal_heuristic'),required=True)
    parser.add_argument('--output',required=True);args=parser.parse_args()
    began=time.perf_counter();spec=registry()[2][args.case];library=[];weights=None
    if args.lane!='base':
        discovery=json.loads(gzip.decompress((LEDGER/'discovery.json.gz').read_bytes()))['data'];library=discovery['library']
    if args.lane in ('attention','zero','goal_heuristic'):
        weights=json.loads((LEDGER/'frozen-policy.json').read_text())['weights'] if args.lane=='attention' else list(HEURISTIC) if args.lane=='goal_heuristic' else [0.]*12
    setup=time.perf_counter()-began;start=time.perf_counter();cat=inventory(spec);grammar=time.perf_counter()-start
    model=M.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    r=S.search(model,library,'base' if args.lane=='base' else 'fixed' if args.lane=='fixed' else 'policy',weights,
        attempts=50000,seconds=60,proposal_limit=32)
    r['grammar_seconds']=grammar;decorate(spec,cat,r);r['worker_setup_seconds']=setup;r['total_seconds']=time.perf_counter()-began
    r['semantic_sha256']=hashlib.sha256(canonical(semantic(r))).hexdigest()
    out=dict(spec=spec,catalog=cat,result=r,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    target=Path(args.output);temporary=target.with_suffix('.partial')
    temporary.write_bytes(gzip.compress(canonical(out)+b'\n',mtime=0));temporary.replace(target)
    print(json.dumps({'case':spec['id'],'lane':args.lane,'status':r['status'],'attempts':r['metrics']['attempts'],'seconds':r['total_seconds']}),flush=True)
if __name__=='__main__':main()
