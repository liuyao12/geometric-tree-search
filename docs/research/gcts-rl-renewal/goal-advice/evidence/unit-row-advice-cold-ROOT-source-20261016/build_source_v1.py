"""Raw Source assembly/AST checks only; never execute a scientific module."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
    p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
def save(name,value):
    p=HERE/name
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
assert len(sys.argv)==3,'frozen engine handoff and controls handoff required'
eh,ch=(read(Path(name)) for name in sys.argv[1:])
for h in (eh,ch):assert h['source_only'] and h['scientific_calls']==0 and not h['scientific_acceptance'];check(h['source']);check(h['source_contract'])
parent=BASE/'unit-row-retained-cold-ROOT-source-20261016/unit_row_retained_domain_cold_v2.py'
parent_contract=parent.parent/'Source-contract-v2.json'
assert pin(parent)['sha256']=='3cb4edbfcb0dfafd712f97f4319f0b0b5ccb74e1a31f20077cd747f73558a3a4'
old=parent.read_text();source_text=old;edits=[]
def replace(before,after):
    global source_text
    assert source_text.count(before)==1,before[:120]
    source_text=source_text.replace(before,after,1);edits.append({'before':before,'after':after})
old_tree=ast.parse(old)
fixed=ast.literal_eval(next(n.value for n in old_tree.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='FIXED' for v in n.targets)))
fixed['engine']=eh['source']
fixed['adviser']=pin(BASE/'unit-row-goal-branch-adviser-source-20261016/goal_branch_adviser_v1.py')
assert fixed['adviser']['sha256']=='c6fc2e5dfae79eb4f3a070f1439e2461f9f684ee72ee3bf4620aca7645ef40cb'
vh=read(BASE/'unit-row-independent-advice-consumer-source-20261016/handoff-v2.json')
fixed['advice_validator']=vh['source'];assert fixed['advice_validator']['sha256']=='f668330c0ed98b9d6cd56150996c141c991a93b9058b898a86fd3068c832d317'
fixed['advice_controls']=ch['source']
prior_point=read(BASE/'shared-bounded-point-board-ROOT-20261015/ROOT-plan-v1.json')['sources']
for role,oldrole in [('word_checker','checker'),('converter','converter'),('point_checker','point_checker')]:fixed[role]=prior_point[oldrole]
for ref in fixed.values():check(ref)
assert len(fixed)==16
line=next(line for line in old.splitlines() if line.startswith('FIXED='));replace(line,'FIXED='+repr(fixed))
replace("VERSION='unit-row-retained-domain-cold-v2-lossless-wire'","VERSION='unit-row-advised-domain-cold-v1'")
replace("SCOPE='unit-row-retained-domain-cold-Source'","SCOPE='unit-row-advised-domain-cold-Source'")
oldpurposes="('unit-row-retained-original-controls','unit-row-retained-domain-controls','unit-row-retained-target-search')"
newpurposes="('unit-row-advised-original-controls','unit-row-advised-domain-controls','unit-row-advised-advice-controls','unit-row-advised-canonical-search','unit-row-advised-target-search')"
replace(oldpurposes,newpurposes)
replace("contract['schema'] == 'unit-row-retained-domain-cold-Source-contract-v2'","contract['schema'] == 'unit-row-advised-domain-cold-Source-contract-v1'")
replace('    def engine_factory(*,initial_state=None,degree_proposer=proposer_adapter,\n            fallback=fallback_adapter,certify_fallback=certify_adapter,tick):',
        '    def engine_factory(*,initial_state=None,degree_proposer=proposer_adapter,\n            fallback=fallback_adapter,certify_fallback=certify_adapter,\n            branch_adviser=None,validate_advice=None,tick):')
replace('            fallback=fallback,certify_fallback=certify_fallback,tick=step,\n            initial_state=copy.deepcopy(initial_state),maximum_nodes=128,maximum_events=2000)',
        '            fallback=fallback,certify_fallback=certify_fallback,tick=step,\n            branch_adviser=branch_adviser,validate_advice=validate_advice,\n            initial_state=copy.deepcopy(initial_state),maximum_nodes=128,maximum_events=2000)')
replace("    search_capture = {'returned':False,'payload':None,'returned_ns':None}",
        (HERE/'advice_adapters_block_v1.txt').read_text()+'\n'+(HERE/'proof_validation_block_v1.txt').read_text()+"\n    search_capture = {'returned':False,'payload':None,'returned_ns':None}")
replace('        engine = engine_factory(initial_state=None,tick=tick)',
        "        enabled = plan['purpose'] == 'unit-row-advised-target-search'\n        engine = engine_factory(initial_state=None,tick=tick,\n            branch_adviser=adviser_adapter if enabled else None,\n            validate_advice=validate_advice_adapter if enabled else None)")
replace("    is_controls = plan['purpose'] != 'unit-row-retained-target-search'",
        "    found_validation = None\n    is_controls = plan['purpose'] in ('unit-row-advised-original-controls','unit-row-advised-domain-controls','unit-row-advised-advice-controls')")
replace("        is_original = plan['purpose'] == 'unit-row-retained-original-controls'\n        selected_controls = modules['controls'] if is_original else modules['retained_controls']",
        "        is_original = plan['purpose'] == 'unit-row-advised-original-controls'\n        is_advice = plan['purpose'] == 'unit-row-advised-advice-controls'\n        selected_controls = modules['controls'] if is_original else modules['advice_controls'] if is_advice else modules['retained_controls']")
replace("        else:\n            control_kwargs.update(transition=transition_adapter,refresh=refresh_adapter)\n        payload = invoke_fn(selected_controls.run_controls,(),control_kwargs,",
        "        elif is_advice:\n            control_kwargs.update(adviser=adviser_adapter,validate_advice=validate_advice_adapter)\n        else:\n            control_kwargs.update(transition=transition_adapter,refresh=refresh_adapter)\n        payload = invoke_fn(selected_controls.run_controls,(),control_kwargs,")
replace("        expected_schema = ('unit-row-lazy-global-controls-v1' if is_original\n                           else 'unit-row-retained-domain-controls-v1')",
        "        expected_schema = ('unit-row-lazy-global-controls-v1' if is_original\n                           else 'unit-row-goal-advice-controls-v1' if is_advice\n                           else 'unit-row-retained-domain-controls-v1')")
replace("                'fresh original-root search result, not an accepted proof')",
        "                'fresh original-root search result, not an accepted proof')\n            need((payload['found'] is not None) is (payload['status'] == 'POINT_BOARD_PROPOSAL'),\n                 'found proposal exactly joins producer board-proposal status')\n            if payload['found'] is not None:\n                found_validation = invoke_fn(validate_found,(copy.deepcopy(payload['found']),),{},\n                    boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)")
replace("        'search':None if is_controls else payload,'search_work_bounds':{'maximum_nodes':128,'maximum_events':2000},",
        "        'search':None if is_controls else payload,'found_validation':found_validation,\n        'search_work_bounds':{'maximum_nodes':128,'maximum_events':2000},")
selected=HERE/'unit_row_advised_domain_cold_v1.py'
with selected.open('xb') as f:f.write(source_text.encode())
tree=ast.parse(source_text);compile(tree,str(selected),'exec')
inverse=source_text
for edit in reversed(edits):
    assert inverse.count(edit['after'])==1
    inverse=inverse.replace(edit['after'],edit['before'],1)
assert inverse==old
olddefs={n.name:n for n in old_tree.body if isinstance(n,ast.FunctionDef)}
newdefs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
unchanged=[n for n in olddefs if n!='main']
for name in unchanged:
    assert ast.dump(olddefs[name],include_attributes=False)==ast.dump(newdefs[name],include_attributes=False)
    assert ast.get_source_segment(old,olddefs[name])==ast.get_source_segment(source_text,newdefs[name])
tail="    body = {'schema':'ROOT-unit-row-global-engine-response-body-v1',"
assert source_text[source_text.index(tail):]==old[old.index(tail):]
source=pin(selected);sources=dict(fixed,intake=source);parentc=read(parent_contract)
delta=save('source-delta-v1.json',{'schema':'ROOT-advised-cold-Source-delta-v1','parent':pin(parent),'source':source,'edits':edits,'entire_inverse_recovers_parent':True})
purposes={
 'unit-row-advised-original-controls':'Original17 controls on current optional-advice engine, callbacks disabled.',
 'unit-row-advised-domain-controls':'Original17 retention/archive/rollback controls on current engine, callbacks disabled.',
 'unit-row-advised-advice-controls':'New genuine adviser/independent consumer/transaction controls, explicit malformed or interruption seams.',
 'unit-row-advised-canonical-search':'Fresh canonical arm on same selected engine/caller and original full target, advice disabled.',
 'unit-row-advised-target-search':'Fresh advised arm on same selected engine/caller and original full target, advice enabled.'}
c={'schema':'unit-row-advised-domain-cold-Source-contract-v1','author_identity':'/root','scope':'unit-row-advised-domain-cold-Source',
 'sources':sources,'inputs':parentc['inputs'],'limits':parentc['limits'],'resource_rule':parentc['resource_rule'],
 'parent_source':pin(parent),'parent_contract':pin(parent_contract),'source_delta':delta,'purposes':purposes,
 'source_only':True,'scientific_calls':0,'scientific_acceptance':False,
 'unchanged_top_level_helpers':unchanged,'unchanged_failure_writer':True,'unchanged_result_transport':True,
 'positive_response_stdout_native_exit_tail_exact':True,
 'authority':'Same original input2; fresh private language for original and new adviser/independent consumer calls, per-engine semantics, and positive proof/point checking. No proof word/donor/library/route input or model change.',
 'guards':'All17 selected Sources covered by unchanged surrounding CodeSeal/all-function anchors and native tick preceding injected control tick. New adapters reuse original invoke; no per-yield/hostile concurrent OS guarantee and no new custody framework.',
 'scheduler':'Unchanged whole-frontier dead/forced/earliest-generation ROW-TIE; advice only after actual BRANCH. Independent current anchor validation, one pending family, ordinary canonical intervening rows, exact owned checkpoint adoption/rollback and full all-six fallback remain mandatory.',
 'advice':'Current c6fc hand-written generic goal/novelty/schema proposals, never learned/RL/pruning authority. Whole READY batch independently validated by f668. Native-owning failure propagates; own quota UNKNOWN partial advice ignored. Future member keys uninstalled, current legality checked only at their selected row.',
 'search':'Both search endpoints start initial_stateNone, original24 roots0, max128nodes/2000events. No new two-witness cache or grammar/boundary change. Each once stage separate original20/512MiB, failure55/owned60/caller90+1. Matching Source does not by itself establish a matched successful result.',
 'positive_verification':'If a board is proposed, fresh original membership and unchanged1717 full word check, independently authored99b3 full point projection/union, and actual foundstate selected/t/m equality are checked INSIDE the same cold20 endpoint. Whole checking/serialization/output/native terminal/probe costs remain charged; no late proof acceptance.',
 'diagnostics':parentc['diagnostics'],'retention':parentc['retention'],'transport':parentc['transport'],
 'gaps':parentc['gaps']+['No adviser/pending-consumer runtime or matched proof-discovery result before fresh controls/actuals.','Hand-written advice is not RL, learned marking, lemma inventory learning or a GCTS-specific advantage.','Logical/point positive checks do not certify complete candidate graph/search trajectory or universal fixed Wang compiler.'],
 'Review_ABI':{'schema':'unit-row-advised-domain-cold-typed-Source-review-v1','scope':'unit-row-advised-domain-cold-Source','author_identity':'/root','source':source,'sources':sources,'source_contract':'exact current contract capsule','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'source_review_passed':'Distinct whole-caller peer decides; Root author review is separate.'}}
cr=save('Source-contract-v1.json',c)
save('static-evidence-v1.json',{'source':source,'source_contract':cr,'top_level_helpers_raw_and_AST_exact':unchanged,'response_stdout_native_exit_suffix_raw_exact':True,'entire_inverse_recovers_parent':True,'Source17_input2_sixlimits':True,'compile_only':True,'scientific_execution':False})
h=save('handoff-v1.json',{'schema':'ROOT-advised-cold-Source-handoff-v1','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True,'engine_handoff':pin(Path(sys.argv[1])),'controls_handoff':pin(Path(sys.argv[2])),'validator_handoff':pin(BASE/'unit-row-independent-advice-consumer-source-20261016/handoff-v2.json')})
print(json.dumps({'source':source,'source_contract':cr,'handoff':h}))
