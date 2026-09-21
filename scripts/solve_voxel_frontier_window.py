#!/usr/bin/env python3
"""Finite unmarked point window with viable outer frontier; SAT research control.

Uses the pair oracle's retained solver but declares its different target. No
pair exclusions or learned marking may influence these extension checks.
"""
import argparse,hashlib,json
from pathlib import Path
from solve_voxel_pair_corona import solve_window

def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--time-ms',type=int,default=10000);p.add_argument('--max-rounds',type=int,default=1000);p.add_argument('--frontier-batch',type=int,default=4);p.add_argument('--resume');p.add_argument('--phase-hint');p.add_argument('--amo',choices=['pairwise','sequential'],default='pairwise');p.add_argument('--solver',choices=['glucose3','cadical195'],default='glucose3');a=p.parse_args()
    data=json.loads(Path(a.input).read_text());sha=digest(data);prior=json.loads(Path(a.resume).read_text()) if a.resume else None
    if prior and (prior.get('problemSha256')!=sha or prior.get('stats',{}).get('problem')!='point-window' or prior.get('stats',{}).get('frontier')!='occupancy'):p.error('Resume belongs to another problem')
    hint_raw=Path(a.phase_hint).read_bytes() if a.phase_hint else None;hints=json.loads(hint_raw)['placements'] if hint_raw else None
    result=solve_window(data,a.time_ms,a.max_rounds,a.frontier_batch,prior.get('frontierPoints') if prior else None,amo=a.amo,backend=a.solver,phase_hints=hints);result['problemSha256']=sha
    if hint_raw:result['phaseHintSha256']=hashlib.sha256(hint_raw).hexdigest()
    result['stats']['cumulativeMs']=result['stats']['elapsedMs']+(prior['stats'].get('cumulativeMs',prior['stats']['elapsedMs']) if prior else 0)
    root=Path(__file__).resolve().parent
    result['sources']={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['solve_voxel_frontier_window.py','solve_voxel_pair_corona.py','certify_voxel_obstruction.py']}
    Path(a.output).write_text(json.dumps(result));print(json.dumps({k:v for k,v in result.items() if k not in ('placements','frontierPoints','nogoods')}),flush=True)
if __name__=='__main__':main()
