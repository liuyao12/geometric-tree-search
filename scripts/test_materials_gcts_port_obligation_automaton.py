#!/usr/bin/env python3

from materials_gcts_port_obligation_automaton import (
    PortObligationAutomatonSpec, fit_port_obligation_automaton,
    score_port_obligation_trajectory, transition_symbol)


def _transition(*, lost=0, produced=0, reverse=True):
    relations = {name: {"lost": lost if name == "forward" else 0,
                        "gained": 0, "after": 1}
                 for name in ("backward", "forward", "reverse",
                              "same_parent", "same_source",
                              "touch_parent", "touch_source")}
    return {
        "selected_role_transitions": [{
            "before": 2, "after": 1, "discharged": 1,
            "produced": produced,
            "contradiction_flags": {
                "forward_depleted": bool(lost),
                "no_forward_after": False,
                "no_reverse_after": not reverse,
                "no_touch_source_after": False,
                "source_touch_depleted": False,
            },
            "relation_counts": relations,
            # Raw role identity is intentionally ignored.
            "role": ("forged-id", (99,), "other-id", (101,), 123),
        }],
        "selected_pair_relations": [],
    }


def test_group_balance_and_weakest_link():
    good = _transition()
    bad = _transition(lost=1)
    rows = (
        {"group": 0, "fit_label": True, "transitions": (good, good)},
        {"group": 1, "fit_label": True, "transitions": (good,)},
        {"group": 2, "fit_label": False, "transitions": (bad,)},
    )
    model = fit_port_obligation_automaton(rows)
    good_score, good_coverage = score_port_obligation_trajectory(
        model, (good, good))
    bad_score, bad_coverage = score_port_obligation_trajectory(model, (bad,))
    assert good_score == .75 and bad_score == 1 / 3
    assert good_coverage == bad_coverage == 1.
    duplicated = fit_port_obligation_automaton(
        rows + tuple(dict(rows[0]) for _ in range(20)))
    duplicate_score, _ = score_port_obligation_trajectory(
        duplicated, (good,))
    assert duplicate_score == good_score
    assert model.target_used is False
    assert model.candidate_geometry_changed is False


def test_symbol_is_bounded_and_identity_free():
    spec = PortObligationAutomatonSpec(count_cap=4)
    left = _transition(produced=99)
    right = _transition(produced=8)
    assert transition_symbol(left, spec) == transition_symbol(right, spec)
    altered = dict(left)
    altered["selected_role_transitions"] = [dict(
        left["selected_role_transitions"][0],
        role=("completely", (0,), "different", (0,), 0))]
    assert transition_symbol(left, spec) == transition_symbol(altered, spec)
    doubled = dict(left)
    doubled["selected_role_transitions"] = list(reversed(
        left["selected_role_transitions"] * 2))
    expected = transition_symbol(doubled, spec)
    doubled["selected_role_transitions"].reverse()
    assert transition_symbol(doubled, spec) == expected
    model = fit_port_obligation_automaton((
        {"group": 0, "fit_label": True, "transitions": (left,)},
        {"group": 1, "fit_label": False, "transitions": (right,)},
    ))
    assert "forged-id" not in repr(model.states)


def main():
    test_group_balance_and_weakest_link()
    test_symbol_is_bounded_and_identity_free()
    print("port obligation automaton tests passed")


if __name__ == "__main__":
    main()
