from pathlib import Path
import ast, hashlib, json, difflib, subprocess
D=Path('/private/tmp/gcts-first-admission-diagnostic-source-20261017')
def ref(p):
 p=Path(p); b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(name,v):
 p=D/name
 with p.open('x')as f:json.dump(v,f,ensure_ascii=True,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
def defs(text):
 lines=text.splitlines(keepends=True); out={}
 def visit(n,path):
  for c in ast.iter_child_nodes(n):
   if isinstance(c,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
    key=path+'.'+c.name if path else c.name
    out[key]=(''.join(lines[c.lineno-1:c.end_lineno]),ast.dump(c,include_attributes=False));visit(c,key)
   else:visit(c,path)
 visit(ast.parse(text),'');return out
roles={'writer_replacement':('parent-writer.fragment.py','save_failure_diagnostic_v3.fragment.py'),'saved_reader_candidate':('parent-saved-reader.py','first_admission_saved_reader_v3.py')}
records={}; checks=[]
for role,(a,b) in roles.items():
 old=(D/a).read_text();new=(D/b).read_text();ast.parse(new);compile(new,str(D/b),'exec')
 edits=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
  if tag!='equal':edits.append({'old_start':i,'old_end':j,'new_start':k,'new_end':l,'before':old[i:j],'after':new[k:l]})
 f=old
 for e in reversed(edits):
  assert f[e['old_start']:e['old_end']]==e['before'];f=f[:e['old_start']]+e['after']+f[e['old_end']:]
 assert f==new
 inv=new
 for e in reversed(edits):
  assert inv[e['new_start']:e['new_end']]==e['after'];inv=inv[:e['new_start']]+e['before']+inv[e['new_end']:]
 assert inv==old and ast.dump(ast.parse(inv),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
 for direction,left,right in [('forward',old,new),('inverse',new,old)]:
  p=D/(role+'-'+direction+'.patch');p.write_text(''.join(difflib.unified_diff(left.splitlines(keepends=True),right.splitlines(keepends=True),fromfile='target.py',tofile='target.py')))
  work=D/('patch-audit-'+role+'-'+direction);work.mkdir();(work/'target.py').write_text(left)
  r=subprocess.run(['patch','--batch','--fuzz=0','-p0','-i',str(p)],cwd=work,capture_output=True,text=True)
  assert r.returncode==0 and (work/'target.py').read_text()==right,(role,direction,r.stdout,r.stderr)
 olddefs,newdefs=defs(old),defs(new)
 equal=[k for k in olddefs if k in newdefs and olddefs[k]==newdefs[k]]
 changed=[k for k in olddefs if k not in equal]
 added=[k for k in newdefs if k not in olddefs]
 records[role]={'parent':ref(D/a),'source':ref(D/b),'edits':edits,'forward_patch':ref(D/(role+'-forward.patch')),'inverse_patch':ref(D/(role+'-inverse.patch')),'full_forward_raw':True,'full_inverse_raw':True,'full_inverse_AST':True,'actual_patch_forward':True,'actual_patch_inverse':True,'raw_AST_exact_regions':equal,'changed_regions':changed,'added_regions':added}
 checks.append({'role':role,'parse_compile_without_evaluation':True,'raw_edit_count':len(edits),'unchanged_named_regions':len(equal),'actual_patch_directions':2})
writer=(D/roles['writer_replacement'][1]).read_text();oldwriter=(D/roles['writer_replacement'][0]).read_text()
# Exact original function restored by deleting only the new branch and completion selection.
start=writer.index("    elif failure_kind == 'CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3':")
end=writer.index('    else:\n        available = capture',start)
erased=writer[:start]+writer[end:]
erased=erased.replace("else 'unit-row-controls-engine-milestones-completion-v3' if failure_kind == 'CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3' else 'unit-row-search-failure-diagnostic-completion-v1'),","else 'unit-row-search-failure-diagnostic-completion-v1'),",1)
assert erased==oldwriter
# All original captured endpoint/defaults and nested native/encoder/write helpers stay exact.
wd,od=defs(writer),defs(oldwriter)
assert all(wd[k]==od[k] for k in od if k!='save_failure_diagnostic')
oldfn=ast.parse(oldwriter).body[0];newfn=ast.parse(writer).body[0]
assert ast.dump(oldfn.args,include_attributes=False)==ast.dump(newfn.args,include_attributes=False)
rd=defs((D/'first_admission_saved_reader_v3.py').read_text());pod=defs((D/'parent-saved-reader.py').read_text())
for name in ('need','canonical','unique','decode','raw_pin','read','pinned','write','validate_positive_callback_phases'):
 assert rd[name]==pod[name]
parent_root=Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017')
parent_contract=json.loads((parent_root/'Source-contract-v1.json').read_text())
engine=Path('/private/tmp/gcts-first-admission-journal-engine-source-20261017')
api_engine=json.loads((engine/'API-wire-v8.json').read_text())
parent_cold=(parent_root/'callback_stage_receiver_cold_v1.py').read_text()
node=next(n for n in ast.parse(parent_cold).body if isinstance(n,ast.FunctionDef)and n.name=='save_failure_diagnostic')
assert ''.join(parent_cold.splitlines(keepends=True)[node.lineno-1:node.end_lineno])+'\n'==oldwriter
read_text=(D/'first_admission_saved_reader_v3.py').read_text()
ph={}
for n in ast.parse(read_text).body:
 if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id in ('LEGACY_PHASES','CALLBACK_PHASES','SEARCH_PHASES','MILESTONE_PHASES'):
  ph[n.targets[0].id]=ast.literal_eval(n.value)
labels=sum(ph.values(),());assert len(labels)==len(set(labels))==34
lengths={x:len(b'COMPONENT_INVENTORY_PHASE ')+len(x.encode())+1+19+1 for x in labels}
assert max(lengths.values())==75 and sum(lengths.values())==2160
sources={k:ref(D/v[1])for k,v in roles.items()}
delta=put('Source-delta-v1.json',{'schema':'ROOT-first-admission-diagnostic-seam-raw-delta-v1','source_only':True,'scientific_calls':0,'roles':records})
audit=put('static-audit-v1.json',{'schema':'ROOT-first-admission-diagnostic-seam-static-audit-v1','source_only':True,'module_evaluations':0,'scientific_calls':0,'project_function_executions':0,'py_compile_used':False,'checks':checks,'writer_old_branches_raw_erasure_exact':True,'writer_signature_defaults_AST_exact':True,'writer_nested_native_encoder_write_regions_raw_AST_exact':True,'reader_nine_unchanged_top_helpers_raw_AST_exact':True,'phase_lengths_at_19_digits':lengths,'phase_count':34,'max_line_bytes':75,'max_total_bytes':2160,'semantic_payload_checked':False,'no_actual_or_result_inputs':True})
api=put('API-wire-v1.json',{'schema':'ROOT-first-admission-diagnostic-seam-API-v1','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'writer':{'function':'save_failure_diagnostic','signature_unchanged':True,'failure_kind':'CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3','capture_keys':['legacy','provider_returns','engine_milestones'],'legacy_and_provider_shapes':'Exactly unchanged from operative providerV2 branch','engine_capture':'Fixed four list, null or exact ordinal/stage/native_ns/record wrapper; monotone nonnull prefix. Native original20 stamps. Records remain full opaque builtin JSON data.','diagnostic_schema':'unit-row-controls-engine-milestones-diagnostic-v3','completion_schema':'unit-row-controls-engine-milestones-completion-v3','outer_fields':['context','diagnostic','last_observations','provider_returns','engine_milestones'],'journal_metadata_fields':['captured_headers','captured_record_count','serialized_record_count','omitted_record_count','next_omitted_ordinal','engine_record_prefix_reason','engine_journal_bytes'],'prefix_reasons':['ALL_CAPTURED_RECORDS_SAVED','NEXT_RECORD_OUTPUT_BOUND_OR_BUILTIN_TYPE','ENGINE_JOURNAL_AGGREGATE_BYTE_LIMIT'],'journal_budget_bytes':3145728,'journal_encoding':'ensure_ascii=True, separators comma/colon without spaces, insertion order, no sort; complete fixed4 list including null placeholders and brackets','whole_diagnostic_max_bytes':4325376,'context_max_bytes':65536,'failure_window_seconds':55,'internal_peak_bound_bytes':524288000,'old_kinds_unchanged':True,'size_omissions':'Only own bounded builtin encoder ValueError or aggregate limit. Native/resource/endpoint exceptions propagate; complete diagnostic pair is never guaranteed.'},'reader':{'functions':['read_phases','validate_positive_callback_phases','validate_engine_milestones','read_failure_diagnostic','main'],'positive_payload_path':'evidence.receiver_probe.engine_milestones','positive_join':'Validate full raw fixed4 prefix independently of callback observation counts, exact stage/version/depth/field wire plus reached marker/timestamp bounds; no semantic replay','failure_join':'Exact captured headers vs complete serialized prefix and insertion-order ASCII byte length; captured headers may exceed serialized records, never manufacture missing records.','authority_literals':'Current parent authority literals/schema/responseVERSION intentionally unchanged for Root rebinding','original20_seconds':20,'marker_count':34,'marker_max_line_bytes':75,'marker_max_total_bytes':2160,'milestone_phases':ph['MILESTONE_PHASES'],'phase_order':'Sequential P/C groups; M ordinal prefix after C1_READY and before later P2/C2/C3; one incomplete P/C group may remain when search catches TimeoutError. Reached marker alone does not require its own capture; a later M marker requires previous captured headers. Partial final marker is raw tail only.'},'stage_API':ref(engine/'API-wire-v8.json'),'engine_version':api_engine['VERSION'],'stage_fields':api_engine['stage_fields'],'callback_capture_source':ref('/private/tmp/gcts-first-admission-ROOT-source-20261017/capture_engine_milestone.fragment.py'),'flags':{'raw_diagnostic_only':True,'engine_admission_accepted':False,'offers_accepted':False,'current_state_accepted':False,'logical_proof_accepted':False,'failure_cause_established':False,'runtime_qualified':False,'RL_accepted':False}})
contract={'schema':'ROOT-first-admission-diagnostic-seam-Source-contract-v1','scope':'ROOT-first-admission-diagnostic-seam-Source','author':'/root/hilbert_advice_controls','source_only':True,'scientific_calls':0,'module_evaluations':0,'scientific_acceptance':False,'actual_execution_authorized':False,'source':sources['writer_replacement'],'sources':sources,'operative_parent_contract':ref(parent_root/'Source-contract-v1.json'),'parent_cold':ref(parent_root/'callback_stage_receiver_cold_v1.py'),'parent_reader':ref(parent_root/'ROOT_read_callback_stage_receiver_saved_v1.py'),'parent_seam_contract':ref('/private/tmp/gcts-callback-stage-diagnostic-source-20261017/Source-contract-v3.json'),'parent_seam_peer':ref('/private/tmp/gcts-callback-stage-diagnostic-peer-20261017/typed-Source-review-v3.json'),'original_model_binding':parent_contract['original_model_binding'],'original_model_sources':parent_contract['original_model_sources'],'original_model_inputs':parent_contract['original_model_inputs'],'future_Root_composition':{'source_count':22,'input_count':10,'semantic_source_count':17,'semantic_input_count':2,'Root_version':'ROOT-receiver-inference-probe-cold-v5-first-admission-journal','current_scope':'Replacements only: no new executable authority map is claimed here. Root final intake/current contract, identity guards and distinct reviews required before any measured actual.'},'engine_source':api_engine['source'],'engine_contract':ref(engine/'Source-contract-v8.json'),'engine_API':ref(engine/'API-wire-v8.json'),'capture_source':ref('/private/tmp/gcts-first-admission-ROOT-source-20261017/capture_engine_milestone.fragment.py'),'API':api,'delta':delta,'static_audit':audit,'limits':{'original20_seconds':20,'failure_only_seconds':55,'native_peak_limit_bytes':536870912,'internal_peak_limit_bytes':524288000,'whole_diagnostic_bytes':4325376,'engine_journal_bytes':3145728,'positive_expanded_bytes':16777216,'positive_encoded_bytes':4194304,'phase_max_line_bytes':75,'phase_max_total_bytes':2160,'phase_count':34},'boundaries':['New failure branch is raw builtin serialization under captured native55 endpoints only; no original20 or project helper call occurs there.','Every serialized record is whole; omitted suffix and uncaptured slots remain distinct. Timeout/resource failures are never classified as output omissions.','M1 plan may be canonical fallback and M4 child decision any status. A state-shaped record or reached milestone never proves an accepted offer, placement, restoration or theorem.','Reached M phase may have null capture after post-phase native failure. Later phases never fill an earlier absent payload.','Positive reader only reconciles authenticated literal wire and resource metadata; original full native/source/once/CodeSeal/transport contracts remain Root responsibilities.','Read-only writer/readout Source work inspected no actual/result/proofword files and executed no generated function.'],'authorship_overlap':'Controls authored prior provider/consumer/adapter and writer/readout seam. Root owns current integration and actuals; Diagnosis authors engine8 and separately reviews this seam. This packet is author static evidence, not its own independent Source review.','Review_ABI':{'schema':'ROOT-first-admission-diagnostic-seam-typed-Source-review-v1','scope':'ROOT-first-admission-diagnostic-seam-Source','source':sources['writer_replacement'],'sources':sources,'source_contract':'EXACT_CURRENT_CONTRACT_PIN','source_only':True,'source_review_passed':'bool','scientific_calls':0,'scientific_acceptance':False,'reviewer_identity':'distinct from author; disclose engine/old seam overlap'}}
cref=put('Source-contract-v1.json',contract)
handoff=put('handoff-v1.json',{'schema':'ROOT-first-admission-diagnostic-seam-handoff-v1','author':'/root/hilbert_advice_controls','source_only':True,'scientific_calls':0,'module_evaluations':0,'scientific_acceptance':False,'actual_execution_authorized':False,'sources':sources,'source_contract':cref,'API':api,'delta':delta,'static_audit':audit,'Root_integration':'Copy writer function raw into current main; rebind only reader authority/current schema/review scope/responseVERSION in separately reviewed Root composition. payload.engine_milestones is full fixed4 raw list. Existing original native20/55, Source/once/custody machinery unchanged.','Review_ABI':contract['Review_ABI']})
print(json.dumps({'handoff':handoff,'contract':cref,'sources':sources,'API':api,'delta':delta,'static':audit,'checks':checks},indent=2))
