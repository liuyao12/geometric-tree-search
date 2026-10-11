"""Saved-artifact metadata diagnosis only; never imports a scientific engine.

Reads recorded events and literal recipe/interface schema to label counts and
the observed prefix. It does not regenerate candidates, replay a state, validate
an inference, construct a point model, apply the proposed matcher or search.
"""
import collections
import copy
import gzip
import hashlib
import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
V2 = ROOT / '.gcts-active/shared-symbolic-geometry-search-source-v2-20261011'
ROOT_TERMINAL = ROOT / '.gcts-active/automatic-geometry-progress-20261011/root-producer-v2-terminal.json'


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def read(path):
    with (gzip.open(path, 'rt') if Path(path).suffix == '.gz' else Path(path).open()) as stream:
        return json.load(stream)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def save(path, value):
    with Path(path).open('x') as stream: stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    started = time.perf_counter()
    for name in ('diagnosis-v1.json', 'next-gate-plan-v1.json', 'manifest-v1.json'):
        if (HERE / name).exists(): raise ValueError('immutable metadata artifact already exists')
    plan = read(V2 / 'search-plan-v1.json'); outcome = read(V2 / 'search-outcome-v1.json')
    terminal = read(ROOT_TERMINAL); lifetime = read(V2 / 'search-lifetime-v1.json')
    preserved = {}
    for p in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        q = pin(ROOT / p['path'])
        if q != {k: p[k] for k in ('path', 'sha256', 'bytes')}: raise ValueError('frozen prior pin mismatch')
        preserved[q['path']] = q
    roles = {p['role']: ROOT / p['path'] for p in plan['inputs']}
    # Literal source JSON schema, not core.frozen_model or a candidate generator.
    schema = read(roles['primitive_model']); recipes = schema['recipes']
    code = {canonical(f): i for i, f in enumerate(schema['formula_codes'])}
    family = read(roles['complete_family_template_projection']); family.pop('example', None)
    observations = []
    for spec in outcome['observations']:
        p = ROOT / spec['result']['path']
        if pin(p) != spec['result']: raise ValueError('recorded trace bytes changed')
        result = read(p); events = result['events']
        steps = [e for e in events if e['kind'] == 'primitive_step']
        exclusions = [e for e in events if e['kind'] == 'parent_local_exhausted_child_exclusion']
        decisions = [e for e in events if e['kind'] == 'global_decision']
        prefix = []
        for e in steps[:15]:
            w = recipes[e['key'][0]]['primitive_witness']
            prefix.append({'event_index': events.index(e), 'node': e['node'], 'key': e['key'],
                'rule': w['rule'], 'output_code': code[canonical(w['formula'])],
                'universal_binder': w['universal'][1] if w['rule'] == 'instantiate' else None,
                'closed_term': w.get('term')})
        maximum = max(sum(e['state']['projection']['graph']['totals']) for e in events)
        deepest = next((i,e) for i,e in enumerate(events) if sum(e['state']['projection']['graph']['totals']) == maximum)
        initial_graph = result['initial_state']['projection']['graph']
        seedcodes = [code[canonical(recipes[k[0]]['primitive_witness']['formula'])] for k in initial_graph['order']]
        seed_rows_by_code = {c: [k[1] for k in initial_graph['order']
                                if code[canonical(recipes[k[0]]['primitive_witness']['formula'])] == c]
                             for c in seedcodes}
        # Literal interface equality only; no body placement/embedding or proof.
        literal_matches = [d for d in family['definitions'] if all(c in seedcodes for c in d['premise_codes'])]
        matches = [{'name': d['name'], 'family': d['family'], 'ordered_premise_codes': d['premise_codes'],
                    'ordered_matching_seed_rows': [seed_rows_by_code[c] for c in d['premise_codes']],
                    'conclusion_code': d['conclusion_code'], 'primitive_members': d['primitive_member_count']}
                   for d in literal_matches]
        observations.append({'id': spec['id'], 'trace': pin(p), 'recorded_status': result['status'],
            'recorded_attempts': result['attempts'], 'recorded_search_seconds': result['seconds'],
            'recorded_nodes': result['node_count'], 'events': len(events),
            'event_kind_counts': dict(collections.Counter(e['kind'] for e in events)),
            'selected_row_counts': dict(collections.Counter(str(e['key'][1]) for e in steps)),
            'selected_rule_counts': dict(collections.Counter(recipes[e['key'][0]]['primitive_witness']['rule'] for e in steps)),
            'first_fifteen_recorded_steps': prefix,
            'steps_after_prefix': len(steps) - len(prefix),
            'rows_used_after_first_fifteen': sorted({e['key'][1] for e in steps[15:]}),
            'minimum_recorded_excluded_branch_row': min(e['key'][1] for e in exclusions),
            'recorded_deepest_occupied_rows': maximum, 'first_deepest_event_index': deepest[0],
            'first_deepest_order': deepest[1]['state']['projection']['graph']['order'],
            'recorded_restored_root_flag': result['root_restored'],
            'saved_initial_terminal_snapshots_equal': result['initial_state'] == result['terminal_state'],
            'initial_seed_formula_codes': seedcodes, 'initial_literal_port_matching_interfaces': matches,
            'recorded_graph_metrics': result['graph_metrics'], 'recorded_order_metrics': result['ordering_metrics'],
            'recorded_fixed_forward_metrics': result['fixed_forward_metrics'],
            'recorded_preparation': result['preparation_costs'], 'recorded_serialization_seconds': spec['serialization_seconds'],
            'point_certificate_present': result['point_certificate'] is not None,
            'mathematical_scope': 'Recorded producer metadata only, pending independent trace/domain/rollback audit; no regenerated candidates or new proof.'})
        del result, events, steps, exclusions, decisions

    for folder in (V2,):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts: preserved[pin(path)['path']] = pin(path)
    preserved[pin(ROOT_TERMINAL)['path']] = pin(ROOT_TERMINAL)
    prior = Decimal(str(plan['costs']['retained_v1_failed_owner_seconds']))
    current = Decimal(str(lifetime['full_supervisor_process_seconds_including_receipt_write']))
    diagnosis = {'status': 'source_bound_saved_trace_metadata_diagnosis_pending_independent_trace_audit',
        'saved_utc': datetime.now(timezone.utc).isoformat(), 'analysis_source': pin(Path(__file__)),
        'inputs': [pin(V2 / name) for name in ('search-plan-v1.json', 'source-manifest-v2.json', 'search-outcome-v1.json',
                    'search-lifetime-v1.json', 'search-supervision-v1.json', 'root-activation-v1.json')]
                    + [pin(ROOT_TERMINAL), pin(roles['primitive_model']), pin(roles['complete_family_template_projection'])],
        'observations': observations,
        'findings': [
            'The attempt ceiling, rather than the 20-second clock or 2,000-event ceiling, terminated both observations. More wall time alone would not change this fixed 128-attempt experiment.',
            'Base initially places the identical I.2 axiom in every row from 3 through 17. Subsequent tail exploration cannot repair this early allocation until backtracking reaches those earlier choices.',
            'Fixed readiness/novelty removes axiom repetition but resolves tied instantiations by AST size and canonical witness. The recorded first two point instantiations both use P, so the later guard contains the literal not-equality of P with itself and does not match either supplied common-point guard.',
            'All 113 steps after the first 15 occur in rows 18 through 23. No recorded parent exclusion reaches the first fifteen branch choices. The entire attempt budget is spent repairing a target-side tail under that same unhelpful prefix.',
            'The existing fixed ordering has no hypothesis-to-consequent receptor-match feature. Its behavior follows its stated features; the metadata does not establish a scheduler, inference or rollback source bug.',
            'Literal inventory metadata already has three interfaces whose ordered premises match the initial seed formulas: two uniqueness bodies and one searched incidence-transport body. This is a potential proposal source, not an admitted point embedding, a discovered new proof or a target-specific hint whitelist.',
            'A better early specialization feature may still leave unsupported target-side choices. The next hierarchy experiment should use generic validated family attachments and newly produced receptor formulas, with complete primitive fallback; it must not insert the authored 24-row target word.'
        ],
        'formula_explanation_latex': {'bad_guard_literal': r'\(\neg(P=P)\)',
            'supplied_guards': r'\(H(P,Q,l,m),\ H(P,Q,m,n)\)',
            'seed_incidence': r'\(\operatorname{Incident}(R,l)\)'},
        'logical_caution': 'A legal implication with an unusable or contradictory antecedent is not an invalid inference. Literal guard mismatch is a ranking signal here, never a proof-preserving exclusion.',
        'counts_scope': 'Census of exact saved producer events and literal schema labels only. Independent every-domain/order/exhaustion/rollback verification remains open for these two search traces.',
        'costs': {'prior_v1_failure_seconds': float(prior), 'current_v2_full_owner_seconds': float(current),
            'known_v1_plus_v2_owner_seconds': float(prior + current), 'v2_peak_bytes': lifetime['conservative_host_peak_bytes'],
            'metadata_read_and_analysis_seconds_before_write': time.perf_counter() - started,
            'source_authoring': 'Unmeasured; preliminary read-only inspections not instrumented.',
            'source_dependency_costs': 'Original admissions, all unknown/repair costs and independent audits remain separately pinned dependencies, not free.',
            'timer_caution': 'Subphase timers can overlap; do not add them as disjoint wall costs or treat fewer nodes/greater occupancy as proof discovery or speedup.'},
        'no_new_scientific_work': {'engine_imports': 0, 'model_constructions': 0, 'candidate_regenerations': 0,
            'state_replays': 0, 'logical_checks': 0, 'new_searches': 0, 'native_queries': 0, 'compiler_activations': 0,
            'training': False, 'authored_words_used_as_hints': 0},
        'preserved_files': [preserved[k] for k in sorted(preserved)], 'publication_owner': 'root'}
    diagpath = HERE / 'diagnosis-v1.json'; save(diagpath, diagnosis)

    nextplan = {'status': 'prospective_source_only_receptor_match_ranking_gate_no_implementation_or_dispatch',
        'diagnosis': pin(diagpath), 'exact_predecessor_plan': pin(V2 / 'search-plan-v1.json'),
        'recommended_small_next_step': 'Add generic literal partial-guard matching as an ordering feature, then compare the unchanged fixed-forward control against this new ordering on the same full problem. Keep all candidate alternatives.',
        'hypothesis': 'Available hypothesis receptors resolve early quantifier specialization ties more usefully than formula size/witness text alone, reducing tail exploration under an unusable prefix. This is untested.',
        'fixed_scope': {'model_epoch': plan['model_epoch'], 'recipes': 229, 'formulas': 217, 'rows': 24,
            'validated_source_bodies': 171, 'body_authority_plan': plan['body_authority_adapter']['exact_accepted_original_full_plan'],
            'active_cluster_descriptors': 0, 'authored_target_words_as_hints': 0, 'same_theory_hypotheses_target_and_point_boundary': True},
        'matching_feature_specification': [
            'Use only exact formula ASTs of already selected primitive placements, including original hypothesis seeds. A marking on an unoccupied row is not an available hypothesis.',
            'For an instantiation witness, inspect its consequent AST; peel its leading universal binders and, when present, read the immediate implication antecedent as a receptor pattern. Its corresponding MP consequence may use the same pattern feature.',
            'Only variables bound by that peeled universal prefix are pattern variables. Match to whole already selected quantifier-free antecedent formulas by literal AST constructor, symbol, arity, polarity, ordered argument and closed-constant equality.',
            'The first bounded matcher admits images that are closed zero-arity function terms only; repeated occurrences of a pattern variable require the exact same term. Constants introduced by completed instantiations cannot be rebound. Unsupported/nested quantified patterns receive a neutral score rather than a rejection.',
            'Do not solve satisfiability, invoke a host logical prover, infer a new hypothesis, merge conjunctions or rewrite commands. This is structural pattern matching for ranking only.',
            'Keep the original readiness tiers; within relevant ties prefer a pattern matching an available receptor over a nonmatching specialization, then apply the original AST size/witness/recipe/reference tie order. Specify neutral versus match versus nonmatch exactly before implementation.',
            'Compute a complete permutation at the graph-selected point. No failed match removes a candidate or changes degrees, dead/forced decisions, earliest-generation choice, remote markings or parent exclusions.',
            'No predicate names, geometry constants, target formula code, theorem ID, authored proof word or preselected family pair may be embedded in the matching code.'
        ],
        'prospective_controls': [{'mode': 'same frozen fixed-forward ordering', 'attempts': 128, 'seconds': 20, 'trace_events': 2000},
            {'mode': 'fixed-forward plus generic receptor-match feature', 'attempts': 128, 'seconds': 20, 'trace_events': 2000}],
        'source_and_resource_gate': {'before_execution': 'New versioned source/input/preservation/feature plan plus root and independent source review; this note authorizes no implementation run.',
            'owner_seconds': 180, 'supervisor_seconds': 175, 'worker_alarm_seconds': 170, 'host_bytes': 536870912,
            'independent_seconds': 180, 'independent_host_bytes': 536870912,
            'unchanged_child_unknown_behavior': 'Unknown restores paired state without excluding the child; exact finite exhaustion is the only parent-exclusion cause.',
            'costs': 'Charge frozen old preparation/failure costs, fresh model/body setup, matcher feature preparation/per-candidate time, complete permutation/trace/rollback/serialization and separate full audit.'},
        'prospective_adversarial_cases': ['Literal repeated variable matched inconsistently', 'Already instantiated constant rebound',
            'Predicate/constructor/arity/polarity mismatch', 'Binder shadowing or quantified recipient mistaken for a free pattern',
            'Same-formula different primitive reference/identity', 'Ordered duplicate premises merged', 'Nonmatch prunes a legal fallback key',
            'Unsupported AST treated as a logical rejection', 'Forced move bypassed or late-generation receptor selected',
            'Budget-unknown child excluded', 'Source/body authority alias regression'],
        'certificate_goal': 'Only a newly returned full point certificate and independently checked all-24-row symbolic proof count as discovery. All unknowns remain unknown. Any later shared-machine native gate is separately frozen after exact input-byte/capacity review.',
        'interpretation': 'No new RL training. One finite deterministic problem, two order controls; no significance, universal-palette correspondence or general speed claim.',
        'alternate_next_hierarchy_route': {
            'proposal': 'A generic proposer scans every one of the 171 validated family interfaces and every ordered selected-row premise match. It suggests source-body embeddings using exact primitive identities and shared members, then validates aggregates against the same graph.',
            'new_receptors': 'Newly selected outputs can become inputs for later attachments. The proposer must compute those matches at runtime, never receive a manually selected target-proof family chain.',
            'completeness': 'Proposal enumeration may be bounded as advice, but sampled/limited proposals never supply candidate counts, forced/dead claims or pruning; every primitive fallback remains available.',
            'implementation_gap': 'The accepted lifecycle has root-fixed immutable descriptors. Dynamic descriptor additions, absorbing retirement across updates, source/body bindings, versioned authority and paired rollback require a separately designed and checked protocol before activation.',
            'why_not_immediate': 'The smaller guard-match ordering gate isolates the observed early-prefix defect without changing that registry protocol. Its success is not guaranteed; no automatic budget increase or authored witness insertion on failure.'},
        'executed_scientific_trials': 0, 'new_policy_implemented': False, 'native_queries': 0, 'publication_owner': 'root'}
    nextpath = HERE / 'next-gate-plan-v1.json'; save(nextpath, nextplan)
    files = [pin(Path(__file__)), pin(diagpath), pin(nextpath)]
    manifest = {'status': 'frozen_source_bound_metadata_diagnosis_and_unexecuted_next_gate',
        'files': files, 'total_files': len(files), 'total_bytes': sum(p['bytes'] for p in files),
        'current_search_independent_audit': 'pending', 'new_scientific_execution': False,
        'claim': 'Read-only saved-artifact counts and source diagnosis; future matching/proposal gates are unimplemented and unexecuted.',
        'publication_owner': 'root'}
    manifestpath = HERE / 'manifest-v1.json'; save(manifestpath, manifest)
    print(json.dumps({'diagnosis': pin(diagpath), 'next_plan': pin(nextpath), 'manifest': pin(manifestpath),
                      'preserved': len(preserved), 'observations': len(observations)}, indent=2))


if __name__ == '__main__': main()
