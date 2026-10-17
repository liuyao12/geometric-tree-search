from pathlib import Path
import ast,hashlib,json,difflib,subprocess
D=Path('/private/tmp/gcts-hilbert-shared-family-collector-source-20261017')
A=Path('/private/tmp/gcts-hilbert-shared-family-adapter-v2-source-20261017')
P=D/'hilbert_shared_family_selected_dag_collector_v1.py';s=P.read_text();t=ast.parse(s);compile(s,str(P),'exec')
def ref(p):
 p=Path(p)
 if p.stat().st_flags&0x40000000:raise ValueError('dataless Source reference; stop rather than duplicate read: '+str(p))
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,v):
 p=D/n
 with p.open('x')as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
# Caller supplies exact peer pin after the independently reviewed adapter repair.
peer_path=Path('/private/tmp/gcts-hilbert-shared-family-adapter-peer-20261017/typed-Source-review-v2.json')
peer=json.loads(peer_path.read_text());adapter=ref(A/'hilbert_shared_family_admission_adapter_v2.py')
assert peer['source']==adapter and peer['source_review_passed']is True and peer['source_only']is True and peer['scientific_calls']==0
imports=[n.names[0].name for n in t.body if isinstance(n,ast.Import)]
assert imports==['hashlib','json']and not any(isinstance(n,ast.ImportFrom)for n in t.body)
assert all(isinstance(n,(ast.Expr,ast.Import,ast.Assign,ast.ClassDef,ast.FunctionDef))for n in t.body)
for node in t.body:
 if isinstance(node,ast.Assign):ast.literal_eval(node.value)
