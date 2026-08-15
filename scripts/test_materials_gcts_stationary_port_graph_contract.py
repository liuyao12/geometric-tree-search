#!/usr/bin/env python3

from dataclasses import dataclass

from materials_gcts_stationary_port_graph_contract import (
    ColoredPointCloud, EXPECTED_PRODUCTION_KIND, LeakageAudit,
    PromotionWitness, StationaryCallbacks, StationaryCase,
    StationaryProgramAudit, StationaryProductionRejected,
    evaluate_stationary_port_graph_contract)


@dataclass(frozen=True)
class _LineProgram:
    origin: tuple[float, float, float]
    step: tuple[float, float, float]
    initial_atoms: int
    first_species: str
    production_kind: str = EXPECTED_PRODUCTION_KIND


def _cloud(count: int, first_species: str = "O") -> ColoredPointCloud:
    return ColoredPointCloud(
        tuple((float(index), 0.0, 0.0) for index in range(count)),
        tuple(first_species if index == 0 else "A" for index in range(count)))


def _compile(cloud: ColoredPointCloud) -> _LineProgram:
    origins = [index for index, species in enumerate(cloud.species)
               if species == "O"]
    if len(origins) != 1:
        raise StationaryProductionRejected("no unique train-visible root")
    root = origins[0]
    distances = sorted(
        ((sum((left - right) ** 2 for left, right in zip(
            cloud.positions[index], cloud.positions[root])), index)
         for index in range(len(cloud.positions)) if index != root))
    if not distances:
        raise StationaryProductionRejected("too few sites")
    neighbor = distances[0][1]
    step = tuple(cloud.positions[neighbor][axis] -
                 cloud.positions[root][axis] for axis in range(3))
    return _LineProgram(cloud.positions[root], step, len(cloud.positions), "O")


def _audit(program: _LineProgram) -> StationaryProgramAudit:
    witnesses = (
        PromotionWitness(0, 1, "same-port-substitution", 4.0),
        PromotionWitness(1, 2, "same-port-substitution", 4.0),
    )
    return StationaryProgramAudit(
        True, program.production_kind, 3, witnesses, True, 1.0, True, True,
        True, True, True, True, LeakageAudit())


def _execute(program: _LineProgram, seed: ColoredPointCloud,
             actions: int) -> tuple[ColoredPointCloud, ...]:
    assert len(seed.positions) == program.initial_atoms
    result = []
    for action in range(1, actions + 1):
        count = program.initial_atoms * 4 ** action
        positions = tuple(tuple(program.origin[axis] + index *
                                program.step[axis] for axis in range(3))
                          for index in range(count))
        species = tuple("O" if index == 0 else "A"
                        for index in range(count))
        result.append(ColoredPointCloud(positions, species))
    return tuple(result)


def _represented(program: _LineProgram, initial: int, action: int) -> int:
    assert initial == program.initial_atoms
    return initial * 4 ** action


def _signature(program: _LineProgram) -> bytes:
    # The local frame and world origin are intentionally absent.
    return (f"{program.production_kind}:{program.initial_atoms}:4:" +
            program.first_species).encode()


def _callbacks(audit=_audit) -> StationaryCallbacks:
    return StationaryCallbacks(
        _compile, audit, _execute, _represented, _signature)


def _cases() -> tuple[StationaryCase, ...]:
    seed = _cloud(256)
    references = (_cloud(1024), _cloud(4096))
    return tuple(StationaryCase(role, seed, references)
                 for role in ("crystal", "ideal_iqc", "cdyb"))


def test_complete_stationary_contract_can_pass_through_callbacks() -> None:
    result = evaluate_stationary_port_graph_contract(
        _cases(), _cloud(17, "X"), _callbacks())
    assert result.required_roles_present_once
    assert result.one_generic_production_kind
    assert result.amorphous_stationary_production_rejected
    assert result.all_leakage_audits_clean
    assert result.all_metamorphic_audits_passed
    assert result.benchmark_passed
    for case in result.cases:
        assert case.adjacent_stationary_scales_observed
        assert case.exact_first_two_levels
        assert case.first_three_growth_factors == (4.0, 4.0, 4.0)
        assert case.first_million_action == 6


def test_one_observed_scale_and_leakage_remain_honestly_red() -> None:
    def red_audit(program: _LineProgram) -> StationaryProgramAudit:
        base = _audit(program)
        return StationaryProgramAudit(
            base.deterministic, base.production_kind, 2,
            base.promotion_witnesses[:1], base.complete_training_cover,
            base.repeated_training_coverage, base.finite_oriented_ports,
            base.causal_local_marking, base.self_fed_execution,
            base.unique_overlap_counting,
            base.independent_symbolic_count_verified,
            base.explicit_materialization_is_linear,
            LeakageAudit(target_enumerator_used_for_growth=True))

    result = evaluate_stationary_port_graph_contract(
        _cases(), _cloud(17, "X"), _callbacks(red_audit))
    assert not result.benchmark_passed
    assert not result.all_leakage_audits_clean
    assert all(not case.adjacent_stationary_scales_observed
               for case in result.cases)
    assert all(not case.hierarchy_depth_at_least_three
               for case in result.cases)


def test_cross_family_aliases_cannot_substitute_for_required_roles() -> None:
    duplicate = tuple(StationaryCase("crystal", case.training,
                                     case.explicit_references)
                      for case in _cases())
    result = evaluate_stationary_port_graph_contract(
        duplicate, _cloud(17, "X"), _callbacks())
    assert not result.required_roles_present_once
    assert not result.benchmark_passed


def test_growth_threshold_is_strict_and_million_deadline_is_inclusive() -> None:
    def only_three(program: _LineProgram, initial: int, action: int) -> int:
        assert initial == program.initial_atoms
        return initial * 3 ** action

    callbacks = StationaryCallbacks(
        _compile, _audit, _execute, only_three, _signature)
    result = evaluate_stationary_port_graph_contract(
        _cases(), _cloud(17, "X"), callbacks)
    assert not result.benchmark_passed
    for case in result.cases:
        assert case.first_three_growth_factors == (3.0, 3.0, 3.0)
        assert not case.three_actions_above_three
        assert case.first_million_action is None
        assert not case.million_within_seven_actions


if __name__ == "__main__":
    test_complete_stationary_contract_can_pass_through_callbacks()
    test_one_observed_scale_and_leakage_remain_honestly_red()
    test_cross_family_aliases_cannot_substitute_for_required_roles()
    test_growth_threshold_is_strict_and_million_deadline_is_inclusive()
    print("stationary recurring port-graph contract: all assertions passed")
