"""Source bytes/AST/metadata authoring only; never evaluate provider code."""
import ast
import copy
import difflib
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

H = Path('/private/tmp/gcts-observed-receptor-provider-source-20261017')

def raw(p):
    p = Path(p)
    assert not getattr(p.stat(), 'st_flags', 0) & 0x40000000
    return p.read_bytes()

def pin(p):
    b = raw(p)
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def write(name, b):
    p = H / name
    if isinstance(b, str):
        b = b.encode()
    if p.exists():
        assert raw(p) == b
        return pin(p)
    with p.open('xb') as f:
        f.write(b)
    return pin(p)

def save(name, v):
    return write(name, json.dumps(v, sort_keys=True, indent=2) + '\n')

parent_path = H / 'receptor_transfer_physical_provider_v5.py'
a = raw(parent_path)
s = a.decode()
edits = []

def edit(label, old, new):
    global s
    assert s.count(old) == 1, (label, s.count(old))
    i = s.index(old)
    edits.append({'label': label, 'start': i, 'old': old, 'new': new})
    s = s[:i] + new + s[i + len(old):]

edit('own_VERSION', "VERSION = 'receptor-family-observed-receptor-transfer-provider-v5'",
     "VERSION = 'receptor-family-observed-receptor-transfer-provider-v6'")
edit('planning_allocation_state',
     '    plans, physical = [], []\n',
     '    plans, physical, record_allocations = [], [], []\n'
     '    allocated_record_count = record_trial_quota = 0\n')
edit('mode_independent_equal_record_quota',
     '        # This entire plan is built before any mode-dependent receptor inference.\n',
     '        # Each eligible record receives the same finite structural trial share.\n'
     '        # Unused shares/remainders are not reassigned using matching outcomes.\n'
     "        allocated_record_count = min(work.limits['records'], len(mined['families']))\n"
     "        record_trial_quota = work.limits['row_trials'] // allocated_record_count if allocated_record_count else 0\n"
     "        record_allocations = [{'record_index': i, 'row_trial_quota': record_trial_quota,\n"
     "            'row_trials': 0, 'planned_assignments': 0, 'status': 'NOT_STARTED',\n"
     "            'bounded_reason': None} for i in range(allocated_record_count)]\n"
     '        # This entire plan is built before any mode-dependent receptor inference.\n')
edit('per_record_accounting_start',
     "                    raise _AssignmentPrefix('OWN_RECORD_PLANNING_PREFIX')\n                fields(record,",
     "                    raise _AssignmentPrefix('OWN_RECORD_PLANNING_PREFIX')\n"
     "                allocation = record_allocations[record_index]\n"
     "                allocation['status'] = 'SOURCE_GROUND_CHECKING'\n"
     "                fields(record,")
edit('source_ground_UNKNOWN_accounting',
     "                if ground['status'] == 'UNKNOWN':continue\n",
     "                if ground['status'] == 'UNKNOWN':\n"
     "                    allocation['status'] = 'SOURCE_GROUND_UNKNOWN'\n"
     "                    allocation['bounded_reason'] = 'SOURCE_GROUND_UNKNOWN'\n"
     '                    continue\n')
edit('source_check_UNKNOWN_accounting',
     '                if not _ready_checked(checked, ground):continue\n',
     '                if not _ready_checked(checked, ground):\n'
     "                    allocation['status'] = 'SOURCE_CHECK_UNKNOWN'\n"
     "                    allocation['bounded_reason'] = 'SOURCE_CHECK_UNKNOWN'\n"
     '                    continue\n')
old_start = "                for output in origin['outputs']:\n"
start = s.index(old_start, s.index('# Each eligible record'))
end = s.index('            planning_complete = True\n', start)
old_loop = s[start:end]
assert old_loop.count('                            plans.append(item)\n') == 1
assert old_loop.count('                            work.trial();current = dict(assignment);current[key] = row\n') == 1
new_loop = old_loop.replace(
    '                            plans.append(item)\n',
    "                            plans.append(item);allocation['planned_assignments'] += 1\n")
new_loop = new_loop.replace(
    '                            work.trial();current = dict(assignment);current[key] = row\n',
    "                            if allocation['row_trials'] >= record_trial_quota:\n"
    "                                raise _AssignmentPrefix('OWN_PER_RECORD_PHYSICAL_ROW_TRIAL_PREFIX')\n"
    "                            work.trial();allocation['row_trials'] += 1\n"
    '                            current = dict(assignment);current[key] = row\n')
new_loop = ("                allocation['status'] = 'ENUMERATING_STRUCTURAL_PREFIX'\n"
            '                try:\n' + ''.join('    ' + line for line in new_loop.splitlines(True)) +
            '                except _AssignmentPrefix as error:\n'
            "                    allocation['status'] = 'BOUNDED_STRUCTURAL_PREFIX'\n"
            "                    allocation['bounded_reason'] = str(error)\n"
            '                else:\n'
            "                    allocation['status'] = 'STRUCTURAL_ENUMERATION_FINISHED'\n")
