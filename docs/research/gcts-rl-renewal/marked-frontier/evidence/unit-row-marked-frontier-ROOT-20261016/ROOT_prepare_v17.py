"""Prior once-plan assembler adapted to current pins/reviews. Source-only."""
import ast,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
 p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
def save(n,x):
 p=HERE/n
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
 return pin(p)
def same_save(n,x):
 p=HERE/n
 if p.exists():assert read(p)==x;return pin(p)
 return save(n,x)
assert len(sys.argv)==4
mode=sys.argv[1]
purposes={'original-controls':'unit-row-advised-original-controls','domain-controls':'unit-row-advised-domain-controls','advice-controls':'unit-row-advised-advice-controls','canonical-search':'unit-row-advised-canonical-search','advised-search':'unit-row-advised-target-search'}
assert mode in purposes
config_path=HERE/'ROOT-current-review-pins-v1.json';assert pin(config_path)['sha256']==sys.argv[2]
config=read(config_path);h=read(check(config['handoff']));sources,inputs,cr=h['sources'],h['inputs'],h['source_contract'];contract=read(check(cr))
assert len(sources)==17 and len(inputs)==2 and contract['sources']==sources and contract['inputs']==inputs
for r in [*sources.values(),*inputs.values()]:check(r)
for r in sources.values():compile(ast.parse(Path(r['path']).read_bytes()),r['path'],'exec')
peer_path=check(config['caller_peer']);assert pin(peer_path)['sha256']==sys.argv[3];peer=read(peer_path)
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==cr
assert peer['scope']==contract['scope'] and peer['author_identity']=='/root' and peer['reviewer_identity']!='/root'
assert peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
limits=contract['limits'];assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
number=contract['phase_diagnostic_successor']['expected_consumer_cases']
author=dict(contract['Review_ABI']);author.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],authorship_disclosure='Root authored current caller17 only; distinct peer authored paired adviser/engine/semantics dependencies and discloses these roles; no self-review of those dependencies.',checks=[
 'Ten-edit full raw inverse to caller16; two dependency pins/own3IDs and three nested forwarding/target functions only. Optional ROW-default factory/scheduler keyword forwarding plus explicit same MARK policy in both target arms. All other raw/AST regions including native/failure55/fullproof/transport/response/output exact;14otherSources/input2/limits unchanged.',
 'Exact Source17/input2, six-rule original24 root target. Original20/512MiB/failure55/owned60/caller90+1. No target proof/route/donor/library input.',
 'Engine9 adds explicit owned marking-aware earliest-generation BRANCH tie with ROW default. Originalcontrols2 preserves17 ROW meanings and adds6 separately counted policy controls, total23. Retention17 and advice43 remain ROW. Adviser3/consumer3 and mathematical input unchanged; MARK policy is the declared target algorithm change.',
 'Outer batch/work schemas and control eight-kwarg API unchanged; all43 cases/checks preserved. Same report-only exact receipt reuse/genuine owned callback checkpoint and43checks. Current selective-multikey controls preserve all43 case meanings, complete current adviser/independent receipt/global BRANCH/TRY/owned rollback required. A retains first-ranked adoption11–13; B retains successful pending selection14–15; C owns selective remote rejection and forced retirement. No preinstalled future members or assumed eligibility. Existing caller15 four latest scalars/failure55 writer/native calling behavior unchanged; diagnostics remain unqualified.',
 'C control-only first structurally eligible wholebatch proposal, full whole/executed subset independent validation, separate A/B/C ownership and family lineage. Normalize only actual FORCED moves; preserve selective conflict plus legal survivor; actual bad-row BRANCH required before normal rejection/fallback/rollback. Essential gaps remain; adviser ranking and C case meanings unchanged.',
 'New23 policy controls must fully qualify alongside retention17/advice43 before MARK target searches. New policy is an explicit generation tie; ROW43 alone gives no MARK qualification. All cold setup/proposal/validation/search/retention/native output costs charged. No runtime qualification inherited, no hostile concurrent OS or full reference conformance claim.',
 'Any discovered complete word needs unchanged fresh membership/1717/full99b3/selected+t/m join INSIDE samecold20. UNKNOWN late data never proof/trajectory/speed authority.'
 ])
