#!/usr/bin/env python3

from types import SimpleNamespace

from materials_gcts_iqc_stage_local_marking_portfolio import (
    execute_iqc_stage_local_marking_portfolio)


def _candidate(name, positions, rollout):
    state = SimpleNamespace(positions=tuple(positions),
                            species=tuple("X" for _ in positions))
    return SimpleNamespace(action_key=(name,), rollout_score=rollout,
                           state=state)


def stub_executor(_runtime, _prefix, _rollout, *, seed_positions, **_kwargs):
    root = not seed_positions
    rows = (_candidate("connection-head", ((1., 0., 0.),), .1),
            _candidate("rollout-head", ((0., 1., 0.),), .9)) if root else (
            _candidate("next-a", seed_positions + ((1., 1., 0.),), .2),
            _candidate("next-b", seed_positions + ((0., 0., 1.),), .8))
    return SimpleNamespace(candidates=rows,
                           candidate_digest=f"digest:{len(seed_positions)}",
                           target_api_present=False, target_used=False)


def test_iqc_adapter_preserves_both_marking_heads_target_free():
    result = execute_iqc_stage_local_marking_portfolio(
        None, None, None, center=(0., 0., 0.), seed_positions=(),
        seed_species=(), public_radius=10., blocks=1, beam_width=2,
        block_executor=stub_executor)
    assert result.expansion_candidate_counts == (2,)
    assert set(result.tree.levels[0].retained_action_paths) == {
        (("connection-head",),), (("rollout-head",),)}
    assert not result.target_api_present and not result.target_used


def test_iqc_adapter_self_feeds_every_retained_marking_state():
    result = execute_iqc_stage_local_marking_portfolio(
        None, None, None, center=(0., 0., 0.), seed_positions=(),
        seed_species=(), public_radius=10., blocks=2, beam_width=2,
        block_executor=stub_executor)
    assert result.expansion_candidate_counts == (2, 2, 2)
    assert len(result.tree.levels) == 2
    assert len(result.tree.retained) == 2
    assert all(len(node.state.positions) == 2 for node in result.tree.retained)


def test_target_taint_fails_closed():
    def tainted(*_args, **_kwargs):
        return SimpleNamespace(candidates=(), candidate_digest="bad",
                               target_api_present=True, target_used=False)
    try:
        execute_iqc_stage_local_marking_portfolio(
            None, None, None, center=(0., 0., 0.), seed_positions=(),
            seed_species=(), public_radius=10., blocks=1, beam_width=2,
            block_executor=tainted)
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted expansion was accepted")


if __name__ == "__main__":
    test_iqc_adapter_preserves_both_marking_heads_target_free()
    test_iqc_adapter_self_feeds_every_retained_marking_state()
    test_target_taint_fails_closed()
    print("IQC stage-local marking portfolio adapter tests passed")
