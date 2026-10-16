"""Adapted prior once-plan preparation: raw Source/JSON/AST only, no scientific calls."""
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
assert len(sys.argv)==3
mode=sys.argv[1]
purposes={'original-controls':'unit-row-advised-original-controls','domain-controls':'unit-row-advised-domain-controls','advice-controls':'unit-row-advised-advice-controls','canonical-search':'unit-row-advised-canonical-search','advised-search':'unit-row-advised-target-search'}
assert mode in purposes
hpath=BASE/'unit-row-advice-family-retirement-cold-ROOT-source-20261016/handoff-v4.json'
assert pin(hpath)['sha256']=='adf5f454a8cb8827357e736db7e3082ea9c404b3f63dac38c0e8dbe097eb2855'
h=read(hpath);sources,inputs,cr=h['sources'],h['inputs'],h['source_contract'];contract=read(check(cr))
assert len(sources)==17 and len(inputs)==2 and contract['sources']==sources and contract['inputs']==inputs
assert sources['intake']['sha256']=='5b88a8c096e8e55bad143c313749594d58631117584d4c9d34cf74c1a9dfcb95'
assert cr['sha256']=='439d2d6dcb3b6ae3d20a8247709b3d1c04ab27ab26a640c3c9cabe1fd0b5e59e'
for r in [*sources.values(),*inputs.values()]:check(r)
for r in sources.values():compile(ast.parse(Path(r['path']).read_bytes()),r['path'],'exec')
peer_path=BASE/'unit-row-advice-family-retirement-cold-independent-source-20261016/typed-Source-review-v1.json'
assert pin(peer_path)['sha256']==sys.argv[2]
peer=read(peer_path)
assert peer['source']==sources['intake'] and peer['sources']==sources and peer['source_contract']==cr
assert peer['scope']==contract['scope'] and peer['author_identity']=='/root' and peer['reviewer_identity']!='/root'
assert peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
limits=contract['limits'];assert limits=={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
author=dict(contract['Review_ABI']);author.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],authorship_disclosure='Root authored current caller only; author review distinct from genuine current peer.',checks=[
 'Whole reviewed9852 parent plus exactfiveedit inverse/current contract:17tophelpers/every nestedfunction/adviserdefaults/positivechecks/output-nativeexit raw exact; only engine0b45/control183a pins/ownIDs/schema changed.',
 'ExactSource17/input2/current contract; original20/512MiB/failure55/owned60/caller90+1. Separate old17/retention17/new30 stages; no qualification inherited.',
 'Unchanged CodeSeal/nativefirst callback boundaries with fresh private original semantics. New observing wrappers allowed only declared actual-record/phase data, no Source rewrite/fake universe/EOF or hostile-thread guarantee.',
 'Engine6 abandons pure advisory family after definite independent rejection, maxone freshbatch sameBRANCH. Whole base fallback/scheduler/retention/rollback unchanged; originalc6fc manualpolicy/f668 validators retained. No qualitychange.',
 'Any found word still needs original fresh membership/1717fullword/99b3fullpoint and canonicalpacket/state selected+t/m join INSIDE samecold20. No supplied target proof/route.',
 'Current30 control gates and old17/retention17 all currentSource noSKIP/nogap required before targets. Explicit control seams and newREADYreplacement coverage limit remain; no fullconformance/RL/advantage claim.'
 ])
author_ref=same_save('ROOT-caller-author-Source-review-v1.json',author)
dep={}
root_reviews=BASE/'unit-row-advice-ROOT-review-20261016'
for role,path in [('engine',BASE/'unit-row-advice-family-retirement-ROOT-review-20261016/ROOT-engine-v6-Source-review-v1.json'),('adviser',root_reviews/'ROOT-adviser-Source-review-v1.json'),('advice_validator',root_reviews/'ROOT-validator-Source-review-v1.json'),('advice_controls',BASE/'unit-row-advice-family-retirement-ROOT-review-20261016/ROOT-controls-v1-Source-review-v1.json')]:
    r=pin(path);v=read(check(r));assert v['source']==sources[role] and v['source_review_passed'] is True;dep[role]=r
prior=read(BASE/'unit-row-retained-packed-ROOT-20261016/ROOT-original-controls-authorization-v1.json')
for role in ('transition','transition_peer','retained_controls','retained_controls_peer','fallback','controls'):
    r=prior['dependency_reviews'][role];v=read(check(r));assert v['source']==sources[role.removesuffix('_peer')] and v['source_review_passed'] is True;dep[role]=r
