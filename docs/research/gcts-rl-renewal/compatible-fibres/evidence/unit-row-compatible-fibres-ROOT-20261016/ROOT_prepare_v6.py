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
number=contract['compatible_source_fibres_successor']['expected_consumer_cases']
author=dict(contract['Review_ABI']);author.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],authorship_disclosure='Root authored current caller only; distinct peer authored independent paired consumer and discloses this dependency.',checks=[
 'Exact seven-literal inverse to measuredcea5 parent; all17 tophelpers/every nestedfunction/adviserdefaults/proofchecks/response-nativeexit suffix preserved. Four component pins plus own IDs/schema only.',
 'Exact Source17/input2, six-rule original24 root target. Original20/512MiB/failure55/owned60/caller90+1. No target proof/route/donor/library input.',
 'Adviser3 generic matching pair/source fibre FIFO avoids proposal-turn loss to incompatible reads. Existing five-part interface score independently recomputed by consumer3 unchanged. Engine8 three version literals only, methods exact to4afe.',
 'Outer batch/work schemas and control eight-kwarg API unchanged; prior30 definitions and forty labels/checks preserved with new genuine component coverage; declared43 cases. New local control gaps/SKIPs remain explicit and block target admission.',
 'All cold setup/proposal/validation/search/retention/native output costs charged. No runtime qualification inherited, no hostile concurrent OS or full reference conformance claim.',
 'Any discovered complete word needs unchanged fresh membership/1717/full99b3/selected+t/m join INSIDE samecold20. UNKNOWN late data never proof/trajectory/speed authority.'
 ])
author_ref=same_save('ROOT-caller-author-Source-review-v1.json',author)
dep={}
for role,r in config['dependency_reviews'].items():
 v=read(check(r));assert v['source']==sources[role.removesuffix('_peer')] and v['source_review_passed'] is True and v['scientific_calls']==0
 if role.endswith('_peer'):assert v['reviewer_identity']!=v['author_identity']
 dep[role]=r
for role in ('engine','adviser','advice_validator','advice_controls'):
 assert role in dep and role+'_peer' in dep
prior=read(BASE/'unit-row-retained-packed-ROOT-20261016/ROOT-original-controls-authorization-v1.json')
for role in ('transition','transition_peer','retained_controls','retained_controls_peer','fallback','controls'):
 r=prior['dependency_reviews'][role];v=read(check(r));assert v['source']==sources[role.removesuffix('_peer')] and v['source_review_passed'] is True;dep[role]=r
runtime=pin(Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'))
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
if mode in ('canonical-search','advised-search'):
 for prefix,n in [('original-controls',17),('domain-controls',17),('advice-controls',number)]:
  c=read(HERE/('ROOT-'+prefix+'-disposition-v1.json'))
  assert c['controls_accepted'] is True and c['native_resources_qualified'] is True and c['passed_cases']==n and c['skipped_cases']==0
  assert read(check(c['plan']))['sources']==sources
  if prefix=='advice-controls':assert c['all_advice_consumer_gates_qualified'] is True and c['additional_coverage_gaps']==[]
protocol=save('ROOT-'+mode+'-protocol-choice-v1.json',{'schema':'ROOT-advised-domain-protocol-choice-v1','previous_goal_turn':'progress','current_goal_turn':'progress','endpoint':mode,'sources':sources,'inputs':inputs,'limits':limits,'scientific_execution':False,'expected_cases':number if mode=='advice-controls' else 17 if mode.endswith('controls') else None,'separate_control_actuals':True,'target_search_unsplit':True,'encoded_output_cap_bytes':4194304,'expanded_output_cap_bytes':16777216,'material_change':'Generic compatible-source UI fibres, independent unchanged score and new genuine component reopening/three source eligibility controls; no grammar/limit/fallback/engine-method changes. All historical results preserved, no fit prediction.','original_search':'Original right-two target/axioms/emptyGamma/parameters24roots0/all-six bounded inventory; initial_stateNone, no word/donor/library/route input.','work_bounds':{'maximum_nodes':128,'maximum_events':2000},'scope':'Retained-support unit-row ROW-TIE specialization; no full graph conformance/RL/GCTS-specific advantage.','costs':'All cold authentication/setup, adviser/validator, snapshots/search/retention, positive fullword/point/state checking, output/nativeexit/postprobe charged.','search_failure_diagnostics':'Actual returned raw data only under original failure55, unqualified UNKNOWN, no late proof/trajectory/resource authority.'})
owned=HERE/(mode+'-owned-v1');external=HERE/(mode+'-external-v1');assert not owned.exists() and not external.exists()
common={'invocation_id':'unit-row-compatible-fibres-'+mode+'-20261016-v6','purpose':purposes[mode],'output_directory':str(owned),'sources':sources,'inputs':inputs,'source_contract':cr,'reviews':{'ROOT':author_ref,'peer':pin(peer_path)},'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=save('ROOT-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-unit-row-global-engine-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,dependency_reviews=dep))
plan=save('ROOT-'+mode+'-plan-v1.json',dict(common,schema='ROOT-unit-row-global-engine-plan-v1',ROOT_authorization=grant))
save('ROOT-'+mode+'-preflight-v1.json',{'schema':'ROOT-advised-engine-preflight-v1','plan':plan,'scientific_calls':0,'fresh_owned_and_external_outputs':True,'Source17_inputs2_verified':True})
print(json.dumps({'plan':plan,'external_directory':str(external)}))
