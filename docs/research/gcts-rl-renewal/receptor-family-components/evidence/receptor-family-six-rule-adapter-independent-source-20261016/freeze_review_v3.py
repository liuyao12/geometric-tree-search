"""Independent review metadata, raw/AST only; no model/helper evaluation."""
import ast,hashlib,json
from pathlib import Path
R=Path.cwd();A=R/'.gcts-active/receptor-family-six-rule-adapter-source-20261016';D=R/'.gcts-active/receptor-family-six-rule-adapter-independent-source-20261016'
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,d):
 p=D/n;p.open('xb').write((json.dumps(d,indent=2,sort_keys=True)+'\n').encode());return pin(p)
cp=A/'Source-contract-v3.json';c=json.loads(cp.read_bytes());hp=A/'handoff-v3.json';h=json.loads(hp.read_bytes())
assert pin(cp)['sha256']=='1d56488b42aa5c19ffed1e58a86dc647062a14d79580c9c13e2e3ba08d3d209d'
assert pin(hp)['sha256']=='133d10af302668dd020c60daac8df2504f58fc5dd9e4466d5ecf6e4187071886'
source=c['source'];assert pin(source['path'])==source and c['sources']==h['sources']==c['Review_ABI']['sources']=={'adapter':source}
assert c['source']==h['source'] and h['source_contract']==pin(cp)
refs={str(source['path']):source,str(cp):pin(cp),str(hp):pin(hp)}
def verify(x):
 if type(x)is dict:
  if set(x)=={'path','sha256','bytes'}:
   actual=pin(x['path']);assert actual==x;refs[x['path']]=x
  else:
   for v in x.values():verify(v)
 elif type(x)is list:
  for v in x:verify(v)
# Authenticate current capsule dependencies/metadata, not every historical data/source member.
for field in ('source','sources','dependency_sources','source_delta_chain','author_static','common_wire','operative_wire_clarifications','producer_contract','producer_handoff','preserved_issues','preserved_v2_genuine_negative','baseline_component_contract'):verify(c[field])
base=json.loads(Path(c['baseline_component_contract']['path']).read_bytes())
for k in ('original_model_sources','original_model_inputs','original_model_binding'):assert c[k]==base[k]
assert len(c['original_model_sources'])==17 and len(c['original_model_inputs'])==2
st=json.loads((D/'independent-static-v3.json').read_bytes());verify(st['source']);verify(st['raw_refs']);assert st['actual_all_four_patch_directions_exact']
verify(pin(D/'source-negative-v2.json'));verify(pin(D/'independent-static-v3.json'))
tree=ast.parse(Path(source['path']).read_bytes());funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
for name in ('describe_host','adapt_expansion'):
 assert [x.arg for x in funcs[name].args.kwonlyargs]==c['API'][name]['kwargs'] and not funcs[name].args.args
