"""Independently replay frozen-cohort membership and source byte identities."""
import hashlib,json,sys
from pathlib import Path
manifestp,targetp,out=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads(manifestp.read_text());target=json.loads(targetp.read_text())
assert sha(targetp)==manifest['targetHash']
loaded={}
for name,h in manifest['sourceHashes'].items():
    p=Path(name);assert sha(p)==h;loaded[p.name]=json.loads(p.read_text())
full={c['id']:c for c in loaded['coordinates.json']['configurations']}
provenance={c['id']:c for c in loaded['provenance.json']['configurations']}
dictionary=loaded['thermal-dictionary-e015.json']
support=next(v for v in loaded.values() if 'selectedAnchorCount' in v)
marking=next(v for v in loaded.values() if 'landmarks' in v)
ids=[c['id'] for c in target['configurations']]
assert len(ids)==len(set(ids))==20
assert ids==[r['id'] for r in manifest['targets']]
expected={r['id'] for r in provenance.values() if r['split']=='test' and r['sourceFrame'] in range(50,55)}
assert set(ids)==expected
dictionary_ids={r['id'] for r in dictionary['configurations']}
observed_ids={cid for a in support['anchors'] for cid,atom in a['observations']}
assert observed_ids<=set(support['trainingFrames'])
assert set(ids).isdisjoint(dictionary_ids|observed_ids|set(support['trainingFrames']))
assert set(ids).isdisjoint(p['configuration'] for p in support['poses'])
seen={provenance[cid]['geometrySha256'] for cid in dictionary_ids}
for c,metadata in zip(target['configurations'],manifest['targets'],strict=True):
    assert c==full[c['id']] and metadata==provenance[c['id']]
    assert metadata['geometrySha256'] not in seen
phase_counts={phase:sum(provenance[cid]['phase']==phase for cid in ids) for phase in ['Ih','II','VI','VIII']}
assert set(phase_counts.values())=={5}
report=dict(manifestHash=sha(manifestp),targetHash=sha(targetp),verifierHash=sha(Path(__file__)),
            targetIds=ids,phaseCounts=phase_counts,dictionaryFrameOverlap=0,supportObservationFrameOverlap=0,
            exactSourceGeometryDuplicatesToDictionary=0,
            unknownConditionFrames=sum(provenance[cid]['temperatureK'] is None or provenance[cid]['pressurePa'] is None for cid in ids),
            unknownTrajectoryFrames=sum(provenance[cid]['independentTrajectoryId'] is None for cid in ids),
            limits='Verifies source-index selection, unchanged coordinates/metadata, recorded dictionary/observation exclusion and frozen source bytes. Not independent trajectory or matched-condition admission; does not audit every earlier exploratory experiment or prove no distribution-level information leakage.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
