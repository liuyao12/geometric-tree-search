"""Static-only lifecycle package review; no producer/engine import or execution."""
import ast
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / '.gcts-active/hilbert-cluster-lifecycle-20261011'
OUT = Path(__file__).resolve().parent


def pin(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(65536), b''):
            h.update(part)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def need(test, message):
    if not test:
        raise ValueError(message)


def main():
    began = time.perf_counter()
    plan_path = DATA / 'plan-v1.json'
    plan = json.loads(plan_path.read_bytes())
    parsed, all_pins = [], {}
    for kind in ('sources', 'inputs', 'preserved_files'):
        for entry in plan[kind]:
            p = ROOT / entry['path']
            actual = pin(p)
            need(actual == {k: entry[k] for k in ('path', 'sha256', 'bytes')}, 'exact lifecycle freeze pin')
            if entry['path'] in all_pins:
                need(all_pins[entry['path']] == actual, 'same path cannot have two pins')
            all_pins[entry['path']] = actual
            if kind == 'sources':
                ast.parse(p.read_bytes(), filename=str(p))
                parsed.append(actual)
    limits = plan['producer_limits']
    need(limits == {'full_outer_wall_seconds': 60, 'child_alarm_seconds': 50, 'supervisor_seconds': 55,
                    'host_bytes': 536870912, 'execution_authorized_by_this_freeze': False}, 'unchanged prospective tiny bounds')
    need(plan['actual_model_executions'] == 0 and plan['actual_geometry_target_searches'] == 0
         and plan['native_queries'] == 0 and plan['new_RL_training'] is False, 'source-only activation scope')
    need(plan['projection_counts']['fixture_groups_planned'] == 11
         and plan['projection_counts']['exhaustive_formula_states_planned'] == 64
         and plan['projection_counts']['counts_are_predictions_until_actual_terminal_receipt'] is True,
         'predicted fixture counts')
    core_path = ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py'
    need(pin(core_path)['sha256'] == 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd',
         'unchanged complete primitive kernel')
    clarification_path = DATA / 'authoring-cost-clarification-v1.json'
    clarification = json.loads(clarification_path.read_bytes())
    need(clarification['frozen_invalid_value'] == plan['cost_accounting']['source_authoring_elapsed_since_instrumented_start_seconds'],
         'explicit invalid cross-process authoring timer preserved')
    for entry in clarification['bindings']:
        need(pin(ROOT / entry['path']) == entry, 'cost clarification exact binding')
    source = (DATA / 'hilbert_cluster_lifecycle_v1.py').read_text()
    need("core.integer(member['formula_code'])" in source and 'not math.isfinite(seconds)' in source,
         'exact integer and finite time declarations corrected before freeze')
    fixture_source = (DATA / 'hilbert_cluster_fixtures_v1.py').read_text()
    need("'authored24'" not in fixture_source and 'frozen_family_authority(' not in fixture_source,
         'synthetic entry point does not call actual family/model loader')
    receipt = dict(
        status='passed_independent_static_tiny_lifecycle_readiness_with_cost_scope_caveats',
        plan=pin(plan_path), sources=parsed, source_entries=len(plan['sources']),
        input_entries=len(plan['inputs']), preserved_entries=len(plan['preserved_files']),
        unique_verified_paths=len(all_pins), authoring_cost_clarification=pin(clarification_path),
        mathematical_source_review=[
            'BodyAuthority.expected reconstructs ordered input/member row mapping, recipe keys, complete primitive identities and aggregate markings from frozen body records. compile requires exact descriptor equality, so separately valid but unauthorized member replacements fail.',
            'Ordered receptor ports/readers remain explicit. Noninjective recipient maps preserve port multiplicity and reject conflicting formula aliases; source-body member order stays strict.',
            'Exact selected member identity is compared against decorated identity; only unselected members add occupancy. Distinct same-formula keys cannot share occupancy.',
            'Whole pending members are checked against complete current domains including parent-local exclusions, whole additional occupancy and remote aggregate marking agreement. Assigned zero is tested by membership.',
            'One invalid pending constituent retires the whole descriptor, with no preference supplied by its still-legal siblings. Retirement is branch-absorbing until paired rollback.',
            'Global graph decision remains unchanged; forced moves bypass hint ordering. Branch ordering is all ready exact keys once followed by every remaining base candidate.',
            'Hint statuses, eligible caches, reasons, revisions and graph state are trailed to paired checkpoints; semantic snapshot hash must match after rollback. Work counters deliberately do not roll back.',
            'Executor unknown_budget rolls back child and parent without exclusion. Only exhausted_finite_marked_subtree creates a restored-parent candidate exclusion, followed by whole resync.',
            'Static return structure supports finite first-success existence preservation, subject to complete graph/rollback/justified exhaustion. Same visited solution set requires exhaustive enumeration, not first-success termination.',
            'Synthetic opaque-pair recipes are explicitly nonlogical. Actual guarded incidence palette/admission remains separately pinned and unexecuted in this phase.',
        ],
        resource_source_review=[
            'New child has 50-second SIGALRM; sole supervisor samples its own child RSS/time, kills and waits on error/limit, and rejects final peak above cap. Supervisor wall 55 seconds; outer whole lifetime rejects above 60 seconds/512 MiB.',
            'No OS soft-limit claim. External metadata failures fail closed; actual samples/terminal receipts must establish qualification.',
            'The outer whole gate is retrospective and includes producer/supervisor serialization; final outer receipt write remains outside measurement.',
        ],
        caveats=[
            'Disposition permits root to dispatch one bounded authored synthetic producer only. All 11 groups and 64 formula states remain predictions until terminal receipts.',
            'Independent lifecycle actual checks require a new exact source/input/output freeze and separate root authorization.',
            'No actual 24-row geometry graph, target DFS, RL, native query, compiler or authority activation.',
            'All root source registries are explicit trusted authored infrastructure; generic caller metadata alone is not external logical/native admission.',
            'Controlled tiny exclusions outside the DFS are tagged fixture-controlled-not-proof; they do not certify exhausted subtrees.',
            'The altered-equality-template descriptor test checks exact command/body binding; it is not an independent arbitrary equality-rule checker.',
            'Cross-process authoring elapsed value 0.497945667 is invalid and retained with clarification. The UTC interval is calendar time, not CPU effort; earlier reads remain unmeasured.',
            'Controller tracks scan/order/rollback metrics in memory but tiny output does not export them; descriptor compilation has no separate timer. Only total owned phase can charge them from this output. No saved subphase-cost claim.',
            'Fixed priority is an ordering control, not RL. No searched mathematical theorem or observed proof-search gain follows from toy conformance.',
        ],
        static_review_seconds_before_receipt_write=time.perf_counter()-began,
        manual_source_inspection_and_authoring_time='unmeasured; excluded from static pin verifier clock',
        engine_imports=0, fixture_executions=0, actual_model_executions=0,
        target_searches=0, native_queries=0)
    target = OUT / 'tiny-source-review-v1.json'
    with target.open('x') as f:
        f.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'receipt': pin(target),
                      'entry_counts': [receipt['source_entries'], receipt['input_entries'], receipt['preserved_entries']]}))


if __name__ == '__main__':
    main()