attrs=sorted({n.func.attr for n in ast.walk(t)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)})
assert not set(attrs)&{'_context','adapt_expansion','search','solve','proof','apply','_apply_legal','rollback','checkpoint','decision','ordered_domain','candidates','exclude_failed_child','import_module'}
assert not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id in ('eval','exec','open','__import__')for n in ast.walk(t))
assign={n.targets[0].id:ast.literal_eval(n.value)for n in t.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
assert assign['HOST_ADAPTER_VERSION']=='hilbert-shared-parametric-family-native-admission-adapter-v2-unknown-prefix'
assert set(assign['ARITY'])=={'axiom','assumption','instantiate','eq_subst','mp'}
assert assign['ARITY']['mp']==2 and all(assign['ARITY'][k]==0 for k in assign['ARITY']if k!='mp')
assert assign['DEFAULT_LIMITS']=={'work':1000000,'depth':128,'selected':24,'edges':48,'string_bytes':1048576}
assert "'hypotheses': []"in s and "'fact_accepted': False"in s
assert "members = [rows[row] for row in sorted(rows)]"in s
assert "'selection_order': selection_order"in s
assert "'census_join_completed': status == 'COLLECTED_CONDITIONAL_DAG'"in s
assert "except _CallbackFailure as failure:\n        raise failure.error"in s
assert "except _Unfinished as unfinished:\n        return result('UNKNOWN',str(unfinished))"in s
patches={}
for direction,left,right in [('forward','',s),('inverse',s,'')]:
 pp=D/('collector-addition-'+direction+'.patch');pp.write_text(''.join(difflib.unified_diff(left.splitlines(keepends=True),right.splitlines(keepends=True),fromfile='target.py',tofile='target.py')))
 work=D/('patch-audit-'+direction);work.mkdir();(work/'target.py').write_text(left)
 r=subprocess.run(['patch','--batch','--fuzz=0','-p0','-i',str(pp)],cwd=work,capture_output=True,text=True)
 assert r.returncode==0 and (work/'target.py').read_text()==right,(r.stdout,r.stderr)
 patches[direction]=ref(pp)
assert ast.dump(ast.parse((D/'patch-audit-forward/target.py').read_text()),include_attributes=False)==ast.dump(t,include_attributes=False)
assert ast.dump(ast.parse((D/'patch-audit-inverse/target.py').read_text()),include_attributes=False)==ast.dump(ast.parse(''),include_attributes=False)
base=Path('/private/tmp/gcts-hilbert-shared-family-adapter-source-20261017/dependencies')
deps={'host_adapter':adapter,'context_checker':ref(base/'fresh_final_checker.py'),'logical_oracle':ref(base/'independent_checker.py'),
      'point_core':ref(base/'point_core.py'),'dynamic_graph':ref(base/'dynamic_graph.py'),
      'generic_miner_v3':ref('/private/tmp/gcts-interface-coupled-miner-source-20261017/receptor_family_miner_v3.py')}
source=ref(P)
checks=['Whole Source AST parse and compile without evaluation; only stdlib hashlib/json imports, no dispatcher.',
'No Source/project/helper/clock/test/model/scientific function executed by author.',
'Public Hilbert describe_host only; no adapter private _context or fabricated family/request.',
'Fresh admitted_context and independently decoded original catalogue recipe/model relation.',
'Native original five-rule argument/ordered-port dialect, no arithmetic generalize or channel4 schema relabel.',
'Whole actual selected list taken from current graph semantic_state, never caller-supplied proof/node route.',
'All selected/excluded native keys freshly rebuilt, command-checked, packet-compared and full identities merged.',
'Entire fixed+selected t/m/reference-count union independently compared to current native state.',
'Node order is ascending physical row while actual insertion order/index remains separately retained.',
'All ordered/repeated strictly prior reads preserve exact native formula code and literal source identity.',
'Unoccupied read rows deduplicate only with exact matching formula and remain occupiedFalse/factFalse.',
'All original Gamma occurrences retain index/order; selected assumptions remain actual primitive nodes.',
'Every selected sink exported without target filter; full all-port maps retain source rows/keys/preimages.',
'Caller provenance remains opaque; no engine generation/chronology/target proof from origin labels.',
'Native/callback/data/collision errors propagate; only private own finite bound or empty selected state is UNKNOWN.',
'UNKNOWN exposes no partial derivation/checked members and census_join_completedFalse.',
'Full host/current state/origin/census/qualification/checker theory compared before complete return.',
'Generic miner DAG field sets and rule argument shapes checked against exact resident miner3 Source.',
'Actual unified addition/inverse patches fuzz0, full raw+AST reconstruction exact.',
'Independent repaired adapter Source peer bound, no inherited runtime/geometry/shared consumer qualification.']
delta=put('Source-delta-v1.json',{'schema':'Hilbert-shared-family-selected-collector-addition-delta-v1','source_only':True,'parent_source':None,'source':source,'edits':[{'before':'','after':s}],'forward_patch':patches['forward'],'inverse_patch':patches['inverse'],'full_raw_forward_inverse':True,'whole_AST_forward_inverse':True,'actual_patch_F0_directions':2,'prior_sources_modified':False})
audit=put('static-audit-v1.json',{'schema':'Hilbert-shared-family-selected-collector-static-audit-v1','source_only':True,'scientific_calls':0,'module_evaluations':0,'project_functions_executed':0,'clock_calls':0,'py_compile_used':False,'compile_without_evaluation':True,'checks':checks,'direct_called_attributes':attrs,'actual_patch_F0_directions':2})
api=put('API-wire-v1.json',{'schema':'Hilbert-shared-family-selected-collector-API-v1','VERSION':assign['VERSION'],'source_only':True,'collect_derivation':'collect_derivation(*,graph,point_core,host_adapter,context_checker,logical_oracle,closed_inputs,qualification,prototype_census,origin,tick,limits=None)','inputs':{'graph':'Actual current authenticated sealed Hilbert graph; state is captured freshly inside collector. No saved state/proof/ordered donor node list input.','qualification':'Exact unchanged original Hilbert admitted context; Root-owned ClosedInputs/module Source guards remain required.','host_adapter':'Exact repaired public VERSIONv2-unknown-prefix and describe_host; no private helper consumed.','prototype_census':'Mandatory full prior exposed ID/preimage string pairs supplied by caller; selected/excluded packet exposures freshly merge. No inference of complete engine-private history.','origin':'Required builtin JSON dictionary, retained opaque; compact origin IDs recommended. No chronology/engine-produced/proof authority.','tick':'Original cumulative native Root endpoint. Own work/depth counters do not reset its clock/heap.'},'limits':assign['DEFAULT_LIMITS'],'own_limit_semantics':'Only finite collector work/depth/selected/read/string allowances return UNKNOWN. Original callback/native/membership/authority/collision/malformed errors propagate. On unfinished work derivation=None, checked_members empty, maps=None and census_join_completedFalse; partial request/state/census may remain raw unaccepted diagnostics.','derivation':{'schema':assign['DAG_SCHEMA'],'fields':['schema','host_binding','inputs','hypotheses','nodes','outputs','origin'],'nodes':'All actual selected nodes n<physicalRow> sorted by output row. Exact witness minus rule/formula forms arguments, all ordered/repeated native premise references retained.','hypotheses':'[]: selected assumptions remain primitive nodes with original indexed Gamma licenses. Full ordered Gamma occurrence map remains separately retained.','inputs':'One i<row> per actual unoccupied read row, only after literal/code agreement across readers; sharing ALLOW_SAME_EXACT_PRIOR_SOURCE, occupiedFalse/factFalse.','input_provenance_schema':'hilbert-collected-unoccupied-source-v1; exact current row/model_epoch/context_id/binding/state SHA and selected_key=None. Not a future adapter physical input-source binding.','outputs':'Every actual selected DAG sink o<row>, no target/formula/rule selection. Exact generic output three-field schema; maps mark occupied current point but factFalse.','origin':'Own collector/binding/state identity plus opaque caller_origin; all engine/proof claimsFalse.'},'result':{'schema':assign['RESULT_SCHEMA'],'statuses':['COLLECTED_CONDITIONAL_DAG','UNKNOWN'],'fields':['schema','version','status','reason','request','host','binding','state_sha256','current_state','derivation','derivation_sha256','checked_members','maps','checks','prototype_census','census_join_completed','work','flags'],'checked_members':'All selected members by row, full independently decoded recipe/current placement and distinct local primitive-check schema; no old arithmetic MEMBER receipt relabel.','maps':['selection_order','nodes','reads','inputs','outputs','context_occurrences'],'prototype_census':'Sorted full literal ID/preimage text pairs for supplied history plus every newly inspected recipe/prototype/aggregate placement. Complete only for declared successfully reconciled exposures, not full domain/global degree.'},'downstream':'Current generic miner3 accepts literal DAG wire/host. Root must still generate descriptors, fresh ordinary expand, independent4358 check, and Hilbert native adapter grounding using actual physical rows/source metadata. Arithmetic9f collector and arithmetic provider source schemas are not aliases. No consumer/engine activation in this module.','flags':assign['FLAGS']})
contract={'schema':'Hilbert-shared-family-selected-collector-Source-contract-v1','scope':'Hilbert-shared-family-selected-collector-Source','author':'/root/hilbert_advice_controls','source_only':True,'scientific_calls':0,'module_evaluations':0,'project_functions_executed':0,'clock_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'source':source,'sources':{'hilbert_selected_collector':source},'API':api,'delta':delta,'static_audit':audit,'dependencies':deps,'host_adapter_contract':ref(A/'Source-contract-v2.json'),'host_adapter_peer':ref(peer_path),'semantic_boundary':'Original admitted Hilbert catalogue/theory/ordered indexed Gamma/target/all24 boundary/root/exterior/target marks/formula codes/recipe indices/authority/model epoch remain unchanged. Arithmetic original17/input2 is separate. No graph mutation, global query/fallback enumeration or engine chronology is supplied by this collector.','generic_wire_compatibility':'Exact miner DAG schema and five-rule host argument syntax accepted by miner3 _Graph; full expansion/native admission downstream remains mandatory. Generic miner input validation is structural and never turns origin labels into proof authority.','cost_boundary':'Fresh existing static admission/independent wire construction/actual current selected+excluded packets/whole t-m/refcounts/input copies/census are fully charged to cumulative Root tick. Own finite ceilings are proposal collection bounds; no resource grant, runtime fit, target success or benefit claim.','remaining_gaps':['Hilbert-specific descriptor/physical receiver grounding and preference/continuation consumer remain separately reviewed composition work.','Current complete-domain/global priority/continuation/root rollback dynamic qualification stays separate from logical/point component checks.','Any automatically mined conditional fragment still requires source-ground and current receiver check; no selected-node count or closed DAG alone is a theorem certificate.'],'authorship_overlap':'Controls authored repaired host adapter and earlier arithmetic collector/shared consumer/provider; this is a separately named Hilbert collector, not its independent peer. Root owns integration/actuals; native Hilbert/context and generic independent checker authorship remains separate.','Review_ABI':{'schema':'Hilbert-shared-family-selected-collector-typed-Source-review-v1','scope':'Hilbert-shared-family-selected-collector-Source','source':source,'sources':{'hilbert_selected_collector':source},'source_contract':'EXACT_CURRENT_CONTRACT_PIN','source_only':True,'source_review_passed':'bool','scientific_calls':0,'scientific_acceptance':False,'reviewer_identity':'distinct from author; disclose common native/host/miner dependencies'}}
cr=put('Source-contract-v1.json',contract)
h=put('handoff-v1.json',{'schema':'Hilbert-shared-family-selected-collector-handoff-v1','source_only':True,'scientific_calls':0,'module_evaluations':0,'scientific_acceptance':False,'actual_execution_authorized':False,'source':source,'source_contract':cr,'API':api,'delta':delta,'static_audit':audit,'host_adapter_peer':contract['host_adapter_peer'],'Review_ABI':contract['Review_ABI']})
print(json.dumps({'handoff':h,'contract':cr,'Source':source,'API':api,'delta':delta,'audit':audit},indent=2))
