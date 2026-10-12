"""Static report source review; no generator/checker/UI or model imports."""
import ast
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REPORT = ROOT / '.gcts-active/receptor-matching-progress-20261011'
SECONDS = 60
BYTES = 134217728


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('source-only report review60s')))
    signal.alarm(SECONDS)
    planpath = HERE / 'review-plan-v1.json'
    plan = json.loads(planpath.read_text())
    for entry in plan['sources'] + plan['context_pins']:
        if pin(ROOT / entry['path']) != entry:
            raise ValueError('static review source changed: ' + entry['path'])
    texts = {Path(entry['path']).name: (ROOT / entry['path']).read_text() for entry in plan['sources']}
    trees = {path: ast.parse(source, filename=path) for path, source in texts.items() if path.endswith('.py')}
    evidence = texts['report_evidence.py']
    generator = texts['prepare_report.py']
    validator = texts['validate_report.py']
    stage = texts['stage_publication.py']
    checks = {
        'path_and_SHA_requirement_identity': "identity = (relative, expected_sha)" in evidence and "old_routes[(origin, e['sha256'])]" in evidence,
        'historical_source_lookup_same_identity': "historical_sources.get((relative, expected_sha))" in evidence,
        'historical_member_separated_by_version': "'historical/' + version + '/' + path" in evidence,
        'current_route_rejected_if_wrong_bytes': "if direct and pin(ROOT / path) != expected:" in evidence,
        'historical_overrides_never_adopt_current_route': "route = None if identity in overrides else direct or old_routes.get(identity)" in evidence,
        'all_exported_routes_rehashed': "assert observed=={k:entry[k] for k in ('sha256','bytes')}" in validator,
        'all_origins_copy_equal_source': "assert pin(ROOT/entry['path'])==pin(ROOT/entry['origin'])" in validator,
        'generator_flags_equal_actual_audit_mapping': "assert acceptance['observation_verdicts']==selected['observation_verdicts']" in generator,
        'validator_flags_equal_actual_audit_mapping': "assert acceptance['observation_verdicts']==selected['observation_verdicts']" in validator,
        'original_observation_augmented_without_rewrite': "value=copy.deepcopy(result)" in generator and "assert projected==augmented" in validator,
        'formula_registry_recipes_hypotheses_target_same': all(fragment in validator for fragment in ("assert visual['formula_codes']==model['formula_codes']", "assert visual['recipes']==", "assert visual['hypotheses']==", "assert visual['target']==model['formula_codes'][54]")),
        'actual_unknown_certificates_forbidden': "assert raw['point_certificate'] is None and raw['decoded_certificate'] is None" in validator and "assert verdict['certificate_accepted'] is False" in validator,
        'saved_trace_unknown_scope_strict': "assert raw['status']=='unknown_search_budget' and raw['attempts']==128" in validator and "assert raw['initial_state']==raw['terminal_state']" in validator,
        'no_authored_hint_new_native_RL_claim': "assert outcome['authored_words_used_as_hints']==outcome['native_queries']==0" in validator and "assert outcome['new_RL_training'] is False" in validator,
        'timing_label_corrected': "'Score feature seconds'" in generator and "'Literal matching','literal_matching_seconds'" in generator and "'Comparison and score payload hashing','feature_payload_hash_seconds'" in generator,
        'inclusive_and_overlapping_cost_scope': "cold" in generator.lower() and "Component timers overlap" in generator and "Source-authoring CPU time is unmeasured" in generator,
        'historical_unknown_costs_additional': "50.405773542" in generator and "historical inventory/native preparation and prior unknown runs remain additional" in generator,
        'MathJax_established_chtml_and_latex_delimiters': 'tex-chtml.js' in generator and "r'\\('" in generator and "r'\\['" in generator,
        'partial_constraints_not_proofs': "search states, not established derivations" in generator and "pending earlier sources" in generator,
        'fixed_feature_not_RL_or_learned_pruning': "authored deterministic ordering" in generator and "neither trains RL nor learns failure markings" in generator,
        'no_statistical_transfer_or_unrestricted_native_claim': "does not establish statistical superiority" in generator and "not the full request-independent Wang palette" in generator,
        'arithmetic_transfer_not_activated': "current searched grammar lacks primitive instantiation actions" in generator and "do not activate arithmetic quantifier guidance or discover arithmetic proofs" in generator,
        'main_reconstruction_exact_one_panel_and_counter': "assert restored==baseline" in validator and "'RESEARCH NOTEBOOK · 107','RESEARCH NOTEBOOK · 106',1" in validator,
        'task_paths_restricted_in_validator_and_stager': "assert all(path==MAIN or path.startswith(PREFIX) for path in paths)" in validator and "assert all(p==MAIN or p.startswith(PREFIX) for p in expected)" in stage,
        'staged_blob_hashes_exact': "raw=git('show',':'+e['path'])" in stage and "assert staged==expected" in stage,
        'goal_remains_active': "goal_status='active'" in generator
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError('static source condition failed: ' + ', '.join(failed))
    imports = {path: sorted({(node.module if isinstance(node, ast.ImportFrom) else name.name)
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        for name in (node.names if isinstance(node, ast.Import) else [ast.alias(name='from')])})
        for path, tree in trees.items()}
    notes = {
        'fixed_items': [
            'ROOT changed the misleading Feature seconds label to Score feature seconds and added all four recorded receptor subphase timers before this snapshot.',
            'ROOT changed both helper and validator to require exact equality between selected flags and actual independent observation_verdicts before this snapshot.'
        ],
        'final_projection_gate_required': [
            'Reconcile ROOT terminal selection with the exact terminal audit result, lifetime/same-handle receipt and cost/peak field provenance. These actual files were not read by this source review.',
            'Verify every selected frozen folder exists and every producer/independent/prior-source pin has at least one exact (path,SHA) public route, including historical MAIN105 and committed baseline MAIN106.',
            'The generic projection scanner skips nonexistent paths/folders. That is not complete closure by itself; actual final pin-set reconciliation must demonstrate that no required item was skipped.',
            'Verify task-files manifest and staged blobs contain only the new receptor-matching prefix plus the additive MAIN panel/counter; preserve previous published bytes.',
            'Check actual report assessment text, trace flags, null certificates, cost fields, renderer/link behavior and live math separately. No rendered/DOM/native/logical acceptance follows from this source review.'
        ],
        'historical_version_semantics': 'Same historical path may legitimately have multiple byte versions. Compare identities by (path,sha256), never deduplicate by path. Every direct or archive-member route must independently hash to its expected version.',
        'archive_scope': 'A .diff/.js/.html excluded from direct suffix copying can still have a bound archive-member route. Route presence and exact bytes, not direct-copy count, establish its preservation.',
        'cost_scope': 'New AST owner + producer owner + independent owner are disjoint owned phases only. Source preparation/reference controls/metadata/reviews/generation/publication and historical native preparation remain additional; overlapping component timers must not be summed.',
        'scientific_and_UI_scope': 'This review read source text, parsed Python ASTs and hashed source/context bytes only. It never imported a generator, viewer, checker or scientific engine; never inflated results/models; never rendered or executed a report.'
    }
    wall = time.perf_counter() - started
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
    result = {'status': 'passed_bounded_source_only_report_projection_review_pending_actual_projection' if wall <= SECONDS and rss <= BYTES else 'unknown_static_review_resource',
        'checks': checks, 'source_ASTs': len(trees), 'source_import_declarations_not_executed': imports,
        'notes': notes, 'inputs': plan['sources'] + plan['context_pins'], 'plan': pin(planpath),
        'mutable_source_origins': plan['mutable_source_origins'],
        'seconds_before_receipt_write': wall, 'kernel_peak_bytes': rss, 'seconds_ceiling': SECONDS, 'host_ceiling_bytes': BYTES,
        'clock_scope': 'Helper only; interpreter startup/final receipt write excluded. Source authoring unmeasured.',
        'actual_results_read': 0, 'actual_models_loaded': 0, 'engine_imports': 0, 'report_execution': 0,
        'scientific_execution': 0, 'UI_imports': 0, 'rendering': 0, 'publication': 0,
        'actual_projection_qualified': False}
    with (HERE / 'source-review-v1.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    signal.alarm(0)
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'seconds': wall,
        'rss_bytes': rss, 'review': pin(HERE / 'source-review-v1.json')}))


if __name__ == '__main__':
    main()
