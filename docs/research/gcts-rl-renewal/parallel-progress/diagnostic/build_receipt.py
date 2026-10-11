"""Assemble an exact private diagnostic receipt from saved-trace counts only."""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / '.gcts-active/commutativity13-20261011'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def main():
    result = json.loads((HERE/'diagnostic.json').read_text())
    detailed = [json.loads((HERE/(name+'-diagnostic.json')).read_text()) for name in ('fixed-r1','fixed-r2')]
    a, b = detailed
    assert a['events'] == b['events'] and a['nodes'] == b['nodes']
    events, nodes = a['events'], a['nodes']
    expected_structure = '12b0cb0cfd13a90e0a6830293b507dd2d7cc4e97ec7586f5df1831b8fdbddb13'
    for name in ('base-r1','fixed-r1','fixed-r2','base-r2'):
        assert result['source_input_sha256'][str((SOURCE/(name+'-structure.jsonl')).relative_to(ROOT))] == expected_structure
    inherited = {}
    for phase in ('eligible','waiting','invalid','completed'):
        chosen = [n for n in nodes if n['hint_in'] is not None and n['review'] == phase]
        inherited[phase] = dict(visits=len(chosen), distinct_hint_ids=len({n['hint_in'] for n in chosen}))
    probabilities = [e['stochastic_same_pool_probability_of_changing_first'] for e in events]
    fixture = events[4]
    winner = fixture['actions'][fixture['selected']]
    alternative = next(x for x in fixture['actions'] if x['maximum'] and x['changes_first'])
    assert winner['features'] == alternative['features']
    assert winner['eligible'] == [[12,3,10,7]] and alternative['eligible'] == [[12,3,10,10]]
    role_counts = dict(collections.Counter(str(e['point'][1]) for e in events))
    kinds = a['selected_kinds']
    receipt = dict(
        schema='read-only-cluster-action-effect-diagnostic-v1',
        status='passed_saved_trace_source_and_action_reconciliation',
        scope='Artifact diagnostic, not a search/checker/model execution or new scientific outcome. No original file was modified.',
        original_complete_model_sha256='b131949034b0e396ab885a5a94b870f12d1443e2bdc5df0550963ec0e0698c11',
        original_shared_structural_sha256='12b0cb0cfd13a90e0a6830293b507dd2d7cc4e97ec7586f5df1831b8fdbddb13',
        source_input_sha256=result['source_input_sha256'],
        additional_source_sha256={'docs/basic-tiling-algorithm.md':sha(ROOT/'docs/basic-tiling-algorithm.md')},
        diagnostic_files_sha256={name:sha(HERE/name) for name in ('diagnose.py','build_receipt.py','diagnostic.json','fixed-r1-diagnostic.json','fixed-r2-diagnostic.json')},
        consumed_authority='Pinned tree-audit-stream.json: prior independent complete point graph, scheduler, every proposal and hint replay. This task rechecks all saved scores/probabilities/ties, node summaries and exact structural digests; it intentionally does not rerun legality or native computations.',
        census_handling='The reader skips only each census field. All 5,001 node structural projections exactly match saved structure JSONL bytes, and every other original field is retained before counting. Prior complete independent audit supplies omitted census legality authority.',
        projection_warning='fixed-r1-events.json.gz and fixed-r2-events.json.gz in the input directory project prior 12-row traces. They are excluded; this receipt uses actual current 13-row full search JSON.',
        per_fixed_run=dict(
            nodes=5001, attempts=5000, branches=620, forced_nodes=3249, dead_nodes=1132,
            new_policy_events=527, new_valid_eligible_hints=527, chosen_eligible_set_sizes={'1':527},
            nonnull_pool_items=4380, pool_kinds=a['pool_kinds'], selected_kinds=kinds,
            fresh_selected_first_is_base=527, fresh_changed_alternative_order=0,
            fresh_pools_with_different_eligible_first=527, different_first_pool_items=2635,
            fresh_pools_with_different_first_at_maximum_score=474,
            fresh_pools_with_different_first_same_feature_vector_as_winner=474,
            fresh_events_with_any_feature_class_ambiguous_between_first_candidates=sum(e['features_ambiguous_across_first_actions']>0 for e in events),
            deterministic_maximum_tie_events=481, selected_first_pool_item=485, selected_second_pool_item=42,
            selected_input_port_points=477, scheduler_role_counts=role_counts,
            selected_known_source_fraction_zero=sum(e['actions'][e['selected']]['features'][3]==0 for e in events),
            promoted_family_available_events=sum(any(x['kind']=='promoted-family' for x in e['actions']) for e in events),
            waiting_hint_blocks_new_proposal_at_branch=93,
            inherited_hint_reviews=inherited, phases_by_node_kind=a['phases_by_kind'],
            inherited_eligible_at_branch=0, inherited_eligible_at_forced=11,
            visited_children_labeled_member=538, visited_children_labeled_base=4462,
            actual_alternative_reorder_anywhere=0,
            logical_semantic_event_and_review_sha256=hashlib.sha256(packed({'events':events,'nodes':nodes})).hexdigest()),
        interpretation=[
            'Every fresh non-null proposal is valid and touches the scheduler point: ineligibility at launch explains none of the 527 no-ops.',
            'At all fresh branch starts the preferred singleton is already the first base candidate; the complete fallback list is unchanged. At 474 starts a different first candidate has the exact same features and maximum score, but the first-index tie rule favors the base-first landing.',
            'The nine features measure coarse row completion/novelty/known-source fraction and omit distinctions between many input source bindings. Any linear weights give an identical score to an identical feature pair; this does not mean all possible weight choices leave every other action unchanged.',
            'At the other 53 starts a changing action exists but is below the maximum. The first event illustrates the complete-row prefix using all 20 row entries for one landing while other landings appear only as lower-scoring open shapes.',
            'The mandatory scheduler explains continuation no-ops: 93 branch visits keep waiting hints and do not ask for a new proposal; the 11 inherited eligible visits are forced nodes with no choice. The 355 waiting, 1,143 invalid and 460 completed counts are visits, not disjoint outcomes of 527 unique clusters.',
            'Hints are re-reviewed separately on different DFS descendants/siblings. Distinct-ID counts can overlap; all 527 hints become invalid on at least one visited descendant, and 460 complete on at least one descendant. This does not certify a completed theorem.',
            'Both fixed runs are deterministic: stochastic=False, identical fixed weights and deterministic pool/tie order. The repetition seed affects no sampled choice. Repetitions measure costs, not independently randomized policy trajectories.',
            'The exact fixed-run structural identity to both base runs follows from all alternative orders remaining base order, and is confirmed by the complete saved projection hashes. Policy annotations and proposal costs still differ from base.'
        ],
        eligible_effect_witness=dict(
            kind='saved valid-pool ordering counterfactual; no successor execution', event_id=4, preorder_node=39,
            point=[48,3], selected_prefix_size=len(fixture['chosen']),
            base_first=winner['eligible'][0], alternative_first=alternative['eligible'][0],
            winner_pool_index=winner['index'], alternative_pool_index=alternative['index'],
            exact_equal_features=winner['features'], exact_saved_score=winner['score'],
            source_rows=[6,9], source_role_state={str(row):[key for key in fixture['chosen'] if key[0]==row] for row in (6,9)},
            new_order_if_alternative=alternative['eligible']+[key for key in fixture['domain'] if key not in alternative['eligible']],
            original_complete_domain=fixture['domain'],
            interpretation='The two legal bindings select different strict-prior source rows. Row 6 has two unused input ports occupied; row 9 is untouched. Those different partial states have been collapsed by the current feature vector. The preference only reorders the existing domain; it does not remove any candidate or alter scheduler point.'),
        stochastic_feasibility=dict(
            kind='conditional mass computed from already saved, unused softmax probabilities',
            observed_contexts=527, minimum_different_first_mass=min(probabilities), maximum_different_first_mass=max(probabilities),
            mean_different_first_mass_over_saved_contexts=sum(probabilities)/len(probabilities),
            caveat='Not sampled; not an estimated future action frequency or success rate. A changed action changes subsequent contexts. Pool duplicates can bias sampling mass toward one landing.'),
        proposed_next_experiment=dict(
            status='design_only_not_authorized_or_executed_by_this_receipt',
            objective='Test whether genuinely learned cluster selection improves on stochastic exploration after establishing that the policy changes eligible branch order.',
            unchanged='Exact 13-row point model/target/theory, 153 interfaces, 94 admitted definitions, all 19,848 placements and required points/marks, reference dead/forced/earliest-generation scheduler, exact rollback and every base fallback alternative.',
            policy='Stochastic cluster softmax with on-policy learning. Include action-specific source-row occupancy and formula-assignment status, complete source frontier domain counts, and the distant marking dependency neighborhoods from the same graph. Parameterize shared graph/AST features rather than assigning a preferred induction variable, proof line or successful source index.',
            proposal_control='Keep the existing validated pool initially, including irregular open shapes and promoted families. Uniform and learned controls use the identical pool and feature pipeline. Any later stratification by eligible landing to remove duplicate-mass bias is separately frozen and applied to both controls; it must never replace the complete base graph.',
            training='Fresh on-policy rollouts on this assertion, without target proof words, ordinary witness, solver witness, correct-next-action labels or failure-as-unprovability labels. Use all resolved rollouts for RL; retain unknowns. This is per-instance adaptation. Evaluation on fresh seeds is not a held-out-theorem generalization test.',
            learning_signal='Verified satisfied obligations and growth per attempted base placement; penalties for dead-end/backtrack/proposal-validation costs. Never reward the number of macro labels or speculate that an unknown branch is impossible.',
            suggested_initial_training_gate={'episodes':8,'attempt_ceiling_per_episode':500,'search_seconds_per_episode':10,'total_training_producer_seconds':180,'rss_bytes':536870912},
            frozen_evaluation_lanes=['base','untrained_stochastic','trained_stochastic'],
            suggested_balanced_order=['base-r1','untrained-r1','trained-r1','trained-r2','untrained-r2','base-r2'],
            matched_evaluation_limits={'attempts_per_run':5000,'search_seconds_per_run':60,'rss_bytes':536870912,'proposal_items':24,'proposal_validation_checks':2048},
            effect_gate='Independently replay at least one valid preference that changes the selected-point first alternative. Saved event 4 is a minimal conformance fixture only, not a supplied theorem proof or a choice of winning induction variable. Prove fallback/scheduler/rollback equivalence on changed trajectories.',
            scientific_gate='A changed branch establishes policy action, not acceleration. Compare trained versus untrained stochastic seeds and base for independently checked identical result semantics, report all unknowns and full training/setup/proposal/search/serialization/audit costs. No RL-superiority or theorem-native-acceptance claim follows from this diagnostic.',
            continuation_control='Keep waiting-hint persistence unchanged in the first experiment so representation/exploration effects are identifiable. A later replan-while-waiting variant must be a separate policy experiment, with the same mandatory scheduler and complete fallback.'),
        costs=dict(
            read_only_parser_and_count_pass_seconds=result['seconds'], peak_rss_bytes=result['peak_rss_bytes'],
            earlier_read_only_pass_seconds=18.769499958,
            earlier_source_pin_lookup_error='Immediate read-only KeyError before trace parsing: structure source was in the independent audit freeze, not the execution freeze. No engine/solver/query/training ran.',
            costs_are='Diagnostic stage timers; exclude editing, source inspection, final receipt serialization and this assembler. Original producer/setup/proposal/checking costs are preserved verbatim in diagnostic.json observations.',
            scientific_searches=0, solver_calls=0, native_queries=0, model_training_episodes=0),
        limitations=['This receipt deliberately consumes the already passed independent full graph/event replay for legality. It is not a replacement checker or fresh native acceptance.',
                     'Saved-pool counterfactual order and probability are exact, but counterfactual successors, outcome quality and learned weights were not measured.',
                     'All original four searches remain attempt-budget unknown; no new target proof has been discovered.'])
    (HERE/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(status=receipt['status'], receipt_sha256=sha(HERE/'receipt.json'), private_directory=str(HERE))), flush=True)


if __name__ == '__main__':
    main()
