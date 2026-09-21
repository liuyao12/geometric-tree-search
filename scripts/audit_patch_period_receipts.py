#!/usr/bin/env python3
"""Replay proposal/pool bookkeeping, not the historical timed UNSAT searches."""
import hashlib,json
from collections import Counter
from pathlib import Path
from solve_patch_period_quotients import hnf,propose_bases,quotient_pool
root=Path(__file__).resolve().parents[1]
def raw(name):return (root/name).read_bytes()
def read(name):return json.loads(raw(name))
def sha(b):return hashlib.sha256(b).hexdigest()
w=read('data/3d-viable-frontier-witnesses-2026-09-21.json');m=w['models']['p10-346304'];orientations=[o['voxels'] for o in m['orientations']];voxels=orientations[0]
pilot=read('data/3d-p10-period-pilot-2026-09-21.json');filtered=read('data/3d-p10-period-pair-pilot-2026-09-21.json');expanded=read('data/3d-p10-period-controls-2026-09-21.json')
old={**w,'cases':w['cases'][:8]};old_sha=sha((json.dumps(old,indent=2,ensure_ascii=False)+'\n').encode())
assert pilot['inputSha256']==filtered['inputSha256']==old_sha
assert expanded['inputSha256']==sha(raw('data/3d-viable-frontier-witnesses-2026-09-21.json'))
assert expanded['sourceSha256']==sha(raw('scripts/benchmark_patch_period_quotients.py'))
assert expanded['solverSourceSha256']==sha(raw('scripts/solve_patch_period_quotients.py'))
assert expanded['pairConstraintProof']['manifestSha256']==sha(raw('data/p10-346304-pair-obstruction/manifest.json'))
assert expanded['pairConstraintProof']['verifierSha256']==sha(raw('scripts/verify_voxel_pair_certificate.py'))
assert expanded['skippedReports'][0]['sha256']==sha(raw('data/3d-p10-period-pilot-2026-09-21.json'))
def proposals(source,bounds):
 return propose_bases([c['placements'] for c in source['cases'] if c['tile']=='p10-346304'],len(voxels),bounds['max_vectors'],bounds['min_copies'],bounds['max_copies'])
for r in [pilot,filtered]:
 ps,stats=proposals(old,r['bounds']);assert json.loads(json.dumps(ps))==r['proposals'] and stats==r['proposalStats']
 assert [p['basis'] for p in r['proposals'][:24]]==[x['basis'] for x in r['rows']]
assert pilot['proposals']==filtered['proposals']
skip={hnf(row['basis']) for row in pilot['rows']};ps,stats=proposals(w,expanded['bounds'])
selected=[p for p in ps if p['basis'] not in skip][:expanded['bounds']['max_bases']]
assert json.loads(json.dumps(selected))==expanded['proposals'] and stats==expanded['proposalStats']
assert sum(p['basis'] in skip for p in ps)==expanded['skippedProposals']
assert [p['basis'] for p in expanded['proposals']]==[r['basis'] for r in expanded['rows']]
assert not skip.intersection(hnf(row['basis']) for row in expanded['rows'])
for index,row in enumerate(expanded['rows']):assert row['order']==(['plain','proved_pair'] if index%2==0 else ['proved_pair','plain'])
rows=pilot['rows']+filtered['rows']+[r[mode] for r in expanded['rows'] for mode in ['plain','proved_pair']]
pools={}
for r in rows:
 basis=hnf(r['basis'])
 if basis not in pools:pools[basis]=quotient_pool(voxels,orientations,basis)
 _,pool,_=pools[basis]
 assert len(pool)==r['stats']['candidatePlacements'] and len(pool)==8*r['stats']['quotientSites']
 # The early pilot's occupancy deduplication did not change any p10 pool.
 assert len({p['sites'] for p in pool})==len(pool)
 assert r['copies']*10==r['stats']['quotientSites']
 assert r['status'] in ['unsat_period_lattice','unknown'] and r['certificate'] is None
print(json.dumps({'verifiedBookkeeping':True,'distinctPeriodLattices':len(pools),'calls':len(rows),'pilotPlain':dict(Counter(r['status'] for r in pilot['rows'])),'pilotProvedPair':dict(Counter(r['status'] for r in filtered['rows'])),'expandedPlain':dict(Counter(r['plain']['status'] for r in expanded['rows'])),'expandedProvedPair':dict(Counter(r['proved_pair']['status'] for r in expanded['rows'])),'scope':'Proposal identities, source receipts and complete pool sizes replayed. Does not independently prove historical period UNSAT results or aperiodicity.'}))
