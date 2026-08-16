#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_autonomous_growth_contract import (
    ColoredGrowthScore, FrozenAutonomousTrace, audit_contract,
    audit_growth_case, execute_then_open_target)
from materials_gcts_autonomous_growth_benchmark import evaluate


def _passing_trace():
    return FrozenAutonomousTrace(
        "fixture", "generic", "recurring_port_graph_macro",
        "0" * 64, "1" * 64, "2" * 64, ("3" * 64,),
        (2, 3, 4), (20, 80, 400),
        True, True, 3, False, True, 0, 9, 3, (),
        (("A", (0., 0., 0.)),),
        True, 10, 20, 18, .03125,
        (10, 40, 200, 1000, 1_200_000), True, False, False)


def test_contract_has_independent_hard_gates():
    score = ColoredGrowthScore(100, 100, 100, 1., 1.)
    base = audit_growth_case(
        _passing_trace(), score, role="crystal",
        target_constructed_after_trace_frozen=True)
    assert base.autonomous_case_passed
    mutations = (
        (replace(_passing_trace(), self_fed=False), score),
        (replace(_passing_trace(), promoted_cluster_of_cluster_actions=0),
         score),
        (replace(_passing_trace(), marked_work=19), score),
        (replace(_passing_trace(), symbolic_counts=(10, 20, 30)), score),
        (replace(_passing_trace(), target_used_during_compile_or_execution=True),
         score),
        (_passing_trace(), replace(score, recall=.5)),
    )
    assert all(not audit_growth_case(
        trace, candidate_score, role="crystal",
        target_constructed_after_trace_frozen=True).autonomous_case_passed
               for trace, candidate_score in mutations)
    combined = audit_contract((
        base, replace(base, system="iqc", role="quasicrystal")),
        amorphous_rejected=True)
    assert combined.benchmark_passed


def test_target_factory_is_called_only_after_trace_freeze():
    events = []

    def execute(_train, _seed):
        events.append("execute")
        return replace(_passing_trace(), trace_digest="")

    def open_target():
        events.append("target")
        return object()

    def score(trace, _target):
        assert len(trace.trace_digest) == 64
        events.append("score")
        return ColoredGrowthScore(1, 1, 1, 1., 1.)

    trace, _score, mechanically_enforced = execute_then_open_target(
        object(), object(), executor=execute, target_factory=open_target,
        scorer=score)
    assert events == ["execute", "target", "score"]
    assert len(trace.trace_digest) == 64
    assert mechanically_enforced


def test_current_real_executors_remain_below_authoritative_gate():
    result = evaluate()
    assert result.roles_present == ("crystal", "quasicrystal")
    assert result.amorphous_rejected
    crystal, iqc = result.cases
    assert crystal.precision_recall_gate
    assert crystal.causal_self_feed_gate
    assert crystal.sustained_autonomous_growth_gate
    assert crystal.symbolic_amplification_gate
    assert not crystal.generic_clusters_of_clusters_gate
    assert not crystal.marking_ablation_gate
    assert .91 < iqc.precision < .93
    # The executor genuinely self-feeds, but the disjoint R11 frontier stalls
    # The sealed IQC continuation is genuinely self-fed to depth two, but it
    # reaches a fixed point. Batch scheduling can change the displayed number
    # of waves without changing the final atom union.
    assert iqc.causal_self_feed_gate
    assert not iqc.sustained_autonomous_growth_gate
    assert not iqc.precision_recall_gate
    assert iqc.generic_clusters_of_clusters_gate
    assert not iqc.marking_ablation_gate
    assert not iqc.symbolic_amplification_gate
    assert iqc.leak_free
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_contract_has_independent_hard_gates()
    test_target_factory_is_called_only_after_trace_freeze()
    test_current_real_executors_remain_below_authoritative_gate()
    print("autonomous material-growth contract: all assertions passed")
