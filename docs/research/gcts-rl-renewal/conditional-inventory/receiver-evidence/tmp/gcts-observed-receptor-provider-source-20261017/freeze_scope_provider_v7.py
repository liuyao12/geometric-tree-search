"""Narrow Source/AST metadata successor; no provider/helper evaluation."""
import ast
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
    if isinstance(b, str): b = b.encode()
    if p.exists():
        assert raw(p) == b
        return pin(p)
    with p.open('xb') as f: f.write(b)
    return pin(p)

def save(name, value):
    return write(name, json.dumps(value, sort_keys=True, indent=2) + '\n')

parent = H / 'receptor_transfer_physical_provider_v6.py'
a = raw(parent)
s = a.decode()
edits = []
for label, before, after in [
    ('own_VERSION', "VERSION = 'receptor-family-observed-receptor-transfer-provider-v6'",
     "VERSION = 'receptor-family-observed-receptor-transfer-provider-v7'"),
    ('exact_full_expansion_allowance_rejection',
     "            if error.code in ('PORT_MISMATCH','OUTPUT_MISMATCH','DISTINCT','EIGEN'):return True\n",
     "            if error.code in ('PORT_MISMATCH','OUTPUT_MISMATCH','DISTINCT','EIGEN'):return True\n"
     "            if error.code == 'SCOPE' and str(error) == 'receptor family SCOPE: abstraction free external allowance':return True\n"),
    ('exact_inference_allowance_rejection',
     "                    require(exclusion['code'] in ('UNBOUND_UNKNOWN','PORT_MISMATCH','OUTPUT_MISMATCH','DISTINCT','EIGEN')\n"
     "                            or exclusion['code'] == 'SIDE_CONDITION' and 'unsatisfied ' in exclusion['reason'],\n",
     "                    require(exclusion['code'] in ('UNBOUND_UNKNOWN','PORT_MISMATCH','OUTPUT_MISMATCH','DISTINCT','EIGEN')\n"
     "                            or exclusion['code'] == 'SCOPE' and exclusion['reason'] == 'receptor family SCOPE: abstraction free external allowance'\n"
     "                            or exclusion['code'] == 'SIDE_CONDITION' and 'unsatisfied ' in exclusion['reason'],\n")]:
    assert s.count(before) == 1
    i = s.index(before)
    edits.append({'label': label, 'start': i, 'old': before, 'new': after})
    s = s[:i] + after + s[i+len(before):]
b = s.encode()
ast.parse(b)
compile(b, '<provider7-Source-only>', 'exec', dont_inherit=True)
source = write('receptor_transfer_physical_provider_v7.py', b)
f = a.decode()
for e in edits:
    i = e['start']; assert f[i:i+len(e['old'])] == e['old']
    f = f[:i] + e['new'] + f[i+len(e['old']):]
assert f == s
for e in reversed(edits):
    i = e['start']; assert f[i:i+len(e['new'])] == e['new']
    f = f[:i] + e['old'] + f[i+len(e['new']):]
assert f.encode() == a
assert ast.dump(ast.parse(f), include_attributes=False) == ast.dump(ast.parse(a), include_attributes=False)

def patches(name, x, y):
    out = {}
    for label, before, after in [('forward', x, y), ('full-inverse', y, x)]:
        ref = write(name + '-' + label + '.patch', ''.join(difflib.unified_diff(
            before.decode().splitlines(True), after.decode().splitlines(True), fromfile='before', tofile='after')))
        with tempfile.TemporaryDirectory(dir=str(H)) as td:
            p = Path(td) / 'target.py'; p.write_bytes(before)
            r = subprocess.run(['/usr/bin/patch', '--batch', '-F0', str(p), '-i', ref['path']],
                               cwd=td, capture_output=True)
            assert r.returncode == 0 and p.read_bytes() == after
        out[label] = ref
    return out

im = patches('provider-v6-to-v7', a, b)
v6_delta = json.loads(raw(H / 'Source-delta-v6.json'))
all_edits = v6_delta['whole_v3_edits'] + edits
original_ref = v6_delta['whole_v3_parent_source']
original = raw(original_ref['path'])
f = original.decode()
for e in all_edits:
    i = e['start']; assert f[i:i+len(e['old'])] == e['old']
    f = f[:i] + e['new'] + f[i+len(e['old']):]
assert f == s
for e in reversed(all_edits):
    i = e['start']; assert f[i:i+len(e['new'])] == e['new']
    f = f[:i] + e['old'] + f[i+len(e['new']):]
