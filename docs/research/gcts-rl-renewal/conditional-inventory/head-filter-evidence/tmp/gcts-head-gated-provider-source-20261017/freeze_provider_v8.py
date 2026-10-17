"""Source-only authoring: bytes, AST, metadata and text patches; no evaluation."""
import ast
import difflib
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

H = Path('/private/tmp/gcts-head-gated-provider-source-20261017')
P = Path('/private/tmp/gcts-observed-receptor-provider-source-20261017')
G = Path('/private/tmp/gcts-coarse-head-plan-marks-source-20261017')

def raw(p):
    p = Path(p)
    assert not getattr(p.stat(), 'st_flags', 0) & 0x40000000
    return p.read_bytes()

def pin(p):
    b = raw(p)
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def write(name, b):
    p = H / name
    if isinstance(b, str): b = b.encode()
    with p.open('xb') as f: f.write(b)
    return pin(p)

def save(name, v):
    return write(name, json.dumps(v, sort_keys=True, indent=2) + '\n')

parent = P / 'receptor_transfer_physical_provider_v7.py'
a = raw(parent)
s = a.decode()
edits = []

def edit(label, before, after):
    global s
    assert s.count(before) == 1, (label, s.count(before))
    i = s.index(before)
    edits.append({'label': label, 'start': i, 'old': before, 'new': after})
    s = s[:i] + after + s[i+len(before):]

edit('own_VERSION', "VERSION = 'receptor-family-observed-receptor-transfer-provider-v7'",
     "VERSION = 'receptor-family-observed-receptor-transfer-provider-v8-head-gated'")
edit('explicit_gate_protocol',
     "MEMBERSHIP_VERSION = 'shared-bounded-six-rule-language-v2'\n",
     "MEMBERSHIP_VERSION = 'shared-bounded-six-rule-language-v2'\n"
     "HEAD_GATE_VERSION = 'receptor-family-coarse-formula-head-plan-marks-v1'\n"
     "HEAD_GATE_SCHEMA = 'receptor-family-coarse-head-plan-check-v1'\n"
     "HEAD_GATE_PREFIX_SCHEMA = 'receptor-family-provider-plan-head-gate-prefix-v1'\n"
     "HEAD_GATE_FLAGS = {'advisory_cluster_plan_only': True, 'native_validation_required': True,\n"
     "    'native_state_modified': False, 'native_membership_accepted': False, 'point_union_accepted': False,\n"
     "    'base_candidate_pruning_accepted': False, 'degree_or_EOF_accepted': False,\n"
     "    'engine_activated': False, 'proof_accepted': False, 'universal_lemma_accepted': False,\n"
     "    'runtime_qualified': False, 'speedup_claimed': False}\n")

