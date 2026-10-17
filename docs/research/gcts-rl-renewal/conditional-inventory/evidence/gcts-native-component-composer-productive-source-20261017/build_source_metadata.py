"""Source/AST/metadata only. Does not import/evaluate mathematical code."""
import ast,copy,difflib,hashlib,json,subprocess,tempfile
from pathlib import Path
H=Path('/private/tmp/gcts-native-component-composer-productive-source-20261017');P=Path('/private/tmp/gcts-native-component-composer-source-20261017')
def raw(p):
 p=Path(p);assert not getattr(p.stat(),'st_flags',0)&0x40000000
 return p.read_bytes()
def pin(p):
 b=raw(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 p=H/n
 with p.open('xb')as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
 return pin(p)
def text(n,s):
 p=H/n
 with p.open('xb')as f:f.write(s.encode())
 return pin(p)
parent=P/'native_conditional_component_composer_v1.py';a=raw(parent)
assert hashlib.sha256(a).hexdigest()=='9fee14c1a5fc3e9e982ce78e0db1f83c8a89352c520d35938c92da307c41f3f2'
s=a.decode();edits=[]
def edit(label,old,new):
 global s
 assert s.count(old)==1,(label,s.count(old));i=s.index(old);edits.append({'label':label,'start':i,'old':old,'new':new});s=s[:i]+new+s[i+len(old):]
edit('VERSION',"VERSION = 'receptor-family-native-conditional-component-composer-v1'","VERSION = 'receptor-family-native-conditional-component-composer-v2-closed-open-slots'")
edit('explicit_two_total_slots',"                  'quantum': 8, 'components': 1}","                  'quantum': 8, 'components': 2}")
edit('fixed_two_slot_limit',"                self.limits[key] = value\n","                self.limits[key] = value\n        require(self.limits['components'] == 2, 'LIMITS',\n                'productive allocation requires exactly one closed and one open slot')\n")
edit('slot_initialization',"    component_names = {}\n","    component_names = {}\n    slots = {'closed': None, 'open': None}\n    normal_prefix_finished = False\n")
old="""                    components.append(record)
                    if len(components) >= w.limits['components']:break
                if len(components) >= w.limits['components']:break
"""
new="""                    # Classify only the fully rebuilt native two-member union.
                    # Other proposals still completed the same census and checks.
                    slot = 'open' if record['input_ports'] else 'closed'
                    retain = slots[slot] is None
                    order.append({'action': 'COMPONENT_SLOT', 'slot': slot,
                        'component_id': record['component_id'], 'retained': retain,
                        'identity_preimage': w.copy(record['identity_preimage'])})
                    if retain:
                        slots[slot] = record['component_id']
                        components.append(record)
                    if all(value is not None for value in slots.values()):break
                if all(value is not None for value in slots.values()):break
"""
edit('retain_first_per_actual_port_class_and_stop_only_both',old,new)
edit('normal_prefix_and_goal_distinction',"""        if components:
            status, reason = 'COMPONENT_PROPOSALS', 'DECLARED_COMPLETE_COMPONENT_CAP_OR_PREFIX'
""","""        normal_prefix_finished = True
        if all(value is not None for value in slots.values()):
            status, reason = 'COMPONENT_PROPOSALS', 'CLOSED_AND_OPEN_SLOTS_FILLED'
        else:
            missing = [slot for slot, value in slots.items() if value is None]
            reason = 'SLOT_AVAILABILITY_GAP_WITHIN_DECLARED_PREFIX:'+','.join(missing)
""")
edit('request_slot_policy',"                    'component_size': 2, 'full_rows': 24, 'rule_order': list(RULES)},","                    'component_size': 2, 'full_rows': 24, 'rule_order': list(RULES),\n                    'component_slots': {'closed': 1, 'open': 1},\n                    'slot_policy': 'FIRST_CLOSED_AND_FIRST_OPEN_EXTERNAL_INPUT'},")
edit('explicit_availability_not_component_invalidity',"        'components': accepted,\n","""        'components': accepted,
        'slot_availability': {
            'policy': 'FIRST_CLOSED_AND_FIRST_OPEN_EXTERNAL_INPUT',
            'observed_component_ids': dict(slots),
            'missing_slots': [slot for slot, value in slots.items() if value is None],
            'both_slots_observed': all(value is not None for value in slots.values()),
            'normal_prefix_finished': normal_prefix_finished,
            'proposal_goal_complete': status == 'COMPONENT_PROPOSALS' and not dirty,
            'component_validity_scope': 'RETAINED_RECORD_CHECKS_ARE_LOCAL_NATIVE_UNION_ONLY',
            'missing_slot_is_component_invalidity': False,
            'availability_or_useful_transfer_proved': False},
""")
source=text('native_conditional_component_composer_v2.py',s);b=s.encode();t=ast.parse(b);compile(b,source['path'],'exec',dont_inherit=True)
back=s
for e in reversed(edits):
 i=e['start'];assert back[i:i+len(e['new'])]==e['new'];back=back[:i]+e['old']+back[i+len(e['new']):]
assert back.encode()==a and ast.dump(ast.parse(back),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
patches={}
for label,x,y in [('forward',a,b),('full-inverse',b,a)]:
 p=text(label+'-v2.patch',''.join(difflib.unified_diff(x.decode().splitlines(True),y.decode().splitlines(True),fromfile='before',tofile='after')));patches[label]=p
 with tempfile.TemporaryDirectory(dir=str(H))as td:
  target=Path(td)/'before';target.write_bytes(x)
  r=subprocess.run(['/usr/bin/patch','--batch',str(target),'-i',p['path']],cwd=td,capture_output=True)
  assert r.returncode==0 and target.read_bytes()==y
delta=save('Source-delta-v2.json',{'schema':'receptor-native-component-productive-slots-Source-delta-v2','parent_source':pin(parent),'source':source,'edits':edits,'patches':patches,'whole_raw_inverse_exact':True,'whole_AST_inverse_exact':True,'actual_patch_both_directions_exact':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
constants={n.targets[0].id:ast.literal_eval(n.value)for n in t.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
limits=constants['DEFAULT_LIMITS'];oldC=json.loads(raw(P/'Source-contract-v1.json'))
api=save('API-wire-v2.json',{'schema':'receptor-family-native-component-composer-API-v2','version':constants['VERSION'],'signature':'compose_components(*,language,base_semantics,marked_semantics,point_module,base_fallback,host_adapter,tick,limits=None)','public_injections_unchanged':True,'result_schema':constants['RESULT_SCHEMA'],'statuses':['COMPONENT_PROPOSALS','UNKNOWN'],'limits':limits,'limit_policy':'All old exact positive own caps may be lowered except total components is fixed2 for explicit1closed+1open experiment; components1 is rejected with ComposerDataError codeLIMITS. All root24 rows/native six-rule fallback streams remain available as finite proposal prefixes, not new model bounds.','component_slots':{'closed':1,'open':1},'classification':'Only after original full candidate/native/point union/component() checks: closed iff actual remaining input_ports==[]; open iff actual remaining input_ports nonempty. No formula/row/rule/vacuity/target classification.','retention_and_order':'First actual checked component in each class retained in encounter order. Same-class later connected proposals still undergo native/union/full global census/collision checks, then are discarded from retained slots; construction_order COMPONENT_SLOT entries preserve identity_preimage and retained flag. No alternative point unions merged.','stop':'Stop after BOTH slots filled and their full public-census/fresh-native/union/bookkeeping boundary completed; otherwise unchanged root48/ext96/headquota1/quantum8/work1m/depth128 prefixes. Filling closed alone never stops construction.','result_delta':{'request':'adds component_slots and slot_policy','slot_availability':'policy,observed_component_ids,missing_slots,both_slots_observed,normal_prefix_finished,proposal_goal_complete,component_validity_scope,missing_slot_is_component_invalidityFalse,availability_or_useful_transfer_provedFalse','components':'Both complete slot goals/current global join only when COMPONENT_PROPOSALS; encounter-order list of2','unaccepted_complete_components':'Retained individually checked records on normal missing-slot UNKNOWN or own-bound UNKNOWN; their local checks do not imply invalidity merely because another slot is missing. Hard/native/callback/data/collision errors propagate; no output certificate.','unchanged':'All full component fields/member/native/union records, heads, public cursor contexts/events/prefix census, global full original+decorated preimages and false broad flags are retained.'},'unknown':'Missing slots under a normal bounded prefix are availability gaps, not absence/exhaustion/invalidity proofs. Own-work/depth interruption retains old wholeUNKNOWN/nooperative components semantics; native errors propagate unchanged. No late census after failed advance.','source_only':True,'scientific_calls':0,'scientific_acceptance':False})
def regions(data):
 ls=data.decode().splitlines(True);out={}
 def walk(ns,prefix=''):
  for n in ns:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
    key=prefix+n.name;out[key]=(''.join(ls[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False),n.lineno,n.end_lineno);walk(n.body,key+'.')
 walk(ast.parse(data).body);return out
ra,rb=regions(a),regions(b);changed=[k for k in ra if ra[k][:2]!=rb[k][:2]]
assert set(changed)=={'_Work','_Work.__init__','compose_components'}
same=[{'name':k,'line':rb[k][2],'end_line':rb[k][3]}for k in ra if ra[k][:2]==rb[k][:2]]
checks={'whole8edit_raw_and_AST_inverse':len(edits)==8,'actual_forward_fullinverse_patch_application':True,'only_Work_init_and_containing_compose_changes_existing_regions':True,'all_native_candidate_membership_union_collision_public_census_helpers_raw_AST_exact':all(ra[k][:2]==rb[k][:2]for k in ('compose_components.merge','compose_components.state_record','compose_components.insert','compose_components.export_cursor','compose_components.open_task','compose_components.advance','compose_components.component')),'old_noncomponent_caps_exact':{k:v for k,v in limits.items()if k!='components'}=={k:v for k,v in oldC['limits'].items()if k!='components'},'original_RULES_FLAGS_and_allpublicversions_exact':constants['FLAGS']==oldC['flags'],'no_engine_search_place_decision_calls':not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in ('search','place','decision')for n in ast.walk(t)),'AST_compile_without_evaluation':True}
assert all(checks.values())
audit=save('static-audit-v2.json',{'schema':'receptor-native-component-productive-slots-static-audit-v2','source':source,'source_delta':delta,'checks':checks,'unchanged_named_regions':same,'changed_existing_regions':changed,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'project_module_imported_or_evaluated':False})
C={'schema':'receptor-family-native-component-composer-productive-slots-Source-contract-v2','scope':'receptor-family-native-component-composer-productive-slots-Source','author_identity':'/root/hilbert_advice_controls','source':source,'sources':{'composer':source},'version':constants['VERSION'],'API_wire':api,'source_delta':delta,'static_audit':audit,'operative_parent_contract':pin(P/'Source-contract-v1.json'),'parent_handoff':pin(P/'handoff-v1.json'),'parent_distinct_review':pin('/private/tmp/gcts-native-component-composer-peer-20261017/typed-Source-review-v1.json'),'master':pin('/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md'),'dependency_sources':oldC['dependency_sources'],'original_model_sources':oldC['original_model_sources'],'original_model_inputs':oldC['original_model_inputs'],'original_model_binding':oldC['original_model_binding'],'limits':limits,'fixed_slots':{'closed':1,'open':1},'inheritance':'Only original mathematical protocols, fixed model/bindings and exact unchanged Source regions are inherited. No old runtime/component/engine qualification or availability is transferred.','human_heuristic':'A deliberately human-declared structural proposal allocation: reserve one empty-interface and one open-external-input component to avoid ending only on the first closed pair. It is not a learned policy, accepted generalized lemma, theorem-driven pruning or complete inverse matching. Closed/vacuous components remain locally valid when checked; this policy makes no usefulness claim.','correctness_scope':'Class membership comes solely from actual remaining unoccupied external ports of the independently/native-checked full two-member union. Every encountered public original/decorated exposure including channel4-removed/discarded proposals remains in the single full preimage census. All original own/native/error/dirty-boundary semantics, root24/six native domains and separate alternative unions remain.','gaps':['First-class-only retention and headquota1/finite48+96 advance prefixes can miss open or closed components; neither may be manufactured or promised.','Missing slot leaves overallUNKNOWN and exact retained local component checks/provenance visible; does not refute those components or prove global unavailability.','No engine/BRANCH/provider or live viability/complete candidate graph/degree/EOF/pruning/rollback acceptance; complete canonical fallback is unchanged and not replaced by inventory.','No useful transfer, generalized lemma, original target completion, RL/GCTS gain, runtime or fit claim. All construction/check/serialization costs must be charged under future original native20/512 Root window.'],'future_controls':['Closed-first alone continues with unchanged queues until open or bound; open-first symmetrically waits for closed.','Both slots iff one exact empty-interface and one exact nonempty-interface full native union, encounter order and full identities, no deduped single-member fiction.','Same-class discarded connected proposals still contribute all exposed type fullpreimages/collision checks and recorded slot decision.','Normal missing-slot prefix vs own-bound/dirty interruption vs native/callback/export/collision error propagation remain distinct and never imply proved pruning.'],'flags':constants['FLAGS'],'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'runtime_qualified':False,'runtime_fit':'UNMEASURED'}
C['Review_ABI']={'schema':'receptor-family-native-component-composer-productive-slots-typed-Source-review-v2','scope':C['scope'],'author_identity':C['author_identity'],'source':source,'sources':C['sources'],'source_contract':'current capsule','source_only':True,'scientific_calls':0,'scientific_acceptance':False}
cref=save('Source-contract-v2.json',C);abi=dict(C['Review_ABI'],source_contract=cref)
href=save('handoff-v2.json',{'schema':'receptor-native-component-productive-slots-Source-handoff-v2','source':source,'source_contract':cref,'API_wire':api,'source_delta':delta,'static_audit':audit,'actual_patches':patches,'Review_ABI':abi,'intended_behavior':'One closed+one open slot. No closed-only stop. Both goals permit COMPONENT_PROPOSALS; missing slot or ownbound UNKNOWN retains narrow valid local records only, no pruning/fact/availability proof.','original_limits_except_two_retained_slots':{k:v for k,v in limits.items()if k!='components'},'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False})
print(json.dumps({'source':source,'contract':cref,'API':api,'delta':delta,'audit':audit,'handoff':href,'changed_regions':changed,'unchanged_regions':len(same)},sort_keys=True))
