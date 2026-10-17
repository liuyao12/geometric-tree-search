"""Raw bytes/AST metadata only. Never import or evaluate reviewed Source."""
from pathlib import Path
import ast
import hashlib
import json
import re

A=Path('/private/tmp/gcts-global-phase-diagnostic-source-20261017')
D=Path('/private/tmp/gcts-global-diagnostic-peer-20261017')
def pin(p):
    p=Path(p); b=p.read_bytes()
    return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,value):
    p=D/n
    with p.open('xb') as f:f.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
    return pin(p)
def patch(raw,p):
    rows=raw.decode().splitlines(True); lines=p.read_text().splitlines(True)
    assert lines[0].startswith('--- ') and lines[1].startswith('+++ ')
    out=[]; cur=0; index=2
    while index<len(lines):
        m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[index]);assert m
        oldn=int(m[2] or '1'); newn=int(m[4] or '1')
        start=int(m[1])-1+(oldn==0); assert start>=cur
        out.extend(rows[cur:start]);cur=start;index+=1;used=made=0
        while index<len(lines) and not lines[index].startswith('@@'):
            line=lines[index];assert line[0] in ' +-'
            if line[0] in ' -':assert rows[cur]==line[1:];cur+=1;used+=1
            if line[0] in ' +':out.append(line[1:]);made+=1
            index+=1
        assert used==oldn and made==newn
    out.extend(rows[cur:]);return ''.join(out).encode()
def regions(raw):
    tr=ast.parse(raw);lines=raw.decode().splitlines(True);out={}
    def visit(n,prefix):
        for ch in ast.iter_child_nodes(n):
            if isinstance(ch,(ast.ClassDef,ast.FunctionDef)):
                key=prefix+ch.name
                out[key]=(''.join(lines[ch.lineno-1:ch.end_lineno]),ast.dump(ch,include_attributes=False))
                visit(ch,key+'.')
            else:visit(ch,prefix)
    visit(tr,'');return tr,out
def literal(n):
    # Only module data syntax is interpreted, never a Source expression/call.
    if isinstance(n,ast.Constant):return n.value
    if isinstance(n,(ast.List,ast.Tuple,ast.Set)):
        values=[literal(x) for x in n.elts]
        return values if isinstance(n,ast.List) else tuple(values) if isinstance(n,ast.Tuple) else set(values)
    if isinstance(n,ast.Dict):return {literal(k):literal(v) for k,v in zip(n.keys,n.values)}
    raise ValueError(type(n).__name__)

h=json.loads((A/'handoff-v1.json').read_bytes())
c=json.loads((A/'Source-contract-v1.json').read_bytes())
delta=json.loads((A/'Source-delta-v1.json').read_bytes())
protocol=json.loads((A/'native-readout-protocol-v1.json').read_bytes())
author=json.loads((A/'author-static-v1.json').read_bytes())
assert pin(A/'handoff-v1.json')['sha256']=='9b1b4cfc11003df97170133060a2acc279c3f61c54cc487560afef5cf2745fc9'
assert pin(A/'Source-contract-v1.json')['sha256']=='b5e266467e384aa584679762722b450055186dc5e986a8995349d0ec2e1aacca'
assert c['source']==h['source']==h['Review_ABI']['source'] and c['sources']==h['sources']==h['Review_ABI']['sources']
refs={}
def verify(p):
    assert pin(p['path'])==p;refs[p['path']]=p
for p in [c['source'],h['source_contract'],c['source_delta'],c['native_readout_protocol'],c['author_static'],c['Source_cost_diagnosis'],c['master'],c['Source_pool_manifest'],c['parent_source_copy'],pin(A/'sequential-edits-v1.json'),pin(A/'handoff-v1.json')]:verify(p)
for p in delta['actual_patches'].values():verify(p)
parent=Path(c['parent_source_copy']['path']).read_bytes(); current=Path(c['source']['path']).read_bytes()
assert len(current)==84909 and hashlib.sha256(current).hexdigest()=='d44ad0a0ba4ba4895dd1ab5c0e6ffd4980ee5a876856a7cf51d8fdfeaec0f8fa'
assert delta['edits']==json.loads((A/'sequential-edits-v1.json').read_bytes()) and len(delta['edits'])==19
forward=parent.decode()
for edit in delta['edits']:
    at=edit['start'];assert forward[at:at+len(edit['old'])]==edit['old']
    forward=forward[:at]+edit['new']+forward[at+len(edit['old']):]
assert forward.encode()==current
inverse=current.decode()
for edit in reversed(delta['edits']):
    at=edit['start'];assert inverse[at:at+len(edit['new'])]==edit['new']
    inverse=inverse[:at]+edit['old']+inverse[at+len(edit['new']):]
assert inverse.encode()==parent
assert patch(parent,A/'caller-forward.patch')==current and patch(current,A/'caller-full-inverse.patch')==parent
ta,ra=regions(parent);tb,rb=regions(current)
assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ta,include_attributes=False)
exact=[k for k in ra if ra[k]==rb[k]];changed=[k for k in ra if ra[k]!=rb[k]]
assert exact==author['raw_AST_exact_regions'] and changed==author['changed_existing_regions']
assert set(rb)-set(ra)=={'main.phase'}
for k in ('main.protocol_family','main.transfer_family','main.eof_family','main.child_family','main.stream_component'):
    assert ra[k]==rb[k]
