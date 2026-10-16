"""Saved small-record display/copy only; no kernel, checker, model or search calls."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PROJECT=BASE.parent
DEST=PROJECT/'docs/research/gcts-rl-renewal/shared-bounded-proofs'
def read(path):return json.loads(path.read_bytes())
def pin(path):
    raw=path.read_bytes()
    return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
copies=[]
def copy(path,relative):
    target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True)
    raw=path.read_bytes()
    if target.exists():assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    copies.append({'source_path':str(path),'public_path':relative,**pin(path)})

attempts=[]
for index,name in [(1,'Phase-batched producer'),(2,'Interleaved producer with generic goal closures')]:
    disposition=read(ROOT/('ROOT-ordinary-disposition-v%d.json'%index))
    assert disposition['native_resources_qualified'] is True
    for ref in disposition['outputs']:
        assert pin(Path(ref['path']))=={k:ref[k] for k in ('sha256','bytes')}
    proposal=read(ROOT/('ordinary-owned-v%d/search-result.json'%index))
    attempts.append({'name':name,'disposition':disposition,'proposal':proposal})
assert attempts[0]['disposition']['target_proof_accepted'] is False
assert attempts[1]['disposition']['target_proof_accepted'] is True
commands=attempts[1]['proposal']['candidate']['commands']
assert len(commands)==17

for folder,label in [
 ('shared-bounded-language-ROOT-20261015','policy'),
 ('shared-bounded-language-policy-independent-review-source-20261015','policy-peer'),
 ('shared-bounded-language-implementation-source-20261015','language-source'),
 ('shared-bounded-language-independent-source-20261015','language-peer'),
 ('shared-bounded-ordinary-cold-source-20261015','intake-source'),
 ('shared-bounded-ordinary-cold-independent-source-20261015','intake-peer'),
 ('shared-bounded-ordinary-saved-diagnosis-20261015','first-run-diagnosis'),
 ('shared-bounded-point-board-source-20261015','point-converter-source'),
 ('shared-bounded-point-board-independent-source-20261015','point-checker-source'),
 ('shared-bounded-point-board-correspondence-source-20261015','correspondence')]:
    for path in sorted((BASE/folder).iterdir()):
        if path.is_file() and path.suffix in ('.json','.py','.patch'):
            copy(path,'evidence/'+label+'/'+path.name)
for path in sorted(ROOT.iterdir()):
    if path.is_file() and path.suffix in ('.json','.py'):
        copy(path,'evidence/ROOT/'+path.name)
for index in (1,2):
    for kind in ('owned','external'):
        for path in sorted((ROOT/('ordinary-%s-v%d'%(kind,index))).iterdir()):
            assert path.is_file()
            copy(path,'evidence/attempt-%d/%s/%s'%(index,kind,path.name))
sources=read(ROOT/'ROOT-plan-v2.json')['sources']
for role in ('kernel','checker','clean_support'):
    ref=sources[role];path=Path(ref['path'])
    assert pin(path)=={k:ref[k] for k in ('sha256','bytes')}
    copy(path,'evidence/shared-Source/'+role+'.py')
for path,label in [
 (BASE/'arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py','native_meter.py'),
 (BASE/'arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py','external_once.py'),
 (BASE/'arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json','original-declaration.json')]:
    copy(path,'evidence/shared-Source/'+label)

data={
 'schema':'saved-shared-bounded-proof-reader-data-v1',
 'title':'A seventeen-command arithmetic proof, found automatically',
 'lead':'Generic interleaved ordinary search discovers the original right-two addition theorem. Every primitive passes fresh bounded-language membership and the unchanged independent logical checker. The first phase-batched attempt remains unknown.',
 'summary':[
   {'label':'Discovered proof','tex':'17\\text{ primitive commands}','detail':'Original axioms and target; no supplied proof word or library.'},
   {'label':'Complete successful search/check','tex':'0.810736\\,\\mathrm{s}','detail':'Native launch through fresh postterminal observation.'},
   {'label':'Peak owned memory','tex':'28\\,\\mathrm{MiB}','detail':'One owned process; true terminal peak. Earlier attempt charged separately.'}],
 'result_intro':'Both actual attempts use the same original logical input, selected bounded language, six heuristic work limits and cold resource gates. The successor changes inference scheduling and adds generic syntax-only goal watchers; any firing still requires actual known premises and expands the original rules.',
 'attempts':attempts,
 'comparison_notes':[
   'The first attempt stops at its fact cap without a candidate. The successful successor retains fewer facts and returns a complete checked word. This is one observed algorithm comparison, without a statistical claim or attribution to interleaving alone: generic goal closures changed too.',
   'Aggregate counters do not measure per-phase timing or prove a starvation cause. The Source-level scheduling motivation is a hypothesis. The retained term-only quiescence omission means a newly cached term need not receive another wave; no complete processing or language-exhaustion claim follows.',
   'The successful search received no previous word, donor proof or family library. Every selected instantiation, atomic context and ordered reference comes from its generic heuristics. The ordinary search is an incomplete proof-search control, not GCTS or RL.'
 ],
 'proof':{'commands':commands,'word_check_href':'evidence/attempt-2/owned/word-check.json'},
 'board':None,
 'assessment':'This is concrete automatic theorem discovery within the declared bounded six-rule language. It removes the previous encoding obstruction and supplies a successful conventional baseline. The present proof does not demonstrate a contribution from GCTS markings, learned receptor families or RL; those mechanisms did not run in this search.',
 'evidence':[
   {'label':'Complete file manifest and original raw hashes','href':'evidence-manifest.json'},
   {'label':'First actual: unknown result and resource disposition','href':'evidence/ROOT/ROOT-ordinary-disposition-v1.json'},
   {'label':'Successful actual: independently checked word and resource disposition','href':'evidence/ROOT/ROOT-ordinary-disposition-v2.json'},
   {'label':'All seventeen symbolic commands and search counters','href':'evidence/attempt-2/owned/search-result.json'},
   {'label':'Fresh membership and independent logical receipts','href':'evidence/attempt-2/owned/word-check.json'},
   {'label':'Successful complete two-line wire','href':'evidence/attempt-2/owned/response.jsonl'},
   {'label':'True native terminal/reaping measurement','href':'evidence/attempt-2/external/native-terminal.json'},
   {'label':'Fresh postterminal measurement','href':'evidence/attempt-2/external/observation.json'},
   {'label':'Selected bounded-language policy','href':'evidence/policy/ROOT-profile-choice-v2.json'},
   {'label':'Independent whole producer review and heuristic advisory','href':'evidence/language-peer/findings-v3.json'},
   {'label':'Preserved incompatible runner-contract review','href':'evidence/intake-peer/typed-Source-review-v2.json'},
   {'label':'Corrected current runner review','href':'evidence/intake-peer/typed-Source-review-v3.json'},
   {'label':'Conditional word/point-board correspondence argument','href':'evidence/correspondence/correspondence-v1.json'},
   {'label':'Independently authored point-board checker Source','href':'evidence/point-checker-source/independent_word_point_board_checker_v1.py'},
   {'label':'Root Source review of that separate point checker','href':'evidence/point-converter-source/ROOT-point-checker-Source-review-v1.json'}
 ],
 'display_scope':'Saved small records only; no Source execution or logical/point/model replay during report assembly.',
 'GCTS_advantage_claimed':False,'RL_accepted':False,'broad_goal_complete':False
}
save(DEST/'report-data.json',data)
save(DEST/'evidence-manifest.json',{'schema':'shared-bounded-proof-reader-evidence-manifest-v1','files':copies,
 'scope':'Complete exact copies of selected task-owned small Source/metadata/actual artifacts; this manifest is not a semantic replay.'})
print(json.dumps({'reader':str(DEST/'reader.html'),'evidence_files':len(copies),'evidence_bytes':sum(x['bytes'] for x in copies),'proof_rows':len(commands),'point_board_accepted':False}))
