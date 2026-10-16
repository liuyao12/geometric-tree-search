"""Saved display/manifest extension only; no Source, point or proof replay."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
DEST=BASE.parent/'docs/research/gcts-rl-renewal/shared-bounded-proofs'
POINT=BASE/'shared-bounded-point-board-ROOT-20261015'
def read(path):return json.loads(path.read_bytes())
def pin(path):
    raw=path.read_bytes();return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
manifest=read(DEST/'evidence-manifest.json');copies={x['public_path']:x for x in manifest['files']}
def copy(path,relative):
    target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True);raw=path.read_bytes()
    if target.exists():assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    item={'source_path':str(path),'public_path':relative,**pin(path)}
    if relative in copies:assert copies[relative]==item
    copies[relative]=item
disposition_path=POINT/'ROOT-point-board-disposition-v1.json'
assert pin(disposition_path)['sha256']=='db5f969908c6caca0e4d6cebce234e5b7d851980e8fa5aca0fc1b0e1b5fff1d4'
d=read(disposition_path)
assert d['positive_point_board_accepted'] is True and d['native_resources_qualified'] is True and d['packet_controls_rejected']==14
for ref in d['outputs']:assert pin(Path(ref['path']))=={k:ref[k] for k in ('sha256','bytes')}
board=read(POINT/'point-owned-v1/point-board.json');controls=read(POINT/'point-owned-v1/controls.json')
for folder,label in [
 ('shared-bounded-ordinary-saved-record-review-20261015','ordinary-saved-peer'),
 ('shared-bounded-point-board-cold-source-20261015','point-cold-source'),
 ('shared-bounded-point-board-cold-independent-source-20261015','point-cold-peer'),
 ('shared-bounded-point-board-ROOT-20261015','point-ROOT'),
 ('unit-row-two-witness-feasibility-source-20261015','next-degree-design')]:
    for path in sorted((BASE/folder).iterdir()):
        if path.is_file() and path.suffix in ('.json','.py','.patch'):copy(path,'evidence/'+label+'/'+path.name)
for kind in ('owned','external'):
    for path in sorted((POINT/('point-%s-v1'%kind)).iterdir()):
        assert path.is_file();copy(path,'evidence/point-stage/'+kind+'/'+path.name)
copy(Path(__file__),'evidence/ROOT/'+Path(__file__).name)
data_path=DEST/'report-data.json';archive=DEST/'report-data-before-point-v1.json'
if not archive.exists():archive.write_bytes(data_path.read_bytes())
data=read(data_path)
data['board']={'packet':board['packet'],'receipt':board['independent_point_receipt'],'disposition':d,'controls':controls}
data['lead']='Generic interleaved ordinary search discovers the original right-two addition theorem. Fresh membership and independent logical checks accept every primitive. A separate stage verifies its complete translated point board and rejects all malformed-packet controls.'
data['assessment']='The theorem is discovered automatically within the declared bounded six-rule language, and its complete translated point board is now independently checked. This removes the previous encoding obstruction and supplies a successful conventional baseline. GCTS search, learned receptor families and RL did not run in this discovery or board-verification stage, so no benefit from them is established.'
data['evidence'].extend([
 {'label':'Independent saved-word metadata concordance: all96 checks','href':'evidence/ordinary-saved-peer/findings-v1.json'},
 {'label':'Separate complete positive point-board/resource disposition','href':'evidence/point-ROOT/ROOT-point-board-disposition-v1.json'},
 {'label':'Complete24-row point packet and independent union receipt','href':'evidence/point-stage/owned/point-board.json'},
 {'label':'Fresh original17 and padded24 membership/logical checks','href':'evidence/point-stage/owned/word-checks.json'},
 {'label':'All14 malformed-packet control outcomes','href':'evidence/point-stage/owned/controls.json'},
 {'label':'Complete point-stage two-line wire','href':'evidence/point-stage/owned/response.jsonl'},
 {'label':'Point-stage true native terminal measurement','href':'evidence/point-stage/external/native-terminal.json'},
 {'label':'Independent whole point-stage intake Source review','href':'evidence/point-cold-peer/typed-Source-review-v1.json'},
 {'label':'Next-step two-witness degree design and its forced-row gap','href':'evidence/next-degree-design/feasibility-v1.json'}
])
data['positive_point_board_accepted']=True
save(data_path,data);manifest['files']=[copies[k] for k in sorted(copies)];save(DEST/'evidence-manifest.json',manifest)
print(json.dumps({'evidence_files':len(copies),'evidence_bytes':sum(x['bytes'] for x in copies.values()),'physical_rows':d['physical_rows'],'marking_points':d['marking_point_count'],'marking_occurrences':d['marking_occurrence_count']}))