checks=[
 ('WHOLE_CURRENT_SOURCE','All v3 module constants/functions read; dependency point/member paths traced. No Source execution.'),
 ('WHOLE_CURRENT_CONTRACT_HANDOFF','Full v3 contract/handoff and exact Review_ABI/current adapter-only map checked; no fabricated v2 contract.'),
 ('CURRENT_RAW_PINS','Current adapter, 8 dependency Sources and selected metadata caps raw hashed; original model maps equal fresh13 ancestor.'),
 ('TWO_COMPLETE_RAW_INVERSES','Independent4-edit1→2 and6-edit2→3 raw forward/inverse, whole AST inverses exact.'),
 ('FOUR_ACTUAL_PATCH_DIRECTIONS','Applied real unified patch bytes in both directions for both transitions; no author-only boolean trust.'),
 ('SEVEN_HELPERS_UNCHANGED','require/tree/canonical/digest/describe_host/rows/_key raw and AST exact across1/2/3; only adapt_expansion changed.'),
 ('KEYWORD_API','Both public keyword-only signatures exactly match current contract.'),
 ('NO_SCIENTIFIC_LOADING','Only hashlib/json imports; no loader/exec/eval/file/clock/engine import or entrypoint.'),
 ('ORIGINAL_HOST_AUTHORITY','describe_host preserves original17/input2 epoch and derives full binding/theory/Gamma/finite names; caller raw authentication retained.'),
 ('NO_LEGACY_BLOCK_DIALECT','Exact six-rule argument/ordered arity table matches original membership/kernel; richer block/tautology/refl/induction unavailable.'),
 ('FRESH_INDEPENDENT_CHECK','Calls current independent check_expansion fresh; full request/family checked; no offered receipt or producer helper authority.'),
 ('GENUINE_GAMMA_NODES','Hypotheses are actual assumption primitive nodes; native indexed original Gamma check, no artificial earlier premise row or changed Gamma.'),
 ('ACTUAL_ROW_COMPLETENESS','Unique literal int0..23 assignments for every node/input; every consumed ordered reference strictly earlier.'),
 ('ALL_ORDERED_PREMISES','Repeated ordered reads preserved, actual premise formulas/offsets reconstructed into original full preimage.'),
 ('MEMBERSHIP_REBUILD','Each ground witness calls original language.primitive, c354 rebuild and marked independent tile rebuild; literal base projection equality.'),
 ('POINT_KEY_FIX','Uses base_semantics.text for native decorated selected/excluded identity, rather than ASCII metadata serialization.'),
 ('FULL_COLLISION_LEDGERS','marked check_collision includes original and decorated preimages across current selected/excluded and all new members; unequal preimages never merged by hash.'),
 ('FULL_COMPATIBLE_UNION','Whole t support capacity and every base/extra marking agree; full hypothetical state independently rebuilt and9fd6 checked.'),
 ('EXACT_OVERLAP_DEDUP','Shared placement only exact native full key and entire packet, selected reuse no duplicate contribution; ordered edge uses remain counted.'),
 ('ROOT_PHYSICAL_SHARING','Actual original source metadata/occupancy/formula and root DISTINCT/ALLOW policies checked against physical rows.'),
 ('NESTED_PHYSICAL_SHARING','Every checked call frame resolves to actual node/input rows and enforces its descriptor DISTINCT/ALLOW policy before READY. Closes negative NESTED-PHYSICAL-SOURCE-DISTINCT-1.'),
 ('FULL_SOURCE_INSPECTION','Each frame input exposes final original/decorated full physical keys or null plus unresolved flag; no hash-only alias authority.'),
 ('UNUSED_INTERFACE_FIX','All final root external inputs including unused ones and outputs checked against any assigned literal marks; unresolved ports remain explicit/no invented m facts.'),
 ('NO_MUTATION_OR_COUNTER_RESET','Deep copied hypothetical union only, full request/original authority equality at return, monotone kernel visits; no visit reset/native language constructor.'),
 ('ERROR_UNKNOWN_SCOPE','No adapter exception handlers; all native/checker/tick errors propagate. Fresh checker UNKNOWN returns no partial members/union/physical bindings.'),
 ('HONEST_ACCEPTANCE_SCOPE','Only local_member_membership_checked/local_point_union_checked narrow booleans; proof/degree/EOF/engine/scheduler/trajectory/pruning/RL/resource/runtime flags false.'),
 ('NO_QUALIFICATION_INHERITANCE','Fresh13 baseline pins authenticate dependencies only; no actual, grammar, old8/12 or original17 result promoted to this new composition.'),
]
findings={'schema':'receptor-family-six-rule-adapter-independent-findings-v3','source':source,'source_contract':pin(cp),'checks':[{'id':k,'status':'SOURCE_CHECK_CLOSED','finding':v} for k,v in checks],'check_count':len(checks),'raw_refs':list(refs.values()),'independent_static':pin(D/'independent-static-v3.json'),'preserved_negative':pin(D/'source-negative-v2.json'),'blockers':[],'closed_findings':[{'id':'NESTED-PHYSICAL-SOURCE-DISTINCT-1','closed_by':source,'scope':'Author-discovered before metadata, independently confirmed Source2 negative; v3 per-call physical enforcement.'}],'nonblocking_limits':['Generic checker/producer remain syntax-only and are not self-reviewed here. Their independent whole current Source reviews remain separate.','Caller must authenticate fresh original model and current modules and guard the complete transaction; adapter version strings alone are not arbitrary object authentication.','Full assumption positive is unavailable with actual empty Gamma; do not fabricate Gamma to fill coverage.','No current-state candidate graph, degree/EOF, scheduler, exact live rollback or engine-advice activation is provided. Pending interfaces are obligations, never accepted facts.','Future Root cold native20 qualification must cover the new current composition; no runtime fit or mathematical theorem follows from this Source pass.'],'author_overlap':'/root/arithmetic_induction authored generic producer/design and historical c354/kernel/engine/caller dependencies. Did not author current host adapter; this review is scoped to that adapter and its integration seams, not a self-review of producer/engine.','source_only':True,'scientific_calls':0,'source_functions_executed':0,'helper_execution':False,'models_constructed':0,'tests_run':0,'clocks_called':0,'compile_without_evaluation':True,'runtime_qualified':False}
fp=put('findings-v3.json',findings)
review={'schema':c['Review_ABI']['schema'],'scope':c['Review_ABI']['scope'],'source':source,'source_contract':pin(cp),'sources':c['sources'],'status':'CONDITIONAL_SOURCE_PASS','scientific_calls':0,'author_overlap':findings['author_overlap'],'findings':fp,'blockers':[],'closed_findings':['NESTED-PHYSICAL-SOURCE-DISTINCT-1'],'preserved_negative':pin(D/'source-negative-v2.json'),'check_count':len(checks),'raw_reference_count':len(refs),'native_or_model_execution':False,'tests_run':0,'clocks_called':0,'runtime_qualified':False,'proof_accepted':False,'point_union_runtime_accepted':False,'engine_activated':False,'conditions':findings['nonblocking_limits']}
for key in c['Review_ABI']['required']:assert key in review
rp=put('typed-Source-review-v3.json',review)
hp=put('handoff-v3.json',{'schema':'receptor-family-six-rule-adapter-independent-handoff-v3','review':rp,'findings':fp,'independent_static':pin(D/'independent-static-v3.json'),'preserved_negative':pin(D/'source-negative-v2.json'),'source':source,'source_contract':pin(cp),'status':'CONDITIONAL_SOURCE_PASS','scientific_calls':0,'runtime_qualified':False,'next':'Root own review and any separately granted native component actual; reviewer executes no Source.'})
print(json.dumps({'review':rp,'findings':fp,'handoff':hp,'checks':len(checks),'refs':len(refs)},indent=2))
