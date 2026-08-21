#!/usr/bin/env python3
"""Regression and leakage checks for the common port-incidence quotient."""

from materials_gcts_iqc_port_incidence_quotient import (
    development_rows, semantic_key, select_spec)


def test_common_quotient_contract():
    rows = development_rows()
    assert len(rows) == 168
    selected, audits = select_spec(rows)
    assert audits and selected.supplied_groups == 9
    assert selected.selected_exact_groups == 4
    assert selected.selected_groups == 4
    assert selected.selected_precision == 1.
    assert selected.recognized_exact_candidates == 20
    assert selected.recognized_candidates == 26
    assert all(len(semantic_key(row["graph"], selected.spec)) == 3
               for row in rows)


if __name__ == "__main__":
    test_common_quotient_contract()
    print("port incidence quotient tests passed")
