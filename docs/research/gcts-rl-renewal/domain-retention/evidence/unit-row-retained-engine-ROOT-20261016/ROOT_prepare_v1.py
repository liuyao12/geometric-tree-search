"""Raw Source/review/protocol/once-plan metadata only; no scientific calls."""
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
mode,peer_name,peer_sha=sys.argv[1:]
purposes={'original-controls':'unit-row-retained-original-controls','domain-controls':'unit-row-retained-domain-controls','search':'unit-row-retained-target-search'}
assert mode in purposes
hpath=BASE/'unit-row-retained-cold-ROOT-source-20261016/handoff-v1.json'
assert pin(hpath)['sha256']=='0840a8d1b7c669b809e04a46276e166dd8fc83e48dc84f28411428b8591848c7'
h=read(hpath);sources,inputs,cr=h['sources'],h['inputs'],h['source_contract'];contract=read(check(cr))
assert len(sources)==11 and len(inputs)==2 and contract['sources']==sources and contract['inputs']==inputs
assert sources['intake']['sha256']=='264211f1415b5908f765a14630722e5456cf520327d73ebf5b7f1323df47c352'
assert cr['sha256']=='c528edb0337cf6e8e34ab02969bfb7ae9212d120289ab80c997939658ab7ce84'
for r in [*sources.values(),*inputs.values()]:check(r)
for r in sources.values():compile(ast.parse(Path(r['path']).read_bytes()),r['path'],'exec')
peer_path=Path(peer_name);assert pin(peer_path)['sha256']==peer_sha;peer=read(peer_path)
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==cr
assert peer['scope']==contract['scope'] and peer['author_identity']=='/root' and peer['reviewer_identity']!='/root'
assert peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
limits=contract['limits'];assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
author=dict(contract['Review_ABI']);author.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],authorship_disclosure='Root authored this caller; this is AUTHOR review, genuine whole-caller peer is separate.',checks=[
 'Complete reviewed diagnostic parent plus authored exact current integration; all15 original helpers, whole bounded failure-only writer and positive output/native exit tail byte/AST unchanged.',
 'Exact11Source roles and original input2. Only engine replaced, transition+retained_controls added. Each of two control sets and fresh original-root search has distinct purpose; no target splitting or shared run cache.',
 'Current retained engine receives authenticated transition module. Fresh private original language for each raw proposer/cursor/certifier and new transition/refresh call, plus private per-engine independent semantics. Two-state transition authority freshly captured and original c354 retained.',
 'Existing surrounding Source/function/native guard covers all11Source modules; original native tick precedes control tick. No per-method/yield or hostile concurrent-process custody guarantee.',
 'Source/default anchors, exact review/once grant consumption, original20/512MiB/failure55/owned60/caller90+1 and4MiB output unchanged. All strong acceptance false; Root separately closes outputs/native evidence.',
 'Original17 versus retained17 expected result schema correctly dispatched. Search initial_stateNone/max128nodes/2000events, no supplied proof/donor/library/rank/RL. Existing bounded failure-only returned capture not late proof/trajectory/resource authority.'
 ])
author_ref=same_save('ROOT-caller-author-Source-review-v1.json',author)
dep={}
reviews=BASE/'unit-row-retained-domain-ROOT-review-20261016'
for role,name in [('engine','ROOT-engine-Source-review-v1.json'),('transition','ROOT-transition_checker-Source-review-v1.json'),('retained_controls','ROOT-controls-Source-review-v1.json')]:
    r=pin(reviews/name);v=read(check(r));assert v['source']==sources[role] and v['source_review_passed'] is True;dep[role]=r
oldplan=read(BASE/'unit-row-global-engine-ROOT-20261015/ROOT-controls-plan-v1.json');oldgrant=read(check(oldplan['ROOT_authorization']))
for role in ('fallback','controls'):
    r=oldgrant['dependency_reviews'][role];v=read(check(r));assert v['source']==sources[role] and v['source_review_passed'] is True;dep[role]=r
for folder,name,role in [
 ('unit-row-retained-domain-controls-peer-source-20261015','engine-typed-Source-review-v1.json','engine'),
 ('unit-row-retained-domain-controls-peer-source-20261015','transition_checker-typed-Source-review-v1.json','transition'),
 ('unit-row-retained-controls-independent-source-20261015','typed-Source-review-v2.json','retained_controls')]:
    r=pin(BASE/folder/name);v=read(check(r));assert v['source']==sources[role] and v['source_review_passed'] is True and v['reviewer_identity']!='/root';dep[role+'_peer']=r
runtime=pin(Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'))
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
if mode=='search':
    for prefix in ('original-controls','domain-controls'):
        c=read(HERE/('ROOT-'+prefix+'-disposition-v1.json'))
        assert c['controls_accepted'] is True and c['native_resources_qualified'] is True and c['passed_cases']==17 and c['skipped_cases']==0
        assert read(check(c['plan']))['sources']==sources
protocol=save('ROOT-'+mode+'-protocol-choice-v1.json',{'schema':'ROOT-retained-domain-protocol-choice-v1','previous_goal_turn':'progress','current_goal_turn':'progress','endpoint':mode,'sources':sources,'inputs':inputs,'limits':limits,'scientific_execution':False,
 'expected_cases':17 if mode!='search' else None,'separate_control_actuals':True,'target_search_unsplit':True,'unchanged_output_cap_bytes':4194304,
 'original_search':'Same original right-two target, axioms, emptyGamma, parameters,24root points and all-six bounded inventory; fresh initial_stateNone, no word/donor/library/route input.',
 'work_bounds':{'maximum_nodes':128,'maximum_events':2000},'scope':'Current retained-support engine, original scheduler ROW-TIE; no full reference conformance or learned/RL/advantage claim.',
 'costs':'All cold setup/authentication, state validation, whole support/ledger comparison, retained packet refresh/archive/prefix replay, generation and checking, snapshots/trace/output/native exit/probe charged.',
 'search_failure_diagnostics':'Unqualified actual returned raw data only under original failure55, never a positive20 result; old UNKNOWNs unchanged.'})
owned=HERE/(mode+'-owned-v1');external=HERE/(mode+'-external-v1');assert not owned.exists() and not external.exists()
common={'invocation_id':'unit-row-retained-'+mode+'-20261016-v1','purpose':purposes[mode],'output_directory':str(owned),'sources':sources,'inputs':inputs,'source_contract':cr,'reviews':{'ROOT':author_ref,'peer':pin(peer_path)},'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=save('ROOT-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-unit-row-global-engine-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,dependency_reviews=dep))
plan=save('ROOT-'+mode+'-plan-v1.json',dict(common,schema='ROOT-unit-row-global-engine-plan-v1',ROOT_authorization=grant))
save('ROOT-'+mode+'-preflight-v1.json',{'schema':'ROOT-retained-engine-preflight-v1','plan':plan,'scientific_calls':0,'fresh_owned_and_external_outputs':True,'Source11_inputs2_verified':True})
print(json.dumps({'plan':plan,'external_directory':str(external)}))