helper = '''def _check_plan_head_gate(*, descriptor, shape, assignment, plan, head_gate_module,
                          gate_checks, accounting, work):
    """A completed coarse conflict skips only this advisory physical plan."""
    work.step()
    row_assignment = {'schema': ROW_SCHEMA,
        'node_rows': [[n['id'], assignment[('node', n['id'])]] for n in shape['nodes']],
        'input_rows': [[pid, assignment[('input', pid)]] for pid in shape['inputs']]}
    entry = {'plan_index': plan['plan_index'], 'record_index': plan['record_index'],
        'output_port': plan['output_port'], 'request': None, 'receipt': None, 'outcome': 'PENDING'}
    gate_checks.append(entry)
    expected = {'descriptor': work.copy(descriptor), 'layout_shape': work.copy(shape),
        'row_assignment': work.copy(row_assignment), 'limits': work.copy(head_gate_module.DEFAULT_LIMITS)}
    entry['request'] = expected
    accounting['head_gate_calls'] += 1
    receipt = head_gate_module.check_plan_heads(descriptor=expected['descriptor'],
        layout_shape=expected['layout_shape'], row_assignment=expected['row_assignment'], tick=work.step)
    # Preserve every literal successful return even if the provider's subsequent
    # charged copy/validation reaches its own limit. PENDING is never authority.
    entry['receipt'] = receipt
    accounting['head_gate_receipts_returned'] += 1
    receipt = work.copy(receipt);entry['receipt'] = receipt
    fields(receipt, ('schema','version','status','reason','scope','request','request_sha256',
        'planning_channel','gate_completed','advisory_plan_rejected','requirements','known_marks',
        'conflicts','unknown_requirement_indices','work','flags'), 'HEAD_GATE_PROTOCOL')
    require(receipt['schema'] == HEAD_GATE_SCHEMA and receipt['version'] == HEAD_GATE_VERSION
            and receipt['status'] in ('HEAD_CONFLICT','NO_KNOWN_HEAD_CONFLICT','UNKNOWN')
            and receipt['scope'] == 'THIS_PHYSICAL_CLUSTER_PLAN_ONLY'
            and type(receipt['planning_channel']) is int and receipt['planning_channel'] == 5,
            'HEAD_GATE_PROTOCOL', 'exact fresh advisory gate protocol only')
    require(type(receipt['flags']) is dict and set(receipt['flags']) == set(HEAD_GATE_FLAGS)
            and all(receipt['flags'][k] is v for k, v in HEAD_GATE_FLAGS.items()),
            'HEAD_GATE_PROTOCOL', 'no native or base-candidate authority')
    fields(receipt['work'], ('steps','limits'), 'HEAD_GATE_PROTOCOL')
    require(type(receipt['work']['steps']) is int and receipt['work']['steps'] >= 0
            and canonical(receipt['work']['limits']) == canonical(expected['limits'])
            and receipt['work']['steps'] <= expected['limits']['work'],
            'HEAD_GATE_PROTOCOL', 'existing gate own bounds inside same provider/native work')
    if receipt['request'] is not None:
        require(canonical(receipt['request']) == canonical(expected),
                'HEAD_GATE_PROTOCOL', 'whole descriptor/topology/physical rows/default limits join')
    else:
        require(receipt['status'] == 'UNKNOWN' and receipt['request_sha256'] is None,
                'HEAD_GATE_PROTOCOL', 'early gate UNKNOWN is never a partial conflict')
    if receipt['request_sha256'] is not None:
        require(receipt['request'] is not None and receipt['request_sha256'] == ascii_digest(expected),
                'HEAD_GATE_PROTOCOL', 'exact original ASCII gate request digest')
    require(all(type(receipt[k]) is list for k in
                ('requirements','known_marks','conflicts','unknown_requirement_indices')),
            'HEAD_GATE_PROTOCOL', 'literal full planning receipt lists')
    if receipt['status'] == 'UNKNOWN':
        require(receipt['gate_completed'] is False and receipt['advisory_plan_rejected'] is False
                and all(receipt[k] == [] for k in
                    ('requirements','known_marks','conflicts','unknown_requirement_indices')),
                'HEAD_GATE_PROTOCOL', 'no partial comparison or negative authority from UNKNOWN')
        accounting['head_gate_unknown'] += 1
    else:
        conflict = receipt['status'] == 'HEAD_CONFLICT'
        require(receipt['gate_completed'] is True and receipt['advisory_plan_rejected'] is conflict
                and receipt['reason'] is None and receipt['request'] is not None
                and receipt['request_sha256'] == ascii_digest(expected)
                and bool(receipt['conflicts']) is conflict,
                'HEAD_GATE_PROTOCOL', 'only complete exact current-plan conflict may skip')
        if conflict:
            accounting['head_gate_conflicting_plans'] += 1
            entry['outcome'] = 'SKIP_THIS_PHYSICAL_PLAN'
            return True
        accounting['head_gate_no_known_conflict'] += 1
        if receipt['unknown_requirement_indices']:
            accounting['head_gate_absent_head_passes'] += 1
    accounting['head_gate_downstream_assignments'] += 1
    entry['outcome'] = 'PASS_TO_OBSERVED_MATCHING'
    return False


'''
edit('new_checked_advisory_gate_helper', 'def build_family_batch(*, language, base_semantics, marked_semantics, producer,\n',
     helper + 'def build_family_batch(*, language, base_semantics, marked_semantics, producer,\n')
