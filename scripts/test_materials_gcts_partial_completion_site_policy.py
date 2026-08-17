#!/usr/bin/env python3
"""Feature parity and execution controls for frozen local-site sections."""

from materials_gcts_cdyb_site_resolved_completion_section import (
    FEATURE_NAMES, FrozenSiteSection, _site_features,
    aggregate_action_confidence, score_site_confidence)
from materials_gcts_oriented_overlap_ports import ClusterOccurrence, IDENTITY
from materials_gcts_partial_completion_executor import _dynamic_program
from materials_gcts_partial_completion_marking import freeze_completion_candidate
from materials_gcts_partial_completion_sections import (
    execute_partial_completion_sections, freeze_completion_sections)
from materials_gcts_partial_completion_site_policy import (
    adapt_frozen_site_section, completion_site_feature_context,
    completion_site_features, score_completion_sections,
    score_site_features)
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from test_materials_gcts_partial_completion_sections import _section_fixture


def _frozen_frontier():
    seed_prototype, level = _section_fixture()
    seed = (ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),)
    dynamic = _dynamic_program(level.frozen_lower_program, seed, 1e-6)
    frontier = enumerate_partial_promoted_completions(
        dynamic, level.alternatives, minimum_matched_children=1,
        explicit_seed_sites=seed_prototype.sites,
        frozen_parent_types=level.alternative_parent_types,
        pose_tolerance=1e-6)
    completion = frontier.completions[0]
    macro = level.alternatives[0]
    candidate = freeze_completion_candidate(
        dynamic, macro, completion, pose_tolerance=1e-6)
    sections = freeze_completion_sections(
        dynamic, macro, completion, candidate,
        occupied_sites=seed_prototype.sites, pose_tolerance=1e-6)
    return seed_prototype, level, seed, dynamic, macro, completion, candidate, sections


def test_generic_features_exactly_match_train_module():
    (seed_prototype, _level, _seed, dynamic, macro, completion,
     candidate, sections) = _frozen_frontier()
    context = completion_site_feature_context(
        dynamic, macro, completion, candidate, seed_prototype.sites, 1e-6)
    feature_rows = []
    for section in sections:
        for site in section.sites:
            actual = completion_site_features(site, context)
            expected = _site_features(
                site, context["emitted_sites"], context["seed_sites"],
                context["witness_sites"], context["full_sites"],
                context["multiplicity"], completion, macro, candidate,
                dynamic.minimum_distance)
            assert actual == expected
            feature_rows.append(actual)
    model = FrozenSiteSection(
        FEATURE_NAMES, tuple(index / 10 for index in range(10)),
        tuple(1 + index / 10 for index in range(10)),
        tuple((index - 4) / 20 for index in range(10)),
        -.2, .1, "lower-quartile", False, False)
    policy = adapt_frozen_site_section(model)
    train_scores = tuple(score_site_confidence(model, row)
                         for row in feature_rows)
    assert train_scores == tuple(score_site_features(policy, row)
                                 for row in feature_rows)
    scored = score_completion_sections(
        policy, sections, dynamic, macro, completion, candidate,
        seed_prototype.sites, 1e-6)
    for section_score in scored:
        assert section_score.aggregate_score == aggregate_action_confidence(
            model, tuple(score for _key, score in section_score.site_scores))


def test_frozen_site_section_selects_subset_without_changing_enumeration():
    seed_prototype, level, seed, *_rest = _frozen_frontier()
    raw_model = FrozenSiteSection(
        FEATURE_NAMES, (0.,) * len(FEATURE_NAMES),
        (1.,) * len(FEATURE_NAMES),
        (0., 0., -1.) + (0.,) * (len(FEATURE_NAMES) - 3),
        6., .1, "minimum", False, False)
    policy = adapt_frozen_site_section(raw_model)
    baseline = execute_partial_completion_sections(
        level, seed, explicit_seed_sites=seed_prototype.sites,
        maximum_waves=1, pose_tolerance=1e-6)
    marked = execute_partial_completion_sections(
        level, seed, explicit_seed_sites=seed_prototype.sites,
        marking=policy, minimum_marking_score=.5,
        maximum_waves=1, pose_tolerance=1e-6)
    assert baseline.waves[0].whole_candidate_ids == \
        marked.waves[0].whole_candidate_ids
    assert baseline.waves[0].whole_candidate_digest == \
        marked.waves[0].whole_candidate_digest
    assert baseline.waves[0].section_ids == marked.waves[0].section_ids
    assert baseline.waves[0].section_digest == marked.waves[0].section_digest
    assert marked.waves[0].accepted_sections == 1
    assert marked.waves[0].deferred_below_threshold == 1
    assert len({round(score, 12) for _section, score in
                marked.waves[0].section_scores}) == 2
    assert marked.exact_certificates and not marked.target_used


def test_tainted_site_section_fails_closed():
    model = FrozenSiteSection(
        FEATURE_NAMES, (0.,) * len(FEATURE_NAMES),
        (1.,) * len(FEATURE_NAMES), (0.,) * len(FEATURE_NAMES),
        0., .1, "mean", True, False)
    try:
        adapt_frozen_site_section(model)
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted site section was admitted")


if __name__ == "__main__":
    test_generic_features_exactly_match_train_module()
    test_frozen_site_section_selects_subset_without_changing_enumeration()
    test_tainted_site_section_fails_closed()
    print("partial completion site policy: passed")
