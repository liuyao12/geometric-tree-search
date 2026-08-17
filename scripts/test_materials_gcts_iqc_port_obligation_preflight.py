#!/usr/bin/env python3

import math

from materials_gcts_iqc_port_obligation_preflight import evaluate


def test_port_obligation_preflight_never_opens_a_confirmation_target():
    report = evaluate()
    assert not report.target_or_confirmation_nucleus_accessed
    assert report.seed_actions > 0
    assert report.self_fed_actions > 0
    assert report.preflight_passed == (
        math.isfinite(report.seed_threshold) and
        math.isfinite(report.self_fed_threshold) and
        report.seed_selected_actions >= report.minimum_selected_actions and
        report.self_fed_selected_actions >= report.minimum_selected_actions)
    assert report.minimum_selected_actions == 18
    assert (report.seed_actions, report.seed_positive_actions) == (216, 57)
    assert (report.self_fed_actions,
            report.self_fed_positive_actions) == (216, 48)
    assert (report.seed_selected_actions,
            report.seed_false_actions) == (1, 0)
    assert (report.self_fed_selected_actions,
            report.self_fed_false_actions) == (1, 0)
    assert report.seed_model_digest == \
        "dc8ca626e7074adb82f51231674d183239d26394edc3fd2238573be050d384cb"
    assert report.self_fed_model_digest == \
        "36cd92980b3bf9d1afeb1cc2cfffddafb44c5a8e8d2370bd61d5a36b3d6259b2"
    assert not report.preflight_passed


if __name__ == "__main__":
    test_port_obligation_preflight_never_opens_a_confirmation_target()
    print("IQC port obligation preflight tests: passed")