assert f.encode() == original
full = patches('parent-v3-to-current-v7', original, b)
delta = save('Source-delta-v7.json', {
    'schema': 'observed-receptor-provider-exact-allowance-Source-delta-v7',
    'parent_source': pin(parent), 'source': source, 'edits': edits, 'patches': im,
    'whole_raw_inverse_exact': True, 'whole_AST_inverse_exact': True,
    'actual_patch_both_directions_F0_exact': True, 'whole_v3_parent_source': original_ref,
    'whole_v3_edits': all_edits, 'whole_v3_patches': full,
    'preserved_v6_finding': 'Exact well-formed residual allowance mismatch was fatal; no prior actual.',
    'source_only': True, 'scientific_calls': 0, 'scientific_acceptance': False})

def regions(data):
    lines = data.decode().splitlines(True); out = {}
    def walk(nodes, prefix=''):
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                out[prefix+n.name] = (''.join(lines[n.lineno-1:n.end_lineno]), ast.dump(n, include_attributes=False))
                walk(n.body, prefix+n.name+'.')
    walk(ast.parse(data).body)
    return out

ra, rb = regions(a), regions(b)
same = [k for k in ra if ra[k] == rb[k]]
assert [k for k in ra if ra[k] != rb[k]] == ['build_family_batch']
ca = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(a).body
      if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
cb = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(b).body
      if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
assert [k for k in ca if ca[k] != cb[k]] == ['VERSION']
audit = save('static-audit-v7.json', {
    'schema': 'observed-receptor-provider-static-v7', 'source': source, 'source_delta': delta,
    'checks': {'exact3rawregions_and_wholeASTinverse': True, 'four_actual_patch_directions_F0_exact': True,
               'only_VERSION_constant_changed': True, 'all_othertophelpersclassesrawASTexact': True,
               'exact_type_code_fullreason_only_no_generic_SCOPE_catch': True,
               'same_planning_quotas_limits_report_fields_FLAGS_native_paths': True,
               'AST_compile_without_evaluation': True},
    'unchanged_named_regions': same, 'source_only': True, 'scientific_calls': 0,
    'project_module_evaluated': False, 'scientific_acceptance': False})
api = json.loads(raw(H / 'API-wire-v6.json'))
api.update(schema='receptor-family-observed-receptor-provider-API-v7', version=cb['VERSION'])
api['errors'] += (
    " V7 additionally recognizes ONLY exact producer.DescriptorError code SCOPE with full reason "
    "'receptor family SCOPE: abstraction free external allowance' as an advisory trial-binding rejection. "
    "The same exact code/reason in pinned infer_observed_ports rejected_bindings is permitted. This means the "
    "inferred abstraction's free names do not satisfy THIS candidate's explicit allowance; later well-formed "
    "name assignments may still be tried. Every other SCOPE/malformed/native/resource error retains its prior behavior.")
api_ref = save('API-wire-v7.json', api)
C = json.loads(raw(H / 'Source-contract-v6.json'))
C.update(schema='receptor-family-observed-receptor-provider-Source-contract-v7', source=source,
         sources={'provider': source}, version=cb['VERSION'], API=api_ref,
         source_delta=delta, static_audit=audit, operative_parent_contract=pin(H/'Source-contract-v6.json'),
         parent_source=pin(parent))
C['exact_allowance_revision'] = {
    'finding_author': '/root/hilbert_ordering_diagnosis',
    'authorization': 'Root authorized exactly ownVERSION plus two exact allowance-rejection sites; no caps or other semantics change.',
    'native_rule': 'No new primitive nonmembership classifier. This is exact existing syntax binding allowance rejection, scoped to current advisory assignment only.',
    'producer_site': 'fd3eb854._Core._binding SCOPE abstraction free external allowance; original pinned source unchanged.',
    'current_reason': 'receptor family SCOPE: abstraction free external allowance',
    'all_other_SCOPE_native_guard_callback_resource_errors_unchanged': True,
    'prior_V6_immutable_no_actual': True}
C['Review_ABI'].update(schema='receptor-family-observed-receptor-provider-typed-Source-review-v7',
                      source=source, sources=C['sources'], source_contract='current capsule')
cref = save('Source-contract-v7.json', C)
href = save('handoff-v7.json', {
    'schema': 'receptor-family-observed-receptor-provider-handoff-v7', 'source': source,
    'source_contract': cref, 'API': api_ref, 'source_delta': delta, 'static_audit': audit,
    'actual_patches': im, 'whole_v3_patches': full,
    'Review_ABI': dict(C['Review_ABI'], source_contract=cref),
    'report_schema': cb['RESULT_SCHEMA'], 'report_fields': api['report_fields'], 'request_fields': api['request_fields'],
    'binding_policies': api['mode_policies'], 'residual_policy_version': cb['RESIDUAL_POLICY_VERSION'],
    'producer_implementation_version': cb['PRODUCER_IMPLEMENTATION'],
    'source_only': True, 'scientific_calls': 0, 'scientific_acceptance': False,
    'actual_execution_authorized': False})
print(json.dumps({'source': source, 'contract': cref, 'API': api_ref, 'delta': delta,
                  'audit': audit, 'handoff': href}, sort_keys=True))