author_ref=same_save('ROOT-caller-author-Source-review-v1.json',author)
dep={}
for role,r in config['dependency_reviews'].items():
 v=read(check(r));assert v['source']==sources[role.removesuffix('_peer')] and v['source_review_passed'] is True and v['scientific_calls']==0
 if role.endswith('_peer'):assert v['reviewer_identity']!=v['author_identity']
 dep[role]=r
for role in ('engine','controls','adviser','advice_validator','advice_controls'):
 assert role in dep and role+'_peer' in dep
prior=read(BASE/'unit-row-retained-packed-ROOT-20261016/ROOT-original-controls-authorization-v1.json')
for role in ('transition','transition_peer','retained_controls','retained_controls_peer','fallback'):
 r=prior['dependency_reviews'][role];v=read(check(r));assert v['source']==sources[role.removesuffix('_peer')] and v['source_review_passed'] is True;dep[role]=r
runtime=pin(Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'))
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
if mode in ('canonical-search','advised-search'):
 for prefix,n in [('original-controls',23),('domain-controls',17),('advice-controls',number)]:
  c=read(HERE/('ROOT-'+prefix+'-disposition-v1.json'))
  assert c['controls_accepted'] is True and c['native_resources_qualified'] is True and c['passed_cases']==n and c['skipped_cases']==0
  assert read(check(c['plan']))['sources']==sources
  if prefix=='advice-controls':assert c['all_advice_consumer_gates_qualified'] is True and c['additional_coverage_gaps']==[]
protocol=save('ROOT-'+mode+'-protocol-choice-v1.json',{'schema':'ROOT-advised-domain-protocol-choice-v1','previous_goal_turn':'progress','current_goal_turn':'progress','endpoint':mode,'sources':sources,'inputs':inputs,'limits':limits,'scientific_execution':False,'expected_cases':number if mode=='advice-controls' else 23 if mode=='original-controls' else 17 if mode=='domain-controls' else None,'separate_control_actuals':True,'target_search_unsplit':True,'encoded_output_cap_bytes':4194304,'expanded_output_cap_bytes':16777216,'material_change':'Engine9 and originalcontrols2 add a named MARK generation tie and six genuine/abstract policy controls while retaining original17 ROW meanings. Three caller adapters forward policy with ROW default for controls; both target arms explicitly MARK. Current23/17/43 and native/wire gates required. Target/declaration/profile/grammar/native20/512/failure55/owned60/caller90+1 unchanged. No proofword/route/donor/library, fit prediction, inherited runtime qualification or adviser/consumer policy change.','original_search':'Original right-two target/axioms/emptyGamma/parameters24roots0/all-six bounded inventory; initial_stateNone, no word/donor/library/route input.','work_bounds':{'maximum_nodes':128,'maximum_events':2000},'scope':'Retained unit-row specialization: ROW control suites plus separately qualified MARK generation tie; no full graph conformance/RL/GCTS-specific advantage.','costs':'All cold authentication/setup, adviser/validator, snapshots/search/retention, positive fullword/point/state checking, output/nativeexit/postprobe charged.','search_failure_diagnostics':'Actual returned raw data only under original failure55, unqualified UNKNOWN, no late proof/trajectory/resource authority.'})
owned=HERE/(mode+'-owned-v1');external=HERE/(mode+'-external-v1');assert not owned.exists() and not external.exists()
common={'invocation_id':'unit-row-marked-frontier-'+mode+'-20261016-v17','purpose':purposes[mode],'output_directory':str(owned),'sources':sources,'inputs':inputs,'source_contract':cr,'reviews':{'ROOT':author_ref,'peer':pin(peer_path)},'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=save('ROOT-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-unit-row-global-engine-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,dependency_reviews=dep))
plan=save('ROOT-'+mode+'-plan-v1.json',dict(common,schema='ROOT-unit-row-global-engine-plan-v1',ROOT_authorization=grant))
save('ROOT-'+mode+'-preflight-v1.json',{'schema':'ROOT-advised-engine-preflight-v1','plan':plan,'scientific_calls':0,'fresh_owned_and_external_outputs':True,'Source17_inputs2_verified':True})
print(json.dumps({'plan':plan,'external_directory':str(external)}))
