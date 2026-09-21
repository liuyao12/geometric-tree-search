#!/usr/bin/env python3
"""Matched complete-quotient checks with/without one checked pair exclusion.

The optional skip reports only choose what to attempt; they supply no clauses.
Pair clauses are admitted only after independent RUP certificate verification.
"""
import argparse,hashlib,json,time
from pathlib import Path
from solve_patch_period_quotients import certificate_templates,hnf,orientation_audit,propose_bases,solve_quotient

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser()
    for name in ['input','output','pair-certificate','checker']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--tile',required=True);p.add_argument('--skip-report',type=Path,action='append',default=[])
    p.add_argument('--time-ms',type=int,default=5000);p.add_argument('--max-vectors',type=int,default=96);p.add_argument('--max-bases',type=int,default=32)
    p.add_argument('--min-copies',type=int,default=14);p.add_argument('--max-copies',type=int,default=64);a=p.parse_args()
    if min(a.time_ms,a.max_vectors,a.max_bases,a.min_copies)<1 or a.max_copies<a.min_copies:p.error('Invalid bounds')
    started=time.perf_counter();raw=a.input.read_bytes();data=json.loads(raw);m=data['models'][a.tile]
    if m.get('allowReflections'):p.error('Proper rotations only')
    orientations=[o['voxels'] for o in m['orientations']];voxels=orientations[0];orientation_audit(voxels,orientations)
    proof_start=time.perf_counter();templates,proof=certificate_templates(a.pair_certificate,a.checker,orientations);proof_ms=(time.perf_counter()-proof_start)*1000
    proposals,stats=propose_bases([c['placements'] for c in data['cases'] if c['tile']==a.tile],len(voxels),a.max_vectors,a.min_copies,a.max_copies)
    skip=set();skip_sources=[]
    for path in a.skip_report:
        raw_skip=path.read_bytes();old=json.loads(raw_skip)
        if old['tile']!=a.tile:p.error('Skip report belongs to another tile')
        skip.update(hnf(row['basis']) for row in old['rows']);skip_sources.append({'sha256':sha(raw_skip),'path':str(path)})
    selected=[row for row in proposals if row['basis'] not in skip][:a.max_bases]
    source=Path(__file__).resolve();report={'tile':a.tile,'inputSha256':sha(raw),'sourceSha256':sha(source.read_bytes()),'solverSourceSha256':sha(source.with_name('solve_patch_period_quotients.py').read_bytes()),'bounds':{k:[str(x) for x in v] if isinstance(v,list) else str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},'proposalStats':stats,'skippedReports':skip_sources,'skippedProposals':sum(row['basis'] in skip for row in proposals),'proposals':selected,'pairConstraintProof':proof,'proofPreparationMs':proof_ms,'rows':[],'scope':'Complete quotient placement pools with alternating plain/proof-backed pair controls. No learned m-values. SAT scheduling is separate from the reference GCTS lane. Each UNSAT excludes one period lattice; limits and untested lattices remain unknown.'}
    def save():
        report['elapsedMs']=(time.perf_counter()-started)*1000;a.output.write_text(json.dumps(report,indent=2)+'\n')
    save()
    for index,proposal in enumerate(selected):
        row={'basis':proposal['basis'],'copies':proposal['copies'],'order':['plain','proved_pair'] if index%2==0 else ['proved_pair','plain']}
        for mode in row['order']:
            result=solve_quotient(voxels,orientations,proposal['basis'],a.time_ms,pair_exclusions=templates if mode=='proved_pair' else ())
            if mode=='proved_pair' and result['status']=='unsat_restricted_quotient':result['status']='unsat_period_lattice';result['proofBackedPairConstraints']=True
            row[mode]=result
        report['rows'].append(row);save()
        print(json.dumps({'index':index,'copies':row['copies'],**{mode:{'status':row[mode]['status'],'elapsedMs':row[mode]['stats']['elapsedMs']} for mode in row['order']}}),flush=True)
        if any(row[mode]['certificate'] for mode in row['order']):break

if __name__=='__main__':main()
