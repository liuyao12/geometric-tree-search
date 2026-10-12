"""Metadata-only immutable source/plan freeze; no project functional import.

Only known manifest JSON, literal curriculum documents, Python ASTs, raw byte
hashing and source archives are handled. No selector/compiler/graph/proposal/
policy/checker/RNG/model/fixture/search/training call occurs in this freezer.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SELECTORS = ('donor-two-guards', 'donor-two-equalities',
             'donor-repeated-guard', 'donor-repeated-equality',
             'heldout-mixed-guard-equality')
SOURCE_NAMES = ('curriculum_selection_v1.py', 'curriculum_context_compiler_v1.py',
    'curriculum_runtime_v1.py', 'curriculum_prepare_worker_v1.py',
    'curriculum_supervisor_v1.py', 'curriculum_outer_v1.py', 'freeze_curriculum_source_v1.py')


def absolute(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def pin(path):
    path = Path(path).resolve(); digest = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block); size += len(block)
    try:
        name = str(path.relative_to(ROOT))
    except ValueError:
        name = str(path)
    return {'path': name, 'sha256': digest.hexdigest(), 'bytes': size}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def read(path):
    return json.loads(Path(path).read_text())


def save(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')


def main():
    started = time.perf_counter()
    if any((HERE / name).exists() for name in ('source-plan-v1.json', 'selection-binding-v1.json', 'integration-v1.json')):
        raise ValueError('immutable source package already frozen; preserve it')
    old_path = ROOT / '.gcts-active/fixed-family-transfer-source-v1-20261012/preparation-plan-v1.json'
    RL_path = ROOT / '.gcts-active/family-proposal-rl-small-source-20261012/source-plan-v1.json'
    previous_directory = ROOT / '.gcts-active/family-curriculum-context-source-v2-20261012'
    previous_integration_path = previous_directory / 'integration-v1.json'
    previous_integration = read(previous_integration_path)
    old = read(old_path); RL = read(RL_path)
    if RL['execution_authorized'] is not False or old['execution_authorized_by_source_freeze'] is not False:
        raise ValueError('source packages cannot grant scientific execution')
    documents = {'reference': ROOT / '.gcts-active/fixed-family-transfer-plan-20261012/next-experiment-v1.json',
        'split': ROOT / '.gcts-active/family-proposal-rl-small-source-20261012/donor-split-v1.json',
        'protocol': ROOT / '.gcts-active/family-proposal-rl-small-source-20261012/protocol-v1.json'}
    decoded = {role: read(path) for role, path in documents.items()}
    split = decoded['split']; protocol = decoded['protocol']
    if (tuple(item['id'] for item in split['donors']) != SELECTORS[:4]
            or split['held_out']['id'] != SELECTORS[-1]
            or split['execution_authorized'] is not False or protocol['execution_authorized'] is not False
            or split['common_boundary']['rows'] != 24 or protocol['features']['count'] != 31
            or len(protocol['curriculum']['training_episodes']) != 8
            or len(protocol['evaluation']['schedule']) != 8):
        raise ValueError('exact existing frozen four donors, heldout and policy protocol required')
    binding = {'schema': 'frozen-five-context-selection-v1', 'documents': {
        role: {'raw_pin': pin(documents[role]),
               'canonical_sha256': hashlib.sha256(canonical(value).encode('utf8')).hexdigest()}
        for role, value in decoded.items()},
        'selectors': list(SELECTORS), 'execution_authorized': False,
        'scope': 'Canonical hashes of literal metadata documents only; no context selector or compiler invoked.'}
    save('selection-binding-v1.json', binding)
    direct_roles = ('primitive_model', 'primitive_logical_audit', 'complete_family_projection',
        'old_complete_body_plan', 'prior_search_helper', 'prior_forward_order', 'prior_decoder',
        'lifecycle_kernel', 'primitive_core', 'proposal_module', 'accepted_old_positive_disposition',
        'accepted_old_positive_audit_plan', 'accepted_old_positive_audit_result',
        'accepted_old_positive_audit_lifetime', 'accepted_old_positive_root_terminal',
        'master_contract', 'repository_contract')
    original_roles = {record['role']: record for record in old['inputs']}
    inputs = [{k: original_roles[role][k] for k in ('role', 'path', 'sha256', 'bytes')} for role in direct_roles]
    inputs.extend({k: record[k] for k in ('role', 'path', 'sha256', 'bytes')}
                  for record in old['inputs'] if record['role'].startswith('old_body_closure_'))
    extra = {'curriculum_reference': documents['reference'], 'frozen_donor_split': documents['split'],
        'frozen_RL_protocol': documents['protocol'], 'frozen_selection_binding': HERE / 'selection-binding-v1.json',
        'original_partial_selection_source': ROOT / '.gcts-active/family-curriculum-context-source-v1-20261012/curriculum_selection_v1.py',
        'original_transfer_source_plan': old_path, 'original_frozen_RL_source_plan': RL_path}
    extra.update({'prior_curriculum_source_plan': previous_directory / 'source-plan-v1.json',
        'prior_curriculum_source_readiness': previous_directory / 'readiness-v1.json',
        'prior_curriculum_source_archive': previous_directory / 'sources-v1.zip',
        'prior_curriculum_source_integration': previous_integration_path,
        'prior_curriculum_package_pins': HERE / 'previous-v2-package-pins-v1.json'})
    inputs.extend({'role': role, **pin(path)} for role, path in extra.items())
    if len({record['role'] for record in inputs}) != len(inputs):
        raise ValueError('all complete distinct source input roles retained')
    sources = []; syntax = []
    for name in SOURCE_NAMES:
        path = HERE / name
        tree = ast.parse(path.read_text(), filename=str(path), feature_version=(3, 9))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(item.name for item in node.names)
            if isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        record = pin(path); sources.append(record)
        syntax.append({'source': record, 'AST_nodes': sum(1 for _ in ast.walk(tree)), 'imports': sorted(set(imports))})
    preserved = {}
    historical = old['sources'] + old['inputs'] + old['preserved_files'] + [pin(old_path)]
    historical += RL['sources'] + RL['inputs'] + RL['preserved_sources_inputs'] + [RL['protocol'], RL['donor_split'], pin(RL_path)]
    historical += previous_integration['files'] + [pin(previous_integration_path)]
    for record in historical:
        literal = {k: record[k] for k in ('path', 'sha256', 'bytes')}
        previous = preserved.setdefault(literal['path'], literal)
        if previous != literal:
            raise ValueError('conflicting frozen inherited source identity')
    direct = {record['path']: {k: record[k] for k in ('path', 'sha256', 'bytes')} for record in sources + inputs}
    for path in direct:
        preserved.pop(path, None)
    checked = {}
    for record in list(direct.values()) + list(preserved.values()):
        actual = pin(absolute(record['path']))
        if actual != record:
            raise ValueError('exact immutable source/input byte changed: ' + record['path'])
        checked[record['path']] = actual
    runtime_alias = Path('/Library/Developer/CommandLineTools/usr/bin/python3')
    runtime = {'executable': str(runtime_alias), 'platform': sys.platform, 'version': sys.version,
        'binary': pin(runtime_alias.resolve()), 'process_metadata': pin('/bin/ps')}
    protocol_new = {'schema': 'frozen-curriculum-context-preparation-handoff-v1',
        'status': 'SOURCE_ONLY_five_exact_contexts_unexecuted', 'selection_binding': pin(HERE / 'selection-binding-v1.json'),
        'frozen_split': pin(documents['split']), 'frozen_RL_protocol': pin(documents['protocol']),
        'selectors': list(SELECTORS), 'context_selection': 'Only exact frozen metadata references/literal ASTs; no proof word, chosen family subset or target priority script.',
        'inventory': {'non_assumption_witnesses': 226, 'ordered_assumption_occurrences': 3,
            'formula_values': 217, 'conditional_source_bodies': 171, 'single_types': 171,
            'ordered_pair_types': 29241, 'height': 24, 'all_initial_point_domains': 'complete; not sampled'},
        'identity': 'The original two-guard donor retains its semantic contextual assumption IDs; changed contexts rebuild all three licenses. Repeated equal formulas retain distinct index licenses. Fresh per-selector source/plan provenance changes model/full-placement/body/pool identity even where semantic context agrees.',
        'boundary': 'All24 required rows are explicit generation-zero roots. Only the three occurrence seeds and the resolved fixed-target formula mark vary; negative exterior sentinel, strict prior offsets, translations and complete point grammar stay identical.',
        'advice': 'Every independently rederived canonical single/ordered-pair root binding and shared full-key union is retained; exact base domains/fallback/scheduler unchanged.',
        'RL_capacity': {'maximum_full_group_count': 64, 'scope': 'Prospective RL feasibility only; preserve all descriptors and report unresolved if exceeded, never trim.'},
        'actual_output_schema': {'compiled': 'closed-frozen-curriculum-context-v1',
            'compiled_fields_additive_to_transfer': ['curriculum_binding', 'hypothesis_codes', 'target_code'],
            'evidence': 'fresh-context-whole-family-pool-preparation-v1',
            'evidence_additional_fields': ['curriculum_binding', 'hypothesis_codes', 'target_code', 'RL_full_pool_capacity', 'RL_full_pool_capacity_satisfied'],
            'artifact_names': ['compiled-context-v1.json.gz', 'preparation-evidence-v1.json.gz', 'preparation-outcome-v1.json'],
            'artifact_namespace': 'outputs/<exact frozen selector>/'},
        'required_actual_static_gate': 'Separate ROOT-owned independent code must resolve the original frozen documents itself, rederive all229 licenses/171 recursively checked conditional bodies/full171+29241 grammar/24 raw domains, bind raw new outputs and actual owner/reaped ROOT terminals. Prior producer counts/source-only manifests are not acceptance. The existing mixed-only static gate cannot accept donor outputs unchanged.',
        'actual_donor_search_and_training': 'Not implemented or authorized here. All five preparation/static gates and the separate real-Controller feature/overlay fixture must precede the frozen episode driver. The8episode/8evaluation schedule,31features,rewards,seeds,zero weights/hyperparameters remain byte frozen.',
        'resource_protocol': {'per_context_preparation_outer_seconds': 60, 'supervisor_seconds': 55, 'child_seconds': 50,
            'per_context_independent_static_seconds': 180, 'peak_bytes': 536870912,
            'five_preparation_and_audit_phase_seconds': 1260, 'coordinator_allowance_seconds': 60,
            'whole_cost': 'Charge all imports/compilation/all bodies/full pool/all candidate domains/serialization/cleanup and full ROOT outer lifecycle. Existing monitor omits observer simultaneous RSS; no OS hard cap or aggregate-host bound.'},
        'hypothesis_holdout': 'Context composition only; existing formula/constant/primitive/source-family overlap and historical old donor result retained. No unseen-theorem, universal Wang, full Hilbert geometry, PA, or native acceptance claim.',
        'immutable_failure': 'Any missing/partial/resource-failed run is UNKNOWN with all partials retained and no rerun under the same frozen version. Observe/reap the same process handle; no retry from an observation timeout.',
        'execution_authorized': False, 'ROOT_sole_actual_owner_and_publisher': True}
    save('prospective-protocol-v1.json', protocol_new)
    inputs.append({'role': 'frozen_curriculum_preparation_protocol', **pin(HERE / 'prospective-protocol-v1.json')})
    source_plan = {'schema': 'frozen_five_curriculum_context_source_plan_v1',
        'status': 'SOURCE_ONLY_immutable_compiler_and_owned_preparation_sources_unexecuted',
        'sources': sources, 'inputs': inputs, 'preserved_files': sorted(preserved.values(), key=lambda item: item['path']),
        'runtime': runtime, 'selection_binding': pin(HERE / 'selection-binding-v1.json'),
        'protocol': pin(HERE / 'prospective-protocol-v1.json'),
        'frozen_donor_split': pin(documents['split']), 'frozen_RL_protocol': pin(documents['protocol']),
        'per_context_plan_paths': ['preparation-' + selector + '-plan-v1.json' for selector in SELECTORS],
        'source_authoring_seconds': None, 'metadata_freeze_seconds_before_source_plan_write': time.perf_counter() - started,
        'scientific_function_imports_calls_models_fixtures_RNG_searches_training_checkers_native': 0,
        'existing_transfer_outputs_read_or_used_as_context_acceptance': False,
        'execution_authorized': False, 'ROOT_only_actual_execution': True}
    save('source-plan-v1.json', source_plan)
    plan_pins = []
    for selector in SELECTORS:
        prefix = 'outputs/' + selector + '/'
        phase = {'kind': 'preparation', 'worker': 'curriculum_prepare_worker_v1.py',
            'child_seconds': 50, 'supervisor_seconds': 55, 'outer_seconds': 60, 'bytes': 536870912,
            **{name: prefix + 'preparation-' + name + '-v1.' + ('txt' if name in ('stdout', 'stderr') else 'json')
               for name in ('stdout', 'stderr', 'launch', 'outcome', 'supervision', 'lifetime')}}
        outputs = {'compiled_context': prefix + 'compiled-context-v1.json.gz',
                   'preparation_evidence': prefix + 'preparation-evidence-v1.json.gz'}
        plan = {'schema': 'frozen-curriculum-family-preparation-plan-v1',
            'status': 'source_frozen_exact_context_preparation_pending_review_and_ROOT_activation',
            'selector': selector, 'partition': 'heldout' if selector == SELECTORS[-1] else 'donor',
            'sources': sources, 'inputs': inputs + [{'role': 'curriculum_source_freeze', **pin(HERE / 'source-plan-v1.json')}],
            'preserved_files': source_plan['preserved_files'], 'runtime': runtime, 'phase': phase,
            'outputs': outputs, 'output_directory': prefix[:-1],
            'proposed_outputs': list(outputs.values()) + [phase[name] for name in ('stdout', 'stderr', 'launch', 'outcome', 'supervision', 'lifetime')],
            'activation_basename': 'root-preparation-' + selector + '-activation-v1.json',
            'activation_status': 'ROOT_authorized_exact_frozen_curriculum_context_preparation_v1',
            'activation_schema': 'ROOT-frozen-curriculum-preparation-activation-v1',
            'RL_full_pool_capacity': 64, 'immutable_fixed_split': pin(documents['split']),
            'immutable_fixed_RL_protocol': pin(documents['protocol']), 'prospective_counts': protocol_new['inventory'],
            'scheduler_and_domains': 'Unchanged global dead/forced/earliest-generation+degree+row. Every primitive alignment and distant marking dependency, all root generations and exact t/m/rollback/fallback retained. No sampled pool supplies domains or exhaustion.',
            'scope': 'Full context/PointGraph/conditional-body/pool/candidate preparation only. Independent per-context static acceptance is mandatory before any trajectory.',
            'target_searches': 0, 'Controller_calls': 0, 'Executor_calls': 0, 'logical_checker_calls': 0,
            'RNG_draws': 0, 'training_runs': 0, 'native_queries': 0,
            'execution_authorized_by_source_freeze': False}
        filename = 'preparation-' + selector + '-plan-v1.json'; save(filename, plan); plan_pins.append(pin(HERE / filename))
    diffs = []
    for old_name, new_name in (('transfer_outer_v1.py', 'curriculum_outer_v1.py'),
                               ('transfer_supervisor_v1.py', 'curriculum_supervisor_v1.py')):
        original = ROOT / '.gcts-active/fixed-family-transfer-source-v1-20261012' / old_name
        successor = HERE / new_name
        diff = ''.join(difflib.unified_diff(original.read_text().splitlines(True), successor.read_text().splitlines(True),
            fromfile=str(original.relative_to(ROOT)), tofile=str(successor.relative_to(ROOT))))
        name = new_name.replace('.py', '-source-diff-v1.txt')
        with (HERE / name).open('x') as stream:
            stream.write(diff)
        diffs.append(pin(HERE / name))
    archive = HERE / 'sources-v1.zip'
    archived = sources + [pin(HERE / 'selection-binding-v1.json'), pin(HERE / 'prospective-protocol-v1.json'),
                          pin(HERE / 'source-plan-v1.json'), pin(HERE / 'previous-v2-package-pins-v1.json')] + plan_pins + diffs
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as stream:
        for record in archived:
            stream.write(absolute(record['path']), arcname=str(Path(record['path']).relative_to(HERE.relative_to(ROOT))))
    readiness = {'status': 'SOURCE_ONLY_ready_for_ROOT_and_independent_review_NOT_EXECUTION',
        'source_plan': pin(HERE / 'source-plan-v1.json'), 'selection_binding': pin(HERE / 'selection-binding-v1.json'),
        'prospective_protocol': pin(HERE / 'prospective-protocol-v1.json'), 'per_context_plans': plan_pins,
        'source_archive': pin(archive), 'new_sources': len(sources), 'source_ASTs': syntax,
        'preserved_unique_paths': len(preserved), 'unique_preexisting_paths_checked': len(checked),
        'input_roles_per_context': len(inputs) + 1,
        'future_ROOT_commands_after_separate_review_and_activation': [[runtime['executable'],
            str(HERE / 'curriculum_outer_v1.py'), str(absolute(record['path']))] for record in plan_pins],
        'metadata_seconds_before_readiness_write': time.perf_counter() - started,
        'metadata_kernel_peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
        'scientific_imports_calls_models_fixtures_RNG_searches_training_checkers_native': 0,
        'actual_prepared_contexts': 0, 'actual_donor_trajectories': 0, 'actual_heldout_trajectories': 0,
        'source_authoring_and_manual_read_cost_seconds': None,
        'scope': 'AST/raw hash/manifest/literal-document canonical-hash/source archive only; no selector/compiler/proposal/graph/policy/checker function or model construction occurred.',
        'limitations': ['Per-context outputs, complete pool sizes and feasibility remain unmeasured; no static acceptance or proof result.',
            'A separately frozen generic independent context/body/domain/pool gate remains required; the mixed-only gate cannot validate donors unchanged.',
            'Actual preparation should stop the RL version if any complete pool exceeds64; retain it unchanged and never trim.',
            'Actual ROOT full outer clock and reap evidence must include receipt serialization; existing owned peak estimates omit observer simultaneous RSS and are not OS or host aggregate hard bounds.',
            'No actual policy driver, donor updates, heldout evaluation or native/universal compiler acceptance supplied.'],
        'execution_authorized': False}
    save('readiness-v1.json', readiness)
    files = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file()]
    save('integration-v1.json', {'status': readiness['status'], 'files': files,
        'source_plan': pin(HERE / 'source-plan-v1.json'), 'readiness': pin(HERE / 'readiness-v1.json'),
        'scientific_execution': False, 'ROOT_sole_actual_owner_and_publisher': True})
    print(json.dumps({'source_plan': pin(HERE / 'source-plan-v1.json'),
        'integration': pin(HERE / 'integration-v1.json'), 'source_count': len(sources),
        'per_context_plans': len(plan_pins), 'preserved_paths': len(preserved),
        'scientific_execution': False, 'metadata_seconds': readiness['metadata_seconds_before_readiness_write']}))


if __name__ == '__main__':
    main()