for role,folder,name,sha in [
 ('engine','unit-row-advice-family-retirement-engine-independent-source-20261016','typed-Source-review-v1.json','37348afa667cd84934679b205c7c53740a3a063369e1dbe1c178406a2fd867b5'),
 ('adviser','unit-row-goal-branch-adviser-independent-source-20261016','typed-Source-review-v1.json','a4b8846268c5d029880e27703db27cabd0d30a8767a3efb19085129f1c6df12e'),
 ('advice_controls','unit-row-advice-family-retirement-controls-independent-source-20261016','typed-Source-review-v2.json','2d2fd107c28fb83c0fb37ae6a08c084f59c9361d310d72a36d8dbd2069838345')]:
    r=pin(BASE/folder/name);assert r['sha256']==sha;v=read(check(r));assert v['source']==sources[role] and v['source_review_passed'] is True and v['reviewer_identity']!='/root';dep[role+'_peer']=r
runtime=pin(Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'))
assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e' and runtime['bytes']==102352
if mode in ('canonical-search','advised-search'):
    for prefix,number in [('original-controls',17),('domain-controls',17),('advice-controls',30)]:
        c=read(HERE/('ROOT-'+prefix+'-disposition-v1.json'))
        assert c['controls_accepted'] is True and c['native_resources_qualified'] is True and c['passed_cases']==number and c['skipped_cases']==0
        assert read(check(c['plan']))['sources']==sources
        if prefix=='advice-controls':assert c['all_advice_consumer_gates_qualified'] is True and c['additional_coverage_gaps']==[]
protocol=save('ROOT-'+mode+'-protocol-choice-v1.json',{'schema':'ROOT-advised-domain-protocol-choice-v1','previous_goal_turn':'progress','current_goal_turn':'progress','endpoint':mode,'sources':sources,'inputs':inputs,'limits':limits,'scientific_execution':False,
 'expected_cases':30 if mode=='advice-controls' else 17 if mode.endswith('controls') else None,'separate_control_actuals':True,'target_search_unsplit':True,'encoded_output_cap_bytes':4194304,'expanded_output_cap_bytes':16777216,
 'material_change':'Observed dangling-family suppression motivates separate engine6 retirement policy only; currentadviser horizon5/3, controls terms1 and targetterms16 unchanged. Current30controls preserve22+eight added lifecycle gates. All previous UNKNOWNs/skips/late prefixes preserved; no fit prediction or quality repair.',
 'original_search':'Original right-two target/axioms/emptyGamma/parameters24roots0/all-six bounded inventory; initial_stateNone, no word/donor/library/route input.',
 'work_bounds':{'maximum_nodes':128,'maximum_events':2000},'scope':'Current retained-support unit-row ROW-TIE engine; no full reference conformance or learned/RL/GCTS-specific advantage.',
 'costs':'All cold authentication/setup, adviser/validator, snapshots/search/retention/prefix replay, any positive fullword/point/state checking, output/nativeexit/postprobe charged.',
 'search_failure_diagnostics':'Actual returned raw data only under original failure55, unqualified UNKNOWN, no late proof/trajectory/resource authority.'})
owned=HERE/(mode+'-owned-v1');external=HERE/(mode+'-external-v1');assert not owned.exists() and not external.exists()
common={'invocation_id':'unit-row-family-retirement-'+mode+'-20261016-v4','purpose':purposes[mode],'output_directory':str(owned),'sources':sources,'inputs':inputs,'source_contract':cr,'reviews':{'ROOT':author_ref,'peer':pin(peer_path)},'runtime':runtime,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1'}
grant=save('ROOT-'+mode+'-authorization-v1.json',dict(common,schema='ROOT-unit-row-global-engine-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=protocol,dependency_reviews=dep))
plan=save('ROOT-'+mode+'-plan-v1.json',dict(common,schema='ROOT-unit-row-global-engine-plan-v1',ROOT_authorization=grant))
save('ROOT-'+mode+'-preflight-v1.json',{'schema':'ROOT-advised-engine-preflight-v1','plan':plan,'scientific_calls':0,'fresh_owned_and_external_outputs':True,'Source17_inputs2_verified':True})
print(json.dumps({'plan':plan,'external_directory':str(external)}))
