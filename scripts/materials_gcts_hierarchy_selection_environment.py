#!/usr/bin/env python3
"""RL-facing exact hierarchy selection environment and beam comparator."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurring_action_submacro_audit import (
    PromotedSubmacroLevel, audit_promoted_submacro_levels)


@dataclass(frozen=True)
class HierarchySelectionAction:
    subset_rule: str
    derivation_policy: str
    selected_types: int
    source_quotient_types: int
    exact_cover_fraction: float
    mdl_saving: int


@dataclass(frozen=True)
class HierarchyStepScore:
    reward: float
    exact_cover_fraction: float
    promoted_occurrences: int
    overlap_relations: int
    boundary_relations: int
    mdl_saving: int


@dataclass(frozen=True)
class FrozenHierarchySelection:
    actions: tuple[HierarchySelectionAction, ...]
    step_scores: tuple[HierarchyStepScore, ...]
    cumulative_reward: float
    fixed_horizon_score: float
    unfilled_level_penalty: float
    positive_levels: int
    final_program: Any
    stationary: bool
    stationary_witnesses: int
    strict_stationarity_gate_external: bool
    exact_replay_gate_external: bool
    target_used_for_selection: bool


@dataclass(frozen=True)
class HeldoutHierarchyScore:
    available: bool
    sampled_occurrences: int
    pose_fit_failures: int
    covered_target_atoms: int
    target_atoms: int
    target_used_for_selection: bool
    unavailable_reason: str


@dataclass(frozen=True)
class _BeamState:
    artifact: Any
    actions: tuple[HierarchySelectionAction, ...]
    scores: tuple[HierarchyStepScore, ...]
    levels: tuple[PromotedSubmacroLevel, ...]
    cumulative_reward: float
    terminated: bool


def _support_cover(macros):
    return {atom for macro in macros
            for occurrence in (macro.promotion_occurrences or
                                macro.occurrences)
            for atom in occurrence.atom_indices}


def _selections(quotient):
    representatives = tuple(quotient.quotient_macros)
    if not representatives:
        return ()
    ranked = tuple(sorted(representatives, key=lambda item: (
        -item.mdl_saving, -len(item.promotion_occurrences or item.occurrences),
        item.dictionary_tokens, item.macro_id)))
    values = [("all", "representative", representatives),
              ("all", "alternative-consistent",
               tuple(quotient.alternative_macros))]
    for fraction, label in ((.75, "top-75pct"), (.5, "top-50pct")):
        count = max(1, math.ceil(len(ranked) * fraction))
        values.append((label, "representative", ranked[:count]))
    unique = {}
    for subset, policy, macros in values:
        key = policy, tuple((item.macro_id, tuple(item.node_types))
                            for item in macros)
        unique.setdefault(key, (subset, policy, macros))
    return tuple(unique.values())


def _advance(state, depth):
    mined = mine_port_graph_macros(
        state.artifact, maximum_nodes=3, include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    if not quotient.quotient_macros:
        return ( _BeamState(
            state.artifact, state.actions, state.scores, state.levels,
            state.cumulative_reward, True), )
    source_cover = _support_cover(quotient.quotient_macros)
    result = []
    for subset_rule, policy, macros in _selections(quotient):
        selected_cover = _support_cover(macros)
        cover_fraction = len(selected_cover & source_cover) / max(1,
                                                                  len(source_cover))
        try:
            promoted = promote_macro_types(
                state.artifact, macros,
                level=getattr(state.artifact, "level", 0) + 1)
        except ValueError:
            continue
        overlap = len(promoted.atlas.relation_classes)
        boundary = len(promoted.boundary_relation_classes)
        mdl = sum(item.mdl_saving for item in macros)
        # Fixed train-only reward: exact cover dominates, followed by future
        # witnessed connectivity and compression. No stationary label or
        # heldout score enters branch selection.
        reward = (100. * (cover_fraction - 1.) +
                  math.log1p(max(0, mdl)) +
                  2. * math.log1p(overlap + boundary) +
                  math.log1p(len(promoted.occurrences)) -
                  .02 * len(macros) - 20.)
        action = HierarchySelectionAction(
            subset_rule, policy, len(macros), quotient.quotient_types,
            cover_fraction, mdl)
        score = HierarchyStepScore(
            reward, cover_fraction, len(promoted.occurrences), overlap,
            boundary, mdl)
        # The semantic level remains the quotient geometry vocabulary even
        # when execution keeps mutually exclusive derivations separate.
        level = PromotedSubmacroLevel(
            depth, state.artifact, tuple(quotient.quotient_macros))
        result.append(_BeamState(
            promoted, state.actions + (action,), state.scores + (score,),
            state.levels + (level,), state.cumulative_reward + reward, False))
    return tuple(result)


def beam_select_hierarchy(initial_program, *, beam_width=3,
                          maximum_levels=8):
    """Deterministic future-RL comparator using only train artifacts."""
    if beam_width < 1 or maximum_levels < 1:
        raise ValueError("beam width and level limit must be positive")
    beam = (_BeamState(initial_program, (), (), (), 0., False),)
    for depth in range(maximum_levels):
        expanded = tuple(child for state in beam
                         for child in (_advance(state, depth)
                                       if not state.terminated else (state,)))
        beam = tuple(sorted(expanded, key=lambda item: (
            -(item.cumulative_reward -
              10. * max(0, depth + 1 - len(item.actions))),
            -len(item.actions),
            tuple((action.subset_rule, action.derivation_policy)
                  for action in item.actions)))[:beam_width])
        if all(item.terminated for item in beam):
            break
    def fixed_score(item):
        return item.cumulative_reward - 10. * (
            maximum_levels - len(item.actions))
    winner = max(beam, key=lambda item: (fixed_score(item),
                                         len(item.actions)))
    strict = audit_promoted_submacro_levels(winner.levels)
    return FrozenHierarchySelection(
        winner.actions, winner.scores, winner.cumulative_reward,
        fixed_score(winner), 10. * (maximum_levels - len(winner.actions)),
        len(winner.actions), winner.artifact, strict.stationary,
        len(strict.witnesses), True, True, False)


def greedy_select_hierarchy(initial_program, *, maximum_levels=8):
    """Comparator constrained to the existing all-representative action."""
    state = _BeamState(initial_program, (), (), (), 0., False)
    for depth in range(maximum_levels):
        children = _advance(state, depth)
        choices = tuple(item for item in children
                        if (not item.actions or
                            item.actions[-1].subset_rule == "all" and
                            item.actions[-1].derivation_policy ==
                            "representative"))
        state = choices[0] if choices else children[0]
        if state.terminated:
            break
    strict = audit_promoted_submacro_levels(state.levels)
    return FrozenHierarchySelection(
        state.actions, state.scores, state.cumulative_reward,
        state.cumulative_reward - 10. * (
            maximum_levels - len(state.actions)),
        10. * (maximum_levels - len(state.actions)),
        len(state.actions), state.artifact, strict.stationary,
        len(strict.witnesses), True, True, False)


def score_frozen_hierarchy_on_heldout(selection, species, positions):
    """Post-freeze occurrence transfer; never feeds selection reward."""
    from materials_gcts_irregular_port_atlas import (
        enumerate_frozen_port_occurrences)
    if not hasattr(selection.final_program, "vocabulary"):
        return HeldoutHierarchyScore(
            False, 0, 0, 0, len(positions),
            selection.target_used_for_selection,
            "oriented transfer fixture accepts primitive irregular programs, "
            "not promoted macro vocabularies")
    result = enumerate_frozen_port_occurrences(
        selection.final_program, species, positions,
        select_greedy_cover=True)
    covered = {atom for _, support in result.occurrence_supports
               for atom in support}
    return HeldoutHierarchyScore(
        True, len(result.occurrences), result.pose_fit_failures, len(covered),
        len(positions), selection.target_used_for_selection, "")
