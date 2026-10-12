"""Static-only source/input metadata freeze. Never imports scientific modules."""
import ast
import datetime
import difflib
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def save(name, data):
    with (HERE / name).open('x') as stream: json.dump(data, stream, indent=2); stream.write('\n')


def main():
    start = time.perf_counter()
    priorpath = ROOT / '.gcts-active/receptor-matching-geometry-source-20261011/search-plan-v1.json'
    prior = json.loads(priorpath.read_text()); oldroles = {p['role']: p['path'] for p in prior['inputs']}
    files = ['family_proposal_v2.py', 'family_preparation_worker_v2.py',
             'family_preparation_supervisor_v2.py', 'family_preparation_outer_v2.py',
             'family_preparation_freeze_v2.py']
    sources = [pin(HERE / name) for name in files]
    static = []
    for name in files:
        tree = ast.parse((HERE / name).read_text(), filename=name)
        static.append({'name': name, 'top_level_functions': [x.name for x in tree.body if isinstance(x, ast.FunctionDef)],
                       'imports': [ast.unparse(x) for x in tree.body if isinstance(x, (ast.Import, ast.ImportFrom))]})
    # Broader predecessor role aliases remain verbatim. The body factory receives
    # the separately pinned accepted original56 plan, never this broader phase.
    inputs = list(prior['inputs'])
    required = {
        'lifecycle_kernel': oldroles['frozen_lifecycle_kernel'],
        'original_point_model_plan': oldroles['prior_full_model_plan'],
        'original_56_input_body_plan': oldroles['passed_full_lifecycle_producer_plan'],
        'checked_compact_family_projection': oldroles['complete_family_template_projection'],
        'prior_matching_phase_plan': str(priorpath.relative_to(ROOT)),
        'prior_matching_actual_independent_terminal': '.gcts-active/receptor-matching-progress-20261011/root-independent-terminal-v3.json',
        'prior_matching_actual_independent_result': '.gcts-active/receptor-matching-geometry-independent-20261011/audit-result-v3.json',
        'prior_matching_actual_independent_lifetime': '.gcts-active/receptor-matching-geometry-independent-20261011/audit-lifetime-v3.json',
        'prior_matching_actual_producer_terminal': '.gcts-active/receptor-matching-progress-20261011/root-producer-terminal-v1.json',
        'prior_matching_actual_producer_lifetime': '.gcts-active/receptor-matching-geometry-source-20261011/search-lifetime-v1.json',
        'prior_matching_actual_producer_outcome': '.gcts-active/receptor-matching-geometry-source-20261011/search-outcome-v1.json',
        'prior_fixed_unknown_trace': '.gcts-active/receptor-matching-geometry-source-20261011/fixed-forward-reference-result-v1.json.gz',
        'prior_matching_unknown_trace': '.gcts-active/receptor-matching-geometry-source-20261011/fixed-forward-receptor-result-v1.json.gz',
        'recorded_metadata_diagnosis_manifest': '.gcts-active/receptor-matching-diagnosis-20261011/integration-v1.json',
        'early_assessment': str((HERE / 'early-assessment-manifest-v1.json').relative_to(ROOT)),
    }
    inputs.extend({'role': role, **pin(ROOT / path)} for role, path in required.items())
    authority_plan = json.loads((ROOT / required['original_56_input_body_plan']).read_text())
    assert len(authority_plan['inputs']) == len({p['path'] for p in authority_plan['inputs']}) == 56
    assert prior['model_epoch'] == '06bc80d38463caa934136e428e66a05bafd6715c715f1fa3892b0dcf20c3c46c'
    preserved = {p['path']: {k: p[k] for k in ('path', 'sha256', 'bytes')}
                 for p in prior['sources'] + prior['inputs'] + prior['preserved_files']}
    extra_folders = [ROOT / '.gcts-active/receptor-matching-geometry-source-20261011',
                     ROOT / '.gcts-active/receptor-matching-diagnosis-20261011']
    for folder in extra_folders:
        for path in sorted(folder.iterdir()):
            if path.is_file(): preserved[str(path.relative_to(ROOT))] = pin(path)
    for name in ['family_proposal_api_v1.py', 'protocol-v1.md', 'early-assessment-manifest-v1.json',
                 'family_preparation_worker_source_review_draft_v2.py', 'family_proposal_source_review_draft_v2.py']:
        preserved[str((HERE / name).relative_to(ROOT))] = pin(HERE / name)
    for p in inputs:
        if p['path'] in preserved and preserved[p['path']] != {k: p[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('inconsistent predecessor source pin')
        preserved[p['path']] = {k: p[k] for k in ('path', 'sha256', 'bytes')}
    for p in preserved.values():
        if pin(ROOT / p['path']) != p: raise ValueError('previous immutable byte changed: ' + p['path'])
    drafts = [('family_preparation_worker_source_review_draft_v2.py', 'family_preparation_worker_v2.py'),
              ('family_proposal_source_review_draft_v2.py', 'family_proposal_v2.py')]
    diffs = []
    for before, after in drafts:
        name = after.replace('.py', '-source-review.diff')
        with (HERE / name).open('x') as stream:
            stream.writelines(difflib.unified_diff((HERE / before).read_text().splitlines(True),
                                                 (HERE / after).read_text().splitlines(True), before, after))
        diffs.append(pin(HERE / name))
    corrections = {
        'status': 'source_only_pre_freeze_review_corrections_no_actual_execution',
        'worker_loader': 'ROOT identified frozen_model(root,plan); preserved draft called one argument. Corrected to exact old accepted convention.',
        'fixed_priority': 'ROOT identified caller-adjustable priority. Immutable computed priority tuple now belongs to pool epoch; expected requires exact indexed value.',
        'additional_metadata': 'Resolved ordered input full-key/full-ID provenance and preparation/registration/graph metric counters added before freeze.',
        'drafts': [pin(HERE / a) for a, _ in drafts], 'diffs': diffs,
        'scientific_imports': 0, 'model_constructions': 0, 'registry_factories': 0, 'fixtures': 0,
        'target_searches': 0, 'native_queries': 0, 'training': 0,
    }
    save('source-review-corrections-v2.json', corrections)
    inputs.append({'role': 'pre_freeze_source_corrections', **pin(HERE / 'source-review-corrections-v2.json')})
    plan = {
        'version': 'finite-family-preparation-plan-v2', 'status': 'unexecuted_source_ready_preparation_only_ROOT_review_and_activation_required',
        'saved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'sources': sources, 'inputs': inputs,
        'preserved_files': [preserved[k] for k in sorted(preserved)], 'unchanged_model_epoch': prior['model_epoch'],
        'scope': {'source_families': 171, 'recipes': 229, 'formulas': 217, 'rows': 24,
                  'original_body_input_paths': 56, 'broader_predecessor_role_prefix_retained': len(prior['inputs']),
                  'single_type_count_prediction': 171, 'ordered_pair_type_count_prediction': 171 ** 2,
                  'binding_and_group_counts': 'unmeasured until separately authorized preparation; no winning subset',
                  'proposals': 'one canonical embedding per exact ordered root/output binding; one whole union hint; all primitive alternatives unchanged',
                  'family_relation': 'previously checked authored/certified finite infrastructure, not newly discovered lemmas',
                  'native_accepted': False, 'native_authority_activated': False,
                  'Controller_constructions': 0, 'Executor_constructions': 0, 'target_searches': 0,
                  'logical_checker_runs': 0, 'point_certificates': 0, 'native_queries': 0, 'new_RL_training': False},
        'prospective_resources': {'preparation_seconds_including_model_and_original_body_setup': 30,
                                 'child_seconds': 60, 'supervisor_seconds': 65, 'ROOT_outer_seconds': 70,
                                 'conservative_host_peak_bytes': 536870912,
                                 'enforcement': 'child SIGALRM; owned external ps RSS/time watchdog; final kernel peak plus outer validation; no OS soft limit claim',
                                 'in_flight': 'deadline checked between finite operations; overshoot retained; owner gates still apply',
                                 'unknown': 'incomplete preparation exports partial visit/rejection accounting but no partial active pool'},
        'costs': {'source_authoring': 'unmeasured; no cross-process monotonic estimate',
                  'static_freeze': 'separately timed source/pin/AST metadata only, not scientific preparation',
                  'new_preparation': 'all source verification/model/body/interface/binding/embedding/sharing/compile/serialization/watchdog/reap costs charged',
                  'prior_matching_producer_seconds': 9.340212875, 'prior_metadata_owner_seconds': 0.654260666,
                  'prior_inventory': 'retain all prior raw admissions, failed resource gates and independent replay bills; no free preparation claim'},
        'pool_output': {'evidence': 'preparation-evidence-v2.json.gz', 'contains': 'all type visits; all rejected bindings; accepted groups with exact component/body/conclusion/ordered ports/full keys/IDs/t/m and source closure; no authored proof hints',
                        'authority': 'new proposal epoch wrapping unchanged original 171-body relation; not native acceptance',
                        'full_identity_preimages': 'SHA-bound and independently reconstructible from exact keys/graph/registry; not repeated long browser payloads'},
        'scientific_executions_by_freeze': 0, 'execution_authorized_by_freeze': False,
        'required_next_gates': ['ROOT full source and input closure review', 'independent source disposition and exact ROOT activation',
                                'one ROOT-owned bounded preparation only', 'independent complete pool/source/body/union/canonical-embedding audit',
                                'separate future lifecycle/search/learning/certificate/native gates'],
        'proposed_outputs': ['preparation-stdout-v2.txt', 'preparation-stderr-v2.txt', 'preparation-launch-v2.json',
                             'preparation-evidence-v2.json.gz', 'preparation-outcome-v2.json', 'preparation-supervision-v2.json', 'preparation-lifetime-v2.json'],
        'ROOT_command_after_reviews_and_activation': 'python3 ' + str((HERE / 'family_preparation_outer_v2.py').relative_to(ROOT)),
    }
    save('preparation-plan-v2.json', plan)
    closure = {p['path']: {k: p[k] for k in ('path', 'sha256', 'bytes')} for p in sources + inputs + plan['preserved_files']}
    for p in closure.values():
        if pin(ROOT / p['path']) != p: raise ValueError('final source closure mismatch')
    receipt = {'status': 'static_source_pin_AST_freeze_only_no_scientific_execution',
               'plan': pin(HERE / 'preparation-plan-v2.json'), 'sources': sources, 'AST_metadata': static,
               'input_roles': len(inputs), 'preserved_files': len(plan['preserved_files']), 'unique_source_closure_paths': len(closure),
               'mismatches': 0, 'elapsed_seconds': time.perf_counter() - start,
               'peak_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
               'scientific_imports': 0, 'model_constructions': 0, 'registry_factories': 0, 'fixtures': 0, 'searches': 0,
               'native_queries': 0, 'new_RL_training': False, 'execution_authorized': False}
    save('source-freeze-v2.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('sources', 'AST_metadata')}, allow_nan=False))


if __name__ == '__main__': main()