edit('required_head_gate_injection',
     '                       expansion_checker, host_adapter, membership_module, residual_policy,\n',
     '                       expansion_checker, host_adapter, membership_module, residual_policy, head_gate_module,\n')
edit('gate_literal_receipt_storage',
     '    plans, physical, record_allocations = [], [], []\n',
     '    plans, physical, record_allocations, gate_checks = [], [], [], []\n')
edit('separate_gate_denominators',
     "        'checked_instances': 0, 'duplicate_instances': 0, 'offered_instances': 0}\n",
     "        'checked_instances': 0, 'duplicate_instances': 0, 'offered_instances': 0,\n"
     "        'head_gate_calls': 0, 'head_gate_receipts_returned': 0, 'head_gate_conflicting_plans': 0,\n"
     "        'head_gate_no_known_conflict': 0, 'head_gate_unknown': 0,\n"
     "        'head_gate_absent_head_passes': 0, 'head_gate_downstream_assignments': 0}\n")
edit('exact_required_gate_version',
     '                and residual_policy.VERSION == RESIDUAL_POLICY_VERSION,\n',
     '                and residual_policy.VERSION == RESIDUAL_POLICY_VERSION\n'
     '                and head_gate_module.VERSION == HEAD_GATE_VERSION\n'
     '                and head_gate_module.SCHEMA == HEAD_GATE_SCHEMA,\n')
edit('post_materialization_pre_matching_both_modes',
     "            fid = record['family_id'];observed = plan['observed_receptors']\n"
     "            attempt = {'plan_index': plan['plan_index'], 'observed_receptors': observed,\n",
     "            fid = record['family_id'];observed = plan['observed_receptors']\n"
     "            if _check_plan_head_gate(descriptor=record['descriptor'], shape=shape, assignment=assignment,\n"
     '                    plan=plan, head_gate_module=head_gate_module, gate_checks=gate_checks,\n'
     '                    accounting=accounting, work=work):\n'
     '                continue\n'
     "            attempt = {'plan_index': plan['plan_index'], 'observed_receptors': observed,\n")
edit('nested_versioned_full_gate_prefix',
     "                'record_allocations': record_allocations, 'plans': plans}, 'accounting': accounting,\n",
     "                'record_allocations': record_allocations, 'plans': plans,\n"
     "                'head_gate': {'schema': HEAD_GATE_PREFIX_SCHEMA, 'module_version': HEAD_GATE_VERSION,\n"
     "                    'checks': gate_checks}}, 'accounting': accounting,\n")
b = s.encode()
t = ast.parse(b)
compile(b, '<head-gated-provider-Source-only>', 'exec', dont_inherit=True)
source = write('receptor_transfer_physical_provider_v8.py', b)
f = a.decode()
for e in edits:
    i=e['start'];assert f[i:i+len(e['old'])] == e['old']
    f=f[:i]+e['new']+f[i+len(e['old']):]
assert f == s
for e in reversed(edits):
    i=e['start'];assert f[i:i+len(e['new'])] == e['new']
    f=f[:i]+e['old']+f[i+len(e['new']):]
assert f.encode() == a
assert ast.dump(ast.parse(f), include_attributes=False) == ast.dump(ast.parse(a), include_attributes=False)

def patches(name, before, after):
    out = {}
    for label, x, y in [('forward', before, after), ('full-inverse', after, before)]:
        ref = write(name+'-'+label+'.patch', ''.join(difflib.unified_diff(
            x.decode().splitlines(True), y.decode().splitlines(True), fromfile='before', tofile='after')))
        with tempfile.TemporaryDirectory(dir=str(H)) as td:
            target=Path(td)/'target.py';target.write_bytes(x)
            r=subprocess.run(['/usr/bin/patch','--batch','-F0',str(target),'-i',ref['path']],cwd=td,capture_output=True)
            assert r.returncode == 0 and target.read_bytes() == y
        out[label] = ref
    return out

