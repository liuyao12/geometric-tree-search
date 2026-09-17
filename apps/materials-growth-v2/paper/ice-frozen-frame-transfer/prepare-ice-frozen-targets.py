"""Freeze a source-index-selected transfer cohort before registration/search.

Frame exclusion is auditable; independent trajectories and matched conditions
are not established by this split. No success-dependent target selection.
"""
import hashlib,json,sys
from pathlib import Path
fullp,provp,dictp,supportp,markp,outdir=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
corpus,provenance,dictionary,support,mark=[json.loads(p.read_text()) for p in [fullp,provp,dictp,supportp,markp]]
assert mark['sourceHashes'][supportp.name]==sha(supportp)
by_id={c['id']:c for c in corpus['configurations']}
metadata=[r for r in provenance['configurations'] if r['split']=='test' and 50<=r['sourceFrame']<=54]
assert len(metadata)==20 and len({r['id'] for r in metadata})==20
for phase in ['Ih','II','VI','VIII']:
    assert sorted(r['sourceFrame'] for r in metadata if r['phase']==phase)==list(range(50,55))
ids={r['id'] for r in metadata}
dictionary_ids={c['id'] for c in dictionary['configurations']}
assert ids.isdisjoint(dictionary_ids)
seen_geometry={r['geometrySha256'] for r in provenance['configurations'] if r['id'] in dictionary_ids}
assert all(r['geometrySha256'] not in seen_geometry for r in metadata)
assert ids.isdisjoint(support['trainingFrames'])
assert ids.isdisjoint(p['configuration'] for p in support['poses'])
outdir.mkdir()
targetp=outdir/'heldout-coordinates.json'
with targetp.open('x') as f:json.dump(dict(configurations=[by_id[r['id']] for r in metadata]),f)
manifest=dict(scope=__doc__,selection='Source author validation frames 50–54, all four phases, fixed before proposal generation.',
              sourceHashes={str(p):sha(p) for p in [fullp,provp,dictp,supportp,markp]},
              codeHash=sha(Path(__file__)),targetHash=sha(targetp),targets=metadata,
              dictionaryFrames=len(dictionary['configurations']),supportTrainingFrames=len(support['trainingFrames']),
              disjointFromDictionaryFrames=True,disjointFromSupportTrainingAndPoses=True,
              noExactSourceGeometryDuplicatesToDictionary=True,
              limits='New frame IDs relative to the frozen dictionary/support pipeline, not independent trajectories, new phases, condition-matched validation or unseen source corpus. Target atom coordinates will be supplied to registration. Frozen learning artifacts are not modified.')
with (outdir/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
print(json.dumps(dict(targets=[r['id'] for r in metadata],targetHash=sha(targetp))))
