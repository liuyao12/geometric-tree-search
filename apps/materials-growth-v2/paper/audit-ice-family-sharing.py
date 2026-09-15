"""Audit observed cross-phase sharing; never treat phase labels as search inputs.

Counts use existing learned base identities, not a new isometry classifier.
Exact serialized cloud equality is storage equality, not tolerance equivalence.
"""
import hashlib
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


def audit(library, provenance):
    meta = {r['id']: r for r in provenance['configurations']}
    observed = defaultdict(set)
    phase_frames = defaultdict(set)
    phase_bases = defaultdict(set)
    phase_motifs = defaultdict(set)
    counts = defaultdict(int)
    for registration in library['trainingRegistrations']:
        cid = registration['id']
        assert meta[cid]['split'] == 'train', 'Non-training frame in library'
        phase = meta[cid]['phase']
        phase_frames[phase].add(cid)
        for placement in registration['selected']:
            motif_id = placement['motif']
            base = library['motifs'][motif_id]['base']
            phase_bases[phase].add(base)
            phase_motifs[phase].add(motif_id)
            observed[base].add(phase)
            counts[phase] += 1
    rows = []
    for base, phases in sorted(observed.items()):
        variants = [m for m in library['motifs'] if m['base'] == base]
        endpoints = [set() for _ in range(2)]
        pairs = set()
        for motif in variants:
            keys = tuple(json.dumps(c, sort_keys=True, separators=(',', ':')) for c in motif['cloudM'])
            assert len(keys) == 2
            for side in range(2):
                endpoints[side].add(keys[side])
            pairs.add(keys)
        product = len(endpoints[0]) * len(endpoints[1])
        rows.append(dict(base=base, phases=sorted(phases), coupledVariants=len(variants),
                         exactStoredEndpointValues=list(map(len, endpoints)),
                         exactStoredPairs=len(pairs), exactCartesianPairs=product,
                         unobservedExactCartesianPairs=product-len(pairs)))
    return dict(scope=__doc__, phases=[dict(phase=p, trainingFrames=len(phase_frames[p]),
                bases=len(phase_bases[p]), decoratedMotifs=len(phase_motifs[p]),
                placementObservations=counts[p]) for p in sorted(phase_frames)],
        pairwise=[dict(phases=[a,b], sharedBases=len(phase_bases[a]&phase_bases[b]),
                       sharedDecoratedMotifs=len(phase_motifs[a]&phase_motifs[b]))
                  for a,b in combinations(sorted(phase_frames),2)],
        baseSharingHistogram={str(n):sum(len(p)==n for p in observed.values()) for n in range(1,len(phase_frames)+1)},
        bases=rows,
        summary=dict(bases=len(rows), exactObservedPairs=sum(r['exactStoredPairs'] for r in rows),
                     exactCartesianPairs=sum(r['exactCartesianPairs'] for r in rows),
                     unobservedExactCartesianPairs=sum(r['unobservedExactCartesianPairs'] for r in rows)),
        limits='Descriptive training audit only. Unobserved is not forbidden; exact storage inequality is not geometric incompatibility. Phase labels are post-hoc metadata. Conditions and independent trajectories are not verified. No search or transfer success is established.')


if __name__ == '__main__':
    library_path, provenance_path, output = map(Path, sys.argv[1:])
    report = audit(json.loads(library_path.read_text()), json.loads(provenance_path.read_text()))
    report['sourceHashes'] = {key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in
                             [('library',library_path),('provenance',provenance_path),('code',Path(__file__))]}
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='bases'}, indent=2))