ps = patches('provider-v7-to-v8', a, b)
parent_delta = json.loads(raw(P/'Source-delta-v7.json'))
original_ref = parent_delta['whole_v3_parent_source'];original = raw(original_ref['path'])
all_edits = parent_delta['whole_v3_edits'] + edits
f = original.decode()
for e in all_edits:
    i=e['start'];assert f[i:i+len(e['old'])] == e['old']
    f=f[:i]+e['new']+f[i+len(e['old']):]
assert f == s
for e in reversed(all_edits):
    i=e['start'];assert f[i:i+len(e['new'])] == e['new']
    f=f[:i]+e['old']+f[i+len(e['new']):]
assert f.encode() == original
whole_patches = patches('parent-v3-to-head-gated-v8', original, b)
delta = save('Source-delta-v8.json', {
    'schema':'receptor-family-head-gated-provider-Source-delta-v8','parent_source':pin(parent),'source':source,
    'edits':edits,'patches':ps,'whole_raw_inverse_exact':True,'whole_AST_inverse_exact':True,
    'actual_patch_both_directions_F0_exact':True,'whole_v3_parent_source':original_ref,
    'whole_v3_edits':all_edits,'whole_v3_patches':whole_patches,
    'source_only':True,'scientific_calls':0,'scientific_acceptance':False})

