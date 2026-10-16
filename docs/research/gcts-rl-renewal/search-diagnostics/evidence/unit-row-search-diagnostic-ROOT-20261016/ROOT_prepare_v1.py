"""Raw Source/AST/review/plan metadata only; no project or scientific calls."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def pin(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def check(r):
    p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
def save(name,value):
    p=HERE/name
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
def same_save(name,value):
    p=HERE/name
    if p.exists():assert read(p)==value;return pin(p)
    return save(name,value)

assert len(sys.argv)==4
mode,peer_name,peer_sha=sys.argv[1:];assert mode in ('controls','search')
hpath=BASE/'unit-row-search-failure-diagnostic-cold-source-20261015/handoff-v1.json'
assert pin(hpath)['sha256']=='703899c10e849d48efe369ea8929dea7a7d81b22de3697b785ba62fc4b3f164e'
h=read(hpath);sources,inputs,cr=h['sources'],h['inputs'],h['source_contract']
assert sources['intake']['sha256']=='0b6c980f2310cac5788876e6837b9213305482bb838dfca47f63f8ae34771db4'
assert sources['intake']['bytes']==34766 and cr['sha256']=='427f618ae2f2748e7e5c994a6815d721172b8c97ca9b9b12848216109122622b'
contract=read(check(cr));assert contract['sources']==sources and contract['inputs']==inputs
old=read(BASE/'unit-row-global-engine-ROOT-20261015/ROOT-controls-plan-v1.json')
assert set(sources)==set(old['sources']) and inputs==old['inputs']
for k,r in sources.items():
    check(r)
    if k!='intake':assert r==old['sources'][k]
for r in inputs.values():check(r)
raw=check(sources['intake']).read_bytes();parent=check(old['sources']['intake']).read_bytes()
tree=ast.parse(raw);oldtree=ast.parse(parent)
compile(tree,sources['intake']['path'],'exec')
helpers=contract['provenance']['unchanged15_helpers'];assert len(helpers)==15
defs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
olddefs={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for name in helpers:
    assert ast.dump(defs[name],include_attributes=False)==ast.dump(olddefs[name],include_attributes=False)
    assert ast.get_source_segment(raw.decode(),defs[name])==ast.get_source_segment(parent.decode(),olddefs[name])
marker=b"    result_raw = canonical({'schema':'ROOT-unit-row-global-engine-result-v1',"
assert raw[raw.index(marker):]==parent[parent.index(marker):]
limits=contract['limits'];assert limits==old['limits']
assert len(sources)==9 and len(inputs)==2
peer_path=Path(peer_name);assert pin(peer_path)['sha256']==peer_sha
peer=read(peer_path)
assert peer['scope']==contract['scope'] and peer['source']==sources['intake'] and peer['sources']==sources
assert peer['source_contract']==cr and peer['author_identity']=='/root/hilbert_advice_controls'
assert peer['reviewer_identity'] not in ('/root','/root/hilbert_advice_controls')
assert peer['source_only'] is True and peer['source_review_passed'] is True
assert peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
review=dict(contract['Review_ABI']);review.update(source_contract=cr,reviewer_identity='/root',source_only=True,
 source_review_passed=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],
 authorship_disclosure='Root did not author the diagnostic caller; Root authored its parent caller and this integration metadata. Distinct whole-caller peer review is separately required.',
 checks=[
  'Whole34,766B code and15,073B contract read. All15 helpers raw+AST and complete positive tail exact to parent; Source8/input2 and original20/55/60/90+1/512MiB limits unchanged.',
  'Capture only actual engine.search returned value before unchanged invoke postboundary. No postfailure scientific callback, state query, reconstruction, re-enumeration or new epoch.',
  'Failure-only55 path uses captured native/resource/file/escape endpoints, exact builtin bounded serializer, chronological prefix stop, exclusive output2/completion hash. No positive responsewire or success receipt on this branch.',
  'Original exception re-raised and top-level exit2 retained regardless diagnostic success. No late proof/graph/trajectory/resource/restore acceptance from raw producer metadata.',
  'Original authority isolation and known reviewed synchronous Source scope unchanged; no per-method/yield hostile-process custody assurance.',
  'ALL24-REBIND and general EOF coverage gaps unchanged. Search actual remains same original target and complete bounded inventory, no word/donor/library.'
 ])
root_review=same_save('ROOT-caller-Source-review-v1.json',review)
runtime=check(old['runtime']);assert pin(runtime)['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
oldgrant=read(check(old['ROOT_authorization']))
dependency_reviews=oldgrant['dependency_reviews']
for k,r in dependency_reviews.items():
    v=read(check(r));assert v['source']==sources[k] and v['source_review_passed'] is True
if mode=='search':
    c=read(HERE/'ROOT-controls-disposition-v1.json')
    assert c['controls_accepted'] is True and c['native_resources_qualified'] is True
    assert c['passed_cases']==17 and c['skipped_cases']==0
    assert read(check(c['plan']))['sources']==sources
protocol=save('ROOT-'+mode+'-protocol-choice-v1.json',{
 'schema':'ROOT-unit-row-search-diagnostic-protocol-choice-v1','previous_goal_turn':'progress','current_goal_turn':'progress',
 'endpoint':mode,'sources':sources,'inputs':inputs,'limits':limits,'scientific_execution_occurred':False,
 'material_change':'Same engine/profile/universe; new caller saves only actual returned raw engine data on search failure. Not an unchanged restart.',
 'expected_controls':{'total':17,'passed':17,'skipped':0},
 'original_search':'Same right-two target, original axioms/emptyGamma/parameters/24unit obligations, all-six bounded inventory, initial_stateNone; no route/word/donor/library.',
 'search_work_bounds':{'maximum_nodes':128,'maximum_events':2000},
 'diagnostic_semantics':'Unqualified raw producer observations only under original failure55, exit2. Old UNKNOWN remains unchanged. No accepted trace/counters/restore/proof/resource success after20s.',
 'conformance_gaps':['ALL24-REBIND does not retain unaffected domains.','No general independently completed all-six EOF/exhaustion cover.','Specialized fixed unit rows only.'],
 'strong_acceptance_claimed':False,'retained_domain_successor_used':False})
owned=HERE/(mode+'-owned-v1');external=HERE/(mode+'-external-v1')
assert not owned.exists() and not external.exists()
common={'invocation_id':'unit-row-search-diagnostic-'+mode+'-20261016-v1','purpose':'unit-row-global-engine-'+mode,
 'output_directory':str(owned),'sources':sources,'inputs':inputs,'source_contract':cr,
 'reviews':{'ROOT':root_review,'peer':pin(peer_path)},'runtime':pin(runtime),'limits':limits,'resource_rule':old['resource_rule']}
grant=save('ROOT-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-unit-row-global-engine-authorization-v1',
 author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,dependency_reviews=dependency_reviews))
plan=save('ROOT-'+mode+'-plan-v1.json',dict(common,schema='ROOT-unit-row-global-engine-plan-v1',ROOT_authorization=grant))
save('ROOT-'+mode+'-preflight-v1.json',{'schema':'ROOT-search-diagnostic-preflight-v1','plan':plan,'scientific_calls':0,
 'fresh_outputs':True,'helper15_raw_AST_equal':True,'positive_tail_raw_equal':True,'source8_input2_limits_unchanged':True})
print(json.dumps({'plan':plan,'external_directory':str(external)}))