edit('nested_record_prefix_stop_and_accounting', old_loop, new_loop)
edit('whole_plan_prefix_completion',
     '            planning_complete = True\n',
     "            planning_complete = all(a['status'] == 'STRUCTURAL_ENUMERATION_FINISHED' for a in record_allocations)\n"
     '            if not planning_complete:\n'
     "                planning_reason = 'EQUAL_PER_RECORD_STRUCTURAL_PLAN_PREFIX'\n"
     '                reason = planning_reason\n')
edit('full_record_quota_denominators',
     "            'offers': offers, 'physical_assignment_plan': {'policy': 'MODE_INDEPENDENT_STRUCTURAL_PREFIX',\n"
     "                'complete_within_declared_limits': planning_complete, 'bounded_reason': planning_reason,\n"
     "                'plans': plans}, 'accounting': accounting,\n",
     "            'offers': offers, 'physical_assignment_plan': {'policy': 'MODE_INDEPENDENT_EQUAL_PER_RECORD_STRUCTURAL_PREFIX',\n"
     "                'complete_within_declared_limits': planning_complete, 'bounded_reason': planning_reason,\n"
     "                'allocated_record_count': allocated_record_count, 'row_trials_per_record': record_trial_quota,\n"
     "                'unallocated_remainder': work.limits['row_trials'] - allocated_record_count * record_trial_quota,\n"
     "                'record_allocations': record_allocations, 'plans': plans}, 'accounting': accounting,\n")
b = s.encode()
t = ast.parse(b)
compile(b, '<providerV6-Source-only>', 'exec', dont_inherit=True)
source = write('receptor_transfer_physical_provider_v6.py', b)
f = a.decode()
for e in edits:
    i = e['start']
    assert f[i:i+len(e['old'])] == e['old']
    f = f[:i] + e['new'] + f[i+len(e['old']):]
assert f == s
for e in reversed(edits):
    i = e['start']
    assert f[i:i+len(e['new'])] == e['new']
    f = f[:i] + e['old'] + f[i+len(e['new']):]
assert f.encode() == a
assert ast.dump(ast.parse(f), include_attributes=False) == ast.dump(ast.parse(a), include_attributes=False)

def patches(name, x, y):
    out = {}
    for label, before, after in [('forward', x, y), ('full-inverse', y, x)]:
        ref = write(name + '-' + label + '.patch', ''.join(difflib.unified_diff(
            before.decode().splitlines(True), after.decode().splitlines(True), fromfile='before', tofile='after')))
        with tempfile.TemporaryDirectory(dir=str(H)) as td:
            target = Path(td) / 'before'
            target.write_bytes(before)
            result = subprocess.run(['/usr/bin/patch', '--batch', '-F0', str(target), '-i', ref['path']],
                                    cwd=td, capture_output=True)
            assert result.returncode == 0 and target.read_bytes() == after
        out[label] = ref
    return out

im = patches('provider-v5-to-v6', a, b)
prior_delta = json.loads(raw(H / 'Source-delta-v5.json'))
original = raw(prior_delta['parent_source']['path'])
full_edits = prior_delta['edits'] + edits
f = original.decode()
for e in full_edits:
    i = e['start']; assert f[i:i+len(e['old'])] == e['old']
    f = f[:i] + e['new'] + f[i+len(e['old']):]
assert f == s
for e in reversed(full_edits):
    i = e['start']; assert f[i:i+len(e['new'])] == e['new']
    f = f[:i] + e['old'] + f[i+len(e['new']):]
assert f.encode() == original
full_patches = patches('parent-v3-to-current-v6', original, b)
delta = save('Source-delta-v6.json', {
    'schema': 'observed-receptor-provider-equal-record-Source-delta-v6',
    'parent_source': pin(parent_path), 'source': source, 'edits': edits, 'patches': im,
    'whole_raw_inverse_exact': True, 'whole_AST_inverse_exact': True,
    'actual_patch_both_directions_F0_exact': True, 'whole_v3_parent_source': prior_delta['parent_source'],
    'whole_v3_edits': full_edits, 'whole_v3_patches': full_patches,
    'preserved_v5_negative': 'Shared global planning budget could exhaust on first record; Source-only finding by Root before any actual.',
    'source_only': True, 'scientific_calls': 0, 'scientific_acceptance': False})

def regions(data):
    lines = data.decode().splitlines(True)
    out = {}
    def walk(nodes, prefix=''):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                k = prefix + n.name
                out[k] = (''.join(lines[n.lineno-1:n.end_lineno]), ast.dump(n, include_attributes=False))
                walk(n.body, k + '.')
    walk(ast.parse(data).body)
    return out

ra, rb = regions(a), regions(b)
unchanged = [k for k in ra if k in rb and ra[k] == rb[k]]
changed = [k for k in ra if k in rb and ra[k] != rb[k]]
assert changed == ['build_family_batch']
ca = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(a).body
      if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