def regions(data):
    lines=data.decode().splitlines(True);out={}
    def walk(nodes,prefix=''):
        for n in nodes:
            if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
                name=prefix+n.name
                out[name]=(''.join(lines[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False))
                walk(n.body,name+'.')
    walk(ast.parse(data).body)
    return out
ra,rb=regions(a),regions(b)
unchanged=[k for k in ra if ra[k]==rb[k]]
assert [k for k in ra if ra[k]!=rb[k]] == ['build_family_batch']
assert set(rb)-set(ra) == {'_check_plan_head_gate'}
def constants(data):
    return {n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(data).body
            if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
ca,cb=constants(a),constants(b)
assert [k for k in ca if ca[k]!=cb[k]] == ['VERSION']
gc=constants(raw(G/'coarse_formula_head_plan_marks_v1.py'))
assert gc['VERSION']==cb['HEAD_GATE_VERSION'] and gc['SCHEMA']==cb['HEAD_GATE_SCHEMA'] and gc['FLAGS']==cb['HEAD_GATE_FLAGS']
assert cb['DEFAULT_LIMITS']==ca['DEFAULT_LIMITS'] and cb['FLAGS']==ca['FLAGS']
report_fields=request_fields=None
for n in ast.walk(t):
    if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Dict):
        if n.targets[0].id=='report':report_fields=[k.value for k in n.value.keys]
        if n.targets[0].id=='input_request':request_fields=[k.value for k in n.value.keys]
parent_api=json.loads(raw(P/'API-wire-v7.json'))
assert report_fields==parent_api['report_fields'] and request_fields==parent_api['request_fields']
audit=save('static-audit-v8.json', {
    'schema':'receptor-family-head-gated-provider-static-v8','source':source,'source_delta':delta,
    'checks':{'9_declared_raw_edits_whole_raw_AST_inverse':len(edits)==9,
        'four_actual_patch_directions_F0_exact':True,'all_old_constants_except_VERSION_exact':True,
        'only_build_family_batch_changed_new_gate_helper':True,'all_original_tophelpers_raw_AST_exact':True,
        'DEFAULT_LIMITS_FLAGS_report26_request6_and_bare_batch_unchanged':True,
        'all_plan_materialization_and_record_quota_code_raw_exact':True,
        'gate_after_attempted_plan_count_before_inference_both_modes':True,
        'no_GATE_call_in_structural_materialization_or_native_preflight':True,
        'no_new_exception_catch_native_membership_census_fallback_engine_calls':True,
        'literal_gate_return_retained_before_charged_copy_or_validation':True,
        'gate_flags_protocol_default_limits_exact_to7595':True,
        'AST_compile_without_evaluation':True},
    'unchanged_named_regions':unchanged,'added_named_regions':['_check_plan_head_gate'],
    'source_only':True,'scientific_calls':0,'project_module_evaluated':False,'scientific_acceptance':False})
api=dict(parent_api)
api.update(schema='receptor-family-head-gated-provider-API-v8',version=cb['VERSION'],
    signature="build_family_batch(*,language,base_semantics,marked_semantics,producer,expansion_checker,host_adapter,membership_module,residual_policy,head_gate_module,mined,state,decision,tick,limits=None,matching_mode='VISIBLE_RECEPTOR')")
api['head_gate_integration']={
    'required_module':pin(G/'coarse_formula_head_plan_marks_v1.py'),'version':cb['HEAD_GATE_VERSION'],
    'receipt_schema':cb['HEAD_GATE_SCHEMA'],'provider_report_schema':cb['RESULT_SCHEMA'],
    'wire_revision':'Existing report schemaV2/top26/request6 and bare7 batch remain exact; new report.versionV8 and nested head-gate-prefix schema are explicit. No inherited native receipt is normalized or relabelled.',
    'placement':'Common mode-independent structural plan fully materialized first. Per-plan attempted_assignments increment precedes gate; gate precedes observed matching and residual enumeration for BOTH modes.',
    'request':'Full descriptor, topology-only _layout shape, actual input/node row map, and exact existing gate DEFAULT_LIMITS. No source/current substitution or concrete receiver formula is supplied to the gate. Caller pins/authenticates/seals22 executable Sources separately from original semantic17/input2.',
    'retained_prefix':{'path':'report.physical_assignment_plan.head_gate',
        'fields':['schema','module_version','checks'],'schema':cb['HEAD_GATE_PREFIX_SCHEMA'],
        'each_check':['plan_index','record_index','output_port','request','receipt','outcome'],
        'outcomes':['PENDING','SKIP_THIS_PHYSICAL_PLAN','PASS_TO_OBSERVED_MATCHING']},
    'literal_receipt_and_exact_join':'Every successful raw gate return retained BEFORE subsequent charged provider copy/validation, then replaced by exact owned copied receipt. Full request and original ASCII digest join whenever supplied; early gate UNKNOWN may have null internal request/digest, while the provider check entry retains its full supplied request. PENDING/partial validation has no skip authority.',
    'skip':'ONLY completed HEAD_CONFLICT with nonempty full conflicts, exact request/digest and advisory flags skips THIS physical plan. No whole family/binding-domain/native candidate/receiver/global model exclusion.',
    'pass':'NO_KNOWN_HEAD_CONFLICT, including absent meta-head requirements, and gate-own UNKNOWN both pass to unchanged downstream matching/independent expansion/native membership/full point union. Gate status is not mathematical admission.',
    'counters':['head_gate_calls','head_gate_receipts_returned','head_gate_conflicting_plans','head_gate_no_known_conflict','head_gate_unknown','head_gate_absent_head_passes','head_gate_downstream_assignments'],
    'cost_errors':'Same provider own1m/depth128 and original native20/512 externally. Gate existing100k ownwork/depth128/input1MiB/4096requirements caps are unchanged reviewed module defaults; every gate step calls provider work.step/native tick cumulatively. Gate-own UNKNOWN passes; provider-own budget stops whole provider as before. PlanHeadError/native/callback/guard/allunexpected errors propagate unchanged; no catch added.',
    'census':'All original preflight/native/collision ledger code raw exact. Gate builds no native tile and exposes no omitted prototype. Full earlier exposure census still returned even with skipped/no-offer/UNKNOWN prefixes.',
    'planning_channel':'Channel5 only in advisory gate receipts, never added to native state/marking/point union.'}
api_ref=save('API-wire-v8.json',api)
C={'schema':'receptor-family-head-gated-provider-Source-contract-v8',
    'scope':'receptor-family-head-gated-provider-Source','author_identity':'/root/hilbert_advice_controls',
    'authorship_overlap':'Reviewer must disclose shared native ancestry. Author owns parent provider7/host4bd6/consumer and prior kernel/caller work; Arithmetic owns standalone7595 gate, Diagnosis its distinct peer and engine successor. This author packet is not own independent review.',
    'source':source,'sources':{'provider':source},'version':cb['VERSION'],'API':api_ref,
    'source_delta':delta,'static_audit':audit,'parent_source':pin(parent),
    'operative_parent_contract':pin(P/'Source-contract-v7.json'),
    'parent_distinct_peer':pin('/private/tmp/gcts-observed-receptor-provider-peer-20261017/typed-Source-review-v7.json'),
    'gate_source':pin(G/'coarse_formula_head_plan_marks_v1.py'),
    'gate_contract':pin(G/'Source-contract-v1.json'),
    'gate_API':pin(G/'API-wire-v1.json'),
    'gate_theory':pin(G/'design-and-proof-v1.json'),
    'gate_distinct_peer':pin('/private/tmp/gcts-coarse-head-plan-marks-peer-20261017/typed-Source-review-v1.json'),
    'master':pin('/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md'),
    'operative_change':api['head_gate_integration'],
    'unchanged':'Original semantic17/input2 epoch, theory/Gamma/target/24rows/B12N44/frozen marking and all native candidate semantics/global scheduler/complete fallback/owned rollback untouched. Shared finite structural allocation, matching modes/residual policy/full ordinary expansion4358/primitive5d1f/fullpoint4bd6 and exposure census unchanged except declared advisory pre-match gate/counters.',
    'human_heuristic_and_conformance_limits':['Human-designed necessary fixed-head obstruction for an exact supported cluster plan, conditional on full valid downstream typed/capture-safe instantiation; not learned pruning or universal generalized lemma.',
        'Neither shared heads nor gate UNKNOWN prove a native member, compatible union, actual fact, degree/EOF, viable branch, proof or useful transfer.',
        'Finite structural/matching/instance caps remain incomplete advisory prefixes. Gate counts may change actual processed denominators and error/tick prefixes; no nth-callback/timing/output equivalence, speedup or fit claim.',
        'Root must freeze a fresh22-source current map, reviewed provider/engine/helper/caller/readout composition and separate once/native grant. No previous actual qualification is inherited.'],
    'original_semantic_epoch_rebased':False,'native_point_channel5_activated':False,
    'limits':cb['DEFAULT_LIMITS'],'native_budget_increased':False,
    'source_only':True,'scientific_calls':0,'project_module_evaluated':False,
    'actual_result_proofword_donor_reads':False,'scientific_acceptance':False,'runtime_qualified':False,
    'actual_execution_authorized':False}
C['Review_ABI']={'schema':'receptor-family-head-gated-provider-typed-Source-review-v8',
    'scope':C['scope'],'author_identity':C['author_identity'],'source':source,'sources':C['sources'],
    'source_contract':'current capsule','source_only':True,'scientific_calls':0,'scientific_acceptance':False}
cref=save('Source-contract-v8.json',C)
href=save('handoff-v8.json',{'schema':'receptor-family-head-gated-provider-handoff-v8',
    'source':source,'source_contract':cref,'API':api_ref,'source_delta':delta,'static_audit':audit,
    'actual_patches':ps,'whole_v3_patches':whole_patches,
    'Review_ABI':dict(C['Review_ABI'],source_contract=cref),
    'provider_VERSION':cb['VERSION'],'report_schema':cb['RESULT_SCHEMA'],
    'report_fields':report_fields,'request_fields':request_fields,
    'head_gate_prefix':api['head_gate_integration']['retained_prefix'],
    'required_kwarg':'head_gate_module','gate_source':C['gate_source'],
    'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False})
print(json.dumps({'source':source,'contract':cref,'API':api_ref,'delta':delta,'audit':audit,'handoff':href},sort_keys=True))
