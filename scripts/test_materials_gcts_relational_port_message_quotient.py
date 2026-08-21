#!/usr/bin/env python3

from dataclasses import asdict

from materials_gcts_iqc_port_incidence_metric import metric_rows
from materials_gcts_relational_port_message_quotient import (
    RelationalMessageSpec, fit_relational_port_quotient,
    relational_message_features, score_relational_port_quotient,
    species_palette)


def test_feature_schema_and_group_balancing():
    corpus = metric_rows()
    graph = corpus[0]["graph"]
    palette = species_palette(row["graph"] for row in corpus)
    names, values, domains = relational_message_features(graph, palette)
    assert len(names) == len(values) == len(domains) == 216
    assert len(set(names)) == 216
    assert domains.count("nodes") == 159
    assert domains.count("edges") == 57

    rows = tuple({"graph": graph, "group": group, "fit_label": label}
                 for group, label in ((0, True), (1, False), (2, True)))
    spec = RelationalMessageSpec("all", 3, 2, 8, "top", .55)
    model = fit_relational_port_quotient(rows, spec, palette=palette)
    duplicated = fit_relational_port_quotient(
        (*rows, *({"graph": graph, "group": 0, "fit_label": True}
                  for _ in range(20))), spec, palette=palette)
    assert tuple((row.feature_name, row.bin_index, row.posterior)
                 for row in model.states) == tuple((
                     row.feature_name, row.bin_index, row.posterior)
                     for row in duplicated.states)
    assert score_relational_port_quotient(model, graph) == .6
    serialized = repr(asdict(model))
    assert "candidate_id" not in serialized
    assert model.target_used is False
    assert model.candidate_geometry_changed is False


def main():
    test_feature_schema_and_group_balancing()
    print("relational port message quotient tests passed")


if __name__ == "__main__":
    main()