cb = {n.targets[0].id: ast.literal_eval(n.value) for n in t.body
      if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
assert [k for k in ca if ca[k] != cb[k]] == ['VERSION']
assert "work.trial();allocation['row_trials'] += 1" in s
assert len(edits) == 9
checks = {'AST_compile_without_evaluation': True, '9_exact_raw_regions_and_whole_AST_inverse': True,
          'both_immediate_and_whole_parent_actual_patch_directions_F0': True,
          'only_VERSION_constant_changed': True, 'only_build_family_batch_named_region_changed': True,
          'same_DEFAULT_LIMITS_FLAGS_report26_request6': True,
          'equal_floor_allocation_before_mode_matching_no_redistribution': True,
          'nested_assignment_prefix_only_no_ownwork_native_error_catch': True,
          'strict_total_trial_bound_quota_times_record_count_le_total': True,
          'source_ground_and_check_UNKNOWN_allocation_status_explicit': True,
          'original_trial_work_and_preflight_functions_raw_AST_exact': True}
audit = save('static-audit-v6.json', {'schema': 'observed-receptor-provider-static-v6',
    'source': source, 'source_delta': delta, 'checks': checks,
    'unchanged_named_regions': unchanged, 'changed_named_regions': changed,
    'project_module_imported_or_evaluated': False, 'source_only': True,
    'scientific_calls': 0, 'scientific_acceptance': False})
api = json.loads(raw(H / 'API-wire-v5.json'))
api.update(schema='receptor-family-observed-receptor-provider-API-v6', version=cb['VERSION'])
api['shared_physical_plan'] = (
    'Materialize BEFORE matching. Allocate floor(row_trials/min(records,len(families))) trial calls to EACH eligible record; '
    'same both modes. Each record has its own nested finite structural prefix stop; the next record still runs. '
    'No redistribution from incomplete/short/unknown records or remainder; total trials <= declared row_trials. '
    'Root records2/row_trials64 means quota32 each. Record/output/root-sharing/strict-prior/full24row policy unchanged. '
    'Full work/depth/native/callback/collision errors retain original behavior; only scoped _AssignmentPrefix is caught locally.')
api['physical_plan_accounting'] = {
    'policy': 'MODE_INDEPENDENT_EQUAL_PER_RECORD_STRUCTURAL_PREFIX',
    'fields': ['policy', 'complete_within_declared_limits', 'bounded_reason', 'allocated_record_count',
               'row_trials_per_record', 'unallocated_remainder', 'record_allocations', 'plans'],
    'per_record_fields': ['record_index', 'row_trial_quota', 'row_trials', 'planned_assignments', 'status', 'bounded_reason'],
    'scope': 'Source/check UNKNOWN and unfinished work remain distinct. Plans/counts are advisory prefix observations, not matching/domain completeness.'}
api_ref = save('API-wire-v6.json', api)
C = json.loads(raw(H / 'Source-contract-v5.json'))
C.update(schema='receptor-family-observed-receptor-provider-Source-contract-v6', source=source,
         sources={'provider': source}, version=cb['VERSION'], API=api_ref, source_delta=delta, static_audit=audit,
         operative_parent_contract=pin(H / 'Source-contract-v5.json'), parent_source=pin(parent_path))
C['fair_planning_change'] = {
    'reason': 'Root Source-only finding: first literal record could consume entire shared structural budget, starving abstract records before matching.',
    'rule': api['shared_physical_plan'], 'accounting': api['physical_plan_accounting'],
    'original_semantics_native_fallback_unchanged': True, 'prior_V5_unexecuted_and_preserved': True,
    'availability_runtime_benefit_claimed': False}
C['Review_ABI'].update(schema='receptor-family-observed-receptor-provider-typed-Source-review-v6',
                      source=source, sources=C['sources'], source_contract='current capsule')
cref = save('Source-contract-v6.json', C)
href = save('handoff-v6.json', {'schema': 'receptor-family-observed-receptor-provider-handoff-v6',
    'source': source, 'source_contract': cref, 'API': api_ref, 'source_delta': delta,
    'static_audit': audit, 'actual_patches': im, 'whole_v3_patches': full_patches,
    'Review_ABI': dict(C['Review_ABI'], source_contract=cref),
    'report_schema': cb['RESULT_SCHEMA'], 'report_fields': api['report_fields'],
    'request_fields': api['request_fields'], 'binding_policies': api['mode_policies'],
    'residual_policy_version': cb['RESIDUAL_POLICY_VERSION'],
    'producer_implementation_version': cb['PRODUCER_IMPLEMENTATION'],
    'fair_per_record_planning': api['shared_physical_plan'],
    'source_only': True, 'scientific_calls': 0, 'scientific_acceptance': False,
    'actual_execution_authorized': False})
print(json.dumps({'source': source, 'contract': cref, 'API': api_ref, 'delta': delta,
                  'audit': audit, 'handoff': href, 'changed_named_regions': changed,
                  'unchanged_named_regions': unchanged}, sort_keys=True))