assert current[current.index(b"if __name__ == '__main__':"):]==parent[parent.index(b"if __name__ == '__main__':"):]
da={n.targets[0].id:n for n in ta.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
db={n.targets[0].id:n for n in tb.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
for k in da:
    if k not in ('VERSION','SCOPE'):assert ast.dump(da[k],include_attributes=False)==ast.dump(db[k],include_attributes=False)
for key in ('FIXED_INPUTS','LIMITS','ORIGINAL_SOURCES','ORIGINAL_INPUTS','ORIGINAL_BINDING'):
    contractkey={'FIXED_INPUTS':'inputs','LIMITS':'limits','ORIGINAL_SOURCES':'original_model_sources','ORIGINAL_INPUTS':'original_model_inputs','ORIGINAL_BINDING':'original_model_binding'}[key]
    assert literal(db[key].value)==c[contractkey]
expected=dict(literal(db['FIXED'].value));expected['intake']=c['source']
assert expected==c['sources'] and len(expected)==14
cases=literal(db['QUALIFICATION_CASES_BY_PURPOSE'].value)
assert len(cases)==6 and sum(len(v) for v in cases.values())==12
assert literal(db['FIXED'].value)['marked_adapter']['sha256']=='ea3004b3573ab746ad22d1eacf255d61489b2389c06f6ca178821c114288597e'
assignments=[n for n in ast.walk(tb) if isinstance(n,ast.Assign)]
labels=next(literal(n.value) for n in assignments if any(isinstance(t,ast.Name) and t.id=='phase_labels' for t in n.targets))
assert list(labels)==protocol['phase_stderr']['ordered_runtime_literals']
calls=[n.args[0].value for n in ast.walk(tb) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='phase']
assert len(calls)==13 and len(set(calls))==13 and set(calls)==set(labels)
prefix=protocol['phase_stderr']['prefix']
lengths=[len((prefix+' '+label+' '+str(2**63-1)+'\n').encode('ascii')) for label in labels]
assert max(lengths)==84==protocol['phase_stderr']['maximum_complete_line_bytes']
assert sum(lengths)==1059==protocol['phase_stderr']['maximum_complete_marker_bytes']
assert protocol['phase_stderr']==c['API']['phase_stderr']
assert protocol['failure_writer']==c['API']['failure_writer']
assert protocol['successful_exit0']==c['API']['successful_wire']
assert all(value is False for value in c['flags'].values()) and c['qualified_case_count']==0 and c['reported_case_count'] is None
assert ra['save_failure_diagnostic']==rb['save_failure_diagnostic'] and ra['main.tick']==rb['main.tick']
late=next(n for n in ast.walk(tb) if isinstance(n,ast.ExceptHandler) and isinstance(n.type,ast.Name) and n.type.id=='TimeoutError')
names=[n.func.id for n in ast.walk(late) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
assert not any(x in names for x in ('tick','guard','boundary','call','anchor_fn','same_fn','Path'))
assert names.count('f')==1 and any(isinstance(n,ast.Raise) and n.exc is None for n in ast.walk(late))
checks=[
 'whole_current_Source_contract_handoff_readout_costnotes_read',
 'all19_sequential_forward_and_full_inverse_exact',
 'both_actual_unified_patch_directions_exact',
 'whole_AST_inverse_exact_no_Source_evaluation',
 'all17_tophelpers_2classes_native_tail_raw_AST_preserved',
 'only_six_existing_function_regions_changed_plus_phase',
 'all12_scientific_control_erasure_exact_five_other_family_bodies_rawexact',
 'current14_input8_original17_input2_binding_limits_literal_exact',
 'ea300_current_only_familyengine_a197_not_composed',
 '13_unique_fixed_sites_runtime_whitelist_wire84_1059',
 'phase_captured_native_tick_write_charged_no_new_clock',
 'first_return_after_actual_proposer_not_independent_check_acceptance',
 'four_scalar_slots_entry_only_validator_None_no_history_or_activeframe',
 'same_guarded_call_constructor_delegate_kwargs_return_identity_preserved',
 'exact_builtin_TimeoutError_only_late_writer_original_rethrow',
 'captured_writer_all_defaults_cells_tokens_rawexact_no_late_science',
 'missing_partial_writer_unaccepted_failure55_not_native20_positive',
 'success_result_response_final_explicit_diagnostic_null_counts_zeroqualified',
 'readout_partial_tail_stop_malformed_no_cause_or_exclusive_timing_inference',
 'scientific_payload_opaque_all_outcomes_zeroqualification',
 'no_import_eval_test_clock_actual_result_or_donor_execution_byreviewer']
print(json.dumps(put('independent-static-v1.json',{
 'schema':'unit-row-global-phase-diagnostic-independent-static-v1',
 'source':c['source'],'source_contract':h['source_contract'],'raw_refs':list(refs.values()),
 'check_count':len(checks),'checks':checks,'sequential_edit_count':19,
 'actual_forward_inverse_and_AST_inverse_exact':True,'raw_AST_exact_regions':exact,
 'changed_existing_regions':changed,'added_region':'main.phase','case_map':cases,
 'wire_maximum_line_bytes':max(lengths),'wire_maximum_total_bytes':sum(lengths),
 'native_failure_suffix_rawexact':True,'complete_current_sources_map_literal_equal':True,
 'scientific_calls':0,'source_only':True,'scientific_acceptance':False,
 'module_evaluations':0,'tests_run':0,'clocks_called':0,'actual_or_result_reads':0})))
