"""ROOT metadata/display assembly only; no search, model, oracle or policy imports."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.gcts-active/curriculum-gates-progress-20261012'
REPORT = ROOT / 'docs/research/gcts-rl-renewal/curriculum-contexts'
PRODUCER = Path('.gcts-active/family-curriculum-context-source-v3-20261012')
INDEPENDENT = Path('.gcts-active/family-curriculum-independent-source-v3-20261012')
DISPLAY = Path('.gcts-active/curriculum-context-reader-source-20261012')
GATES = Path('.gcts-active/curriculum-gates-progress-20261012')
ORIGINS = []
INPUTS = {}

def read(path, expected=None):
    path = Path(path)
    raw = (ROOT / path).read_bytes()
    pin = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if expected is not None:
        assert pin['sha256'] == expected, pin
    if str(path) in INPUTS:
        assert INPUTS[str(path)] == pin, pin
    INPUTS[str(path)] = pin
    return raw

def data(path, expected=None):
    return json.loads(read(path, expected))

def copy(path, dest, expected=None):
    path = Path(path)
    raw = read(path, expected)
    out = REPORT / dest
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('xb') as file:
        file.write(raw)
    ORIGINS.append({'href': dest, 'source': INPUTS[str(path)]})
    return dest

def save(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    with path.open('xb') as file:
        file.write(raw)
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

assert not REPORT.exists(), 'Never overwrite a previously assembled reader'
prep = data(GATES / 'preparation-donor-two-guards-measured-ROOT-terminal-v2.json',
            '5dc43db23ada0b99d0cb5a0d3c9b3a35b0e48a6eaff87cf72ff680f2bfa64415')
provisional = data(GATES / 'static-donor-two-guards-provisional-ROOT-terminal-v1.json',
                   '4e84adf59fb8fddc1d53a317afd392ac63c4045bfda0a9e79ea4c58d17dab116')
external = data(GATES / 'static-donor-two-guards-external-launcher-v1.json',
                '76118f55684442dc7d85a70e8dfe0e20b3864fe4046a7ee9df4273c781602d3e')
result = data(INDEPENDENT / 'outputs/donor-two-guards/static-result-v1.json',
              '4c780805a89a6d00c48af9831e9eb2d54556a0f3cb2c39e8e9b4e5bc357ed617')
lifetime = data(INDEPENDENT / 'outputs/donor-two-guards/static-lifetime-v1.json')
disposition = data(GATES / 'first-static-resource-unknown-disposition-v1.json',
                   '8c58dd8438bb9a2d672ac888f5a93e0cc26421f07394bace1e8938b76e9b77dc')
compiled_raw = read(PRODUCER / 'outputs/donor-two-guards/compiled-context-v1.json.gz',
                    '15b598dbbb66669d62c96e6298b4838f111e1a56060082a229d780d6ad031ab2')
compiled = json.loads(gzip.decompress(compiled_raw))
evidence_raw = read(PRODUCER / 'outputs/donor-two-guards/preparation-evidence-v1.json.gz',
                    '4013f45690e9035b1e82a199a7c0b83caaf370f762ad2b417f6fc37766068cfc')
evidence = json.loads(gzip.decompress(evidence_raw))
split = data(Path('.gcts-active/family-proposal-rl-small-source-20261012/donor-split-v1.json'),
             '7085af5ac8304faf3268ee7117bb9674c77f849cdb17b45899a9fc6c4eb0e4ed')
reference = data(Path('.gcts-active/fixed-family-transfer-plan-20261012/next-experiment-v1.json'),
                 'f2f8c25b21dfee4966bdcfd6fe93d0dcaa4c4caf194a3a83462474cf9db5f24b')
assert prep['full_resource_accepted'] is True
assert prep['original_external_envelope_accepted'] is False
assert provisional['full_resource_accepted'] is False
assert external['accepted_for_metadata_finalization'] is False
assert result['static_context_pool_accepted'] is True
assert result['certificate_accepted'] is False and result['searches'] == 0 and result['training'] == 0
assert disposition['complete_context_qualification_issued'] is False
assert result['complete_initial_domain_census']['initial_complete_candidates'] == 332130
assert len(result['groups_checked']) == 5
assert result['source_body_count'] == 171 and result['RL_full_pool_capacity'] == 64
assert len(compiled['formula_codes']) == 217
assert provisional['maximum_bytes'] == prep['maximum_bytes'] == 536870912

# Resolve literal saved display metadata only. No producer compiler or proof checker.
def literal(item):
    if 'literal_ast' in item:
        return item['literal_ast']
    value = reference
    for key in item['metadata_reference']:
        value = value[key]
    return value

def term_latex(term):
    if term[0] == 'fun' and term[2] == []:
        return '\\ell' if term[1] == 'l' else term[1]
    if term[0] == 'var':
        return term[1]
    raise ValueError('Display supports only the saved constant/variable terms')

def formula_latex(formula):
    if formula[0] == 'pred':
        return '\\operatorname{' + formula[1] + '}(' + ','.join(term_latex(t) for t in formula[2]) + ')'
    if formula[0] == 'eq':
        return term_latex(formula[1]) + '=' + term_latex(formula[2])
    if formula[0] == 'not':
        return '\\neg(' + formula_latex(formula[1]) + ')'
    if formula[0] == 'and':
        return '(' + formula_latex(formula[1]) + '\\land ' + formula_latex(formula[2]) + ')'
    raise ValueError('No additional display grammar is required for these saved formulas')

guards = [(reference['original_ordered_hypotheses_ast'][0], 'H(P,Q,\\ell,m)'),
          (reference['original_ordered_hypotheses_ast'][1], 'H(P,Q,m,n)')]
def readable(formula):
    for ast, latex in guards:
        if formula == ast:
            return latex
    return formula_latex(formula)

entries = list(split['donors']) + [split['held_out']]
expected_order = ['donor-two-guards', 'donor-two-equalities', 'donor-repeated-guard',
                  'donor-repeated-equality', 'heldout-mixed-guard-equality']
assert [entry['id'] for entry in entries] == expected_order
contexts = []
for index, entry in enumerate(entries):
    raw_hyp = entry['ordered_hypotheses']
    hypotheses = literal(raw_hyp) if isinstance(raw_hyp, dict) else [literal(item) for item in raw_hyp]
    target = literal(entry['target'])
    assert len(hypotheses) == 3
    if index == 0:
        assert hypotheses == compiled['context']['ordered_local_premises'] == result['original_Gamma']
        assert target == compiled['target'] == result['target']
    h_records = []
    for occurrence, ast in enumerate(hypotheses):
        code = compiled['formula_codes'].index(ast)
        duplicate = next((i for i in range(occurrence) if hypotheses[i] == ast), None)
        license_id = result['fresh_context_assumptions'][occurrence]['recipe_id'] if index == 0 else None
        h_records.append({'occurrence_index': occurrence, 'row': occurrence, 'latex': readable(ast),
                          'formula_code': code, 'license_id': license_id, 'duplicate_of_index': duplicate,
                          'literal_formula_ast': ast})
    phase = {'status': 'not_run', 'root_full_owned_seconds': None, 'peak_estimate_bytes': None,
             'root_resource_accepted': None, 'artifact_href': None}
    context = {'id': entry['id'], 'partition': 'donor' if index < 4 else 'heldout',
               'hypotheses': h_records, 'target': {'latex': readable(target),
               'formula_code': compiled['formula_codes'].index(target), 'row': 23, 'literal_formula_ast': target},
               'inventory': {'initial_primitive_candidate_count': None, 'complete_cluster_group_count': None,
                             'complete_body_count': None, 'capacity': 64, 'capacity_status': 'pending'},
               'preparation': dict(phase), 'static_gate': dict(phase, context_inventory_accepted=None),
               'formula_display_scope': 'Literal frozen split ASTs and lookup in the saved shared registry; formula codes alone are not fresh model or license qualification.',
               'complete_context_qualification_issued': False}
    if index == 0:
        context['inventory'].update(initial_primitive_candidate_count=332130, complete_cluster_group_count=5,
                                    complete_body_count=171, capacity_status='within')
        context['preparation'] = {'status': 'accepted',
            'root_full_owned_seconds': prep['full_outer_seconds_including_receipt_write'],
            'peak_estimate_bytes': prep['conservative_combined_peak_bytes'], 'root_resource_accepted': True,
            'artifact_href': 'evidence/ROOT/preparation-donor-two-guards-measured-ROOT-terminal-v2.json',
            'note': 'Measured historical preparation qualifies under unchanged caps; original failed predictive envelope retained. No preparation rerun.'}
        context['static_gate'] = {'status': 'unknown',
            'root_full_owned_seconds': external['full_dispatcher_process_seconds_including_startup_imports_final_write_exit_reap'],
            'peak_estimate_bytes': external['observer_inclusive_phase_plus_launcher_peak_estimate_bytes'],
            'root_resource_accepted': False, 'context_inventory_accepted': True,
            'artifact_href': 'evidence/ROOT/first-static-resource-unknown-disposition-v1.json',
            'note': 'Raw finite context/inventory checks passed; complete ROOT resource gate failed the frozen memory limit. This context is not fully qualified.',
            'raw_result_href': 'evidence/independent-actual/static-result-v1.json',
            'inner_owner_peak_estimate_bytes': lifetime['kernel_conservative_peak_bytes'],
            'ROOT_provisional_peak_estimate_bytes': provisional['conservative_combined_peak_bytes'],
            'frozen_maximum_bytes': 536870912,
            'context_mutation_calls': len(result['context_controls']),
            'per_group_pool_comparison_controls': len(result['pool_controls']),
            'controls_scope': 'Actual fresh context-gate calls and per-group comparisons; no full altered-file/process replay.'}
    contexts.append(context)

# Copies are exact saved research artifacts only, never the unrelated preserved-file closure.
REPORT.mkdir(parents=True)
source_expected = {'source-plan-v1.json': '6631f0bd5c079442f48a0035aeb630373e4a8a460fc0aaec5f82cfd20871cf38',
                   'sources-v1.zip': '27159e391f269fbf1ad6ce091d2813ef14aa8fbb2b333868b2ed188dd4f37f68'}
for name in ['source-plan-v1.json', 'sources-v1.zip', 'prospective-protocol-v1.json', 'selection-binding-v1.json',
             'curriculum_context_compiler_v1.py', 'curriculum_prepare_worker_v1.py', 'curriculum_runtime_v1.py',
             'curriculum_selection_v1.py', 'curriculum_supervisor_v1.py', 'curriculum_outer_v1.py', 'freeze_curriculum_source_v1.py']:
    copy(PRODUCER / name, 'evidence/preparation-source/' + name, source_expected.get(name))
for selector in expected_order:
    name = 'preparation-' + selector + '-plan-v1.json'
    copy(PRODUCER / name, 'evidence/preparation-source/' + name)
independent_expected = {'source-plan-v1.json': '34d94837ad995b7508f851968b8e861dc58d3bcf4495317adc68e61a3f9334b9',
                        'sources-v1.zip': '155a717ad936595a30d36fc17a7683638699c47cdd8bb7c6fcfedb893c0569cd'}
for name in ['source-plan-v1.json', 'sources-v1.zip', 'protocol-v1.json', 'source-review-v1.json',
             'curriculum_context_oracle_v1.py', 'curriculum_independent_owner_v1.py',
             'curriculum_independent_worker_v1.py', 'finalize_curriculum_actual_static_plan_v1.py',
             'independent_curriculum_selection_v1.py', 'freeze_curriculum_independent_source_v1.py',
             'actual-static-donor-two-guards-plan-v1.json']:
    copy(INDEPENDENT / name, 'evidence/independent-source/' + name, independent_expected.get(name))
for folder, output in [(PRODUCER / 'outputs/donor-two-guards', 'preparation-actual'),
                       (INDEPENDENT / 'outputs/donor-two-guards', 'independent-actual')]:
    for path in sorted((ROOT / folder).iterdir()):
        assert path.is_file()
        copy(path.relative_to(ROOT), 'evidence/' + output + '/' + path.name)
for name in ['root-preparation-donor-two-guards-activation-v1.json']:
    copy(PRODUCER / name, 'evidence/preparation-actual/' + name)
copy(INDEPENDENT / 'root-static-donor-two-guards-activation-v1.json',
     'evidence/independent-actual/root-static-donor-two-guards-activation-v1.json')
for path in sorted(WORK.iterdir()):
    if path.name.startswith(('preparation-donor-two-guards-', 'static-donor-two-guards-')) or path.name in [
        'ROOT-source-review-v1.json', 'ROOT-dispatcher-freeze-v3.json',
        'first-preparation-failed-envelope-disposition-v1.json', 'first-static-resource-unknown-disposition-v1.json',
        'run_owned_context_gate_v1.py', 'run_owned_context_gate_v2.py', 'run_owned_context_gate_v3.py',
        'launch_owned_context_gate_v1.py', 'launch_owned_context_gate_v2.py',
        'normalize_measured_context_gate_v1.py', 'normalize_measured_context_gate_v2.py', 'normalize_measured_context_gate_v3.py']:
        copy(path.relative_to(ROOT), 'evidence/ROOT/' + path.name)
for source, dest in [('.gcts-active/curriculum-gates-dispatcher-independent-20261012', 'dispatcher-source-review'),
                     ('.gcts-active/curriculum-envelope-independent-metadata-review-20261012', 'preparation-metadata-review')]:
    for path in sorted((ROOT / source).iterdir()):
        assert path.is_file()
        copy(path.relative_to(ROOT), 'evidence/' + dest + '/' + path.name)
copy(Path('.gcts-active/family-proposal-rl-small-source-20261012/donor-split-v1.json'), 'evidence/frozen-contexts/donor-split-v1.json')
copy(Path('.gcts-active/fixed-family-transfer-plan-20261012/next-experiment-v1.json'), 'evidence/frozen-contexts/next-experiment-v1.json')
copy(DISPLAY / 'view-schema-v1.json', 'evidence/display-source/view-schema-v1.json')
copy(DISPLAY / 'source-validation-v2.json', 'evidence/display-source/source-validation-v2.json')
copy(DISPLAY / 'before-partial-actual-update-reader.html', 'evidence/display-source/before-partial-actual-update-reader.html')
copy(DISPLAY / 'reader.html', 'reader.html', '180cbfdd4be02d2d839c6f88c353bc8a265208a67db55f22a84d4822f85a2b59')
copy(DISPLAY / 'reader.js', 'reader.js', 'd3d8fb49a18c871681c8c2db2176065ccdb932939ec264c7ab7c4db2fa586a84')
copy(Path('.gcts-active/curriculum-static-resource-independent-metadata-review-20261012/review-v1.json'),
     'evidence/static-resource-review/review-v1.json', '43c9dabb621526ebe0f5836c69ed077ff2da6c6aaad21482d3438f93f9c94836')
copy(GATES / 'assemble_partial_context_reader_v1.py', 'evidence/ROOT/assemble_partial_context_reader_v1.py')

view = {'schema': 'ROOT-assembled-frozen-curriculum-context-reader-v1', 'notebook': 114,
        'status_note': 'Partial phase: first preparation qualifies; first independent context/inventory checks passed, but complete ROOT resource qualification is UNKNOWN. The remaining four contexts are Not run; learning is unrun.',
        'guard_definition_latex': 'H(P,Q,\\ell,m)\\equiv ' + formula_latex(guards[0][0]),
        'contexts': contexts, 'all_five_contexts_qualified': False,
        'progress': {'new_proofs': 0, 'training_episodes': 0, 'RNG_draws': 0, 'native_queries': 0},
        'costs': {'phase_subtotal_seconds': sum(c['preparation']['root_full_owned_seconds'] or 0 for c in contexts) +
                                         sum(c['static_gate']['root_full_owned_seconds'] or 0 for c in contexts),
                  'scope': 'Full actual ROOT dispatcher process clocks cover startup/imports, preparation or static audit, original receipt-byte serialization, exit and reaping. Only the two executed phases contribute to this subtotal.',
                  'additional_cost_note': 'The external launcher imports, final metadata receipt writes, metadata normalization/finalization, source authoring, inspection, report assembly and publication are additional. Unavailable costs are not zero. The saved conservative complete memory estimates are retained without discount.',
                  'metadata_normalizer_seconds_through_successor_write': 0.012986458,
                  'static_metadata_plan_finalizer_seconds': 0.431088584,
                  'unmeasured_additional_metadata_costs': True},
        'evidence': [
            {'label': 'Exact artifact origins and hashes', 'href': 'origins.json'},
            {'label': 'Frozen context split', 'href': 'evidence/frozen-contexts/donor-split-v1.json'},
            {'label': 'Preparation source plan', 'href': 'evidence/preparation-source/source-plan-v1.json'},
            {'label': 'Independent source plan', 'href': 'evidence/independent-source/source-plan-v1.json'},
            {'label': 'Prepared compiled context', 'href': 'evidence/preparation-actual/compiled-context-v1.json.gz'},
            {'label': 'Complete preparation evidence', 'href': 'evidence/preparation-actual/preparation-evidence-v1.json.gz'},
            {'label': 'Raw independent finite checks', 'href': 'evidence/independent-actual/static-result-v1.json'},
            {'label': 'Inner independent owner receipt', 'href': 'evidence/independent-actual/static-lifetime-v1.json'},
            {'label': 'Measured preparation ROOT receipt', 'href': 'evidence/ROOT/preparation-donor-two-guards-measured-ROOT-terminal-v2.json'},
            {'label': 'Original failed preparation envelope', 'href': 'evidence/ROOT/preparation-donor-two-guards-external-launcher-v1.json'},
            {'label': 'Static complete resource UNKNOWN', 'href': 'evidence/ROOT/first-static-resource-unknown-disposition-v1.json'},
            {'label': 'Static external observation', 'href': 'evidence/ROOT/static-donor-two-guards-external-launcher-v1.json'},
            {'label': 'Independent review of the static resource failure', 'href': 'evidence/static-resource-review/review-v1.json'},
            {'label': 'Independent source review of preparation metadata repair', 'href': 'evidence/preparation-metadata-review/source-review-normalizer-v3.json'}]}
view_pin = save(REPORT / 'view.json', view)
origin_pin = save(REPORT / 'origins.json', {'schema': 'ROOT-partial-context-reader-exact-origins-v1',
                  'scope': 'Exact selected task-owned sources and saved artifacts; no preserved-file dependency contents copied.',
                  'artifacts': ORIGINS, 'assembly_inputs': list(INPUTS.values()), 'scientific_calls': 0})
for path, expected in INPUTS.items():
    raw = (ROOT / path).read_bytes()
    assert len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], path
files = []
for path in sorted(REPORT.rglob('*')):
    if path.is_file():
        raw = path.read_bytes()
        files.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
assembly = {'schema': 'ROOT-partial-context-reader-assembly-v1', 'view': view_pin, 'origins': origin_pin,
            'file_count': len(files), 'total_bytes': sum(p['bytes'] for p in files), 'files': files,
            'all_five_contexts_qualified': False, 'first_static_resource_qualified': False,
            'new_proofs': 0, 'scientific_calls_by_assembler': 0}
pin = save(WORK / 'partial-context-reader-assembly-v1.json', assembly)
print(json.dumps({'assembly': pin, 'file_count': len(files), 'total_bytes': assembly['total_bytes']}))
