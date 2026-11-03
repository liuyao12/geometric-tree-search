#!/usr/bin/env python3
"""Fast regression for the scalable materials benchmark."""

from materials_million_atom_benchmark import (
    _fibonacci_training,
    _fit_fibonacci,
    benchmark,
)


def main() -> None:
    result = benchmark(
        represented_atoms=4096,
        training_atoms=256,
        audit_atoms=96,
        materialization="audit",
        seed=731,
    )
    assert result["represented_atoms"] == 4096
    assert {row["family"] for row in result["systems"]} == {
        "crystal", "quasicrystal_model_set", "amorphous_stochastic"
    }
    for row in result["systems"]:
        assert 256 <= row["training_atoms"] <= 1024
        assert row["implicit"]["represented_atoms"] == 4096
        assert row["implicit"]["python_size_bytes"] > 0
        assert row["explicit"]["materialized_atoms"] == 96
        assert row["explicit"]["measured_python_bytes"] > 0
        assert row["structural_fidelity"]["generated_audit"]["atoms"] == 96
        assert row["posthoc_order_classification"]["category"] in {
            "crystal", "polycrystal-like", "quasicrystal-candidate", "amorphous"
        }
        assert row["posthoc_order_classification"]["ordinary_space_group_status"] in {
            "cell-required", "not-applicable"
        }
        assert set(row["marking_ablation"]["conditions"]) == {"marked", "unmarked"}
        assert row["marking_ablation"]["affects_growth_in_this_benchmark"] is False
    crystal = result["systems"][0]
    assert crystal["structural_fidelity"]["errors"]["nearest_distance_relative_error"] < 1e-10
    quasi = result["systems"][1]
    assert quasi["implicit"]["grammar"]["kind"] == "fibonacci_product_substitution"
    assert quasi["implicit"]["grammar"]["species_decoration_source"].startswith(
        "learned")
    assert quasi["implicit"]["grammar"]["species_decoration"]
    amorphous = result["systems"][2]
    assert "known_limitation" in amorphous["implicit"]["grammar"]
    assert result["interpretation"]["claim_not_yet_supported"]

    # The upper advertised training bound must remain a bound for every family,
    # even though 1024 is not a cube of the Fibonacci-product side length.
    positions, species = _fibonacci_training(1024)
    assert len(positions) == len(species) == 1024
    boundary_model = _fit_fibonacci(positions, species)
    assert boundary_model.grammar["image_a"] == "AB"
    assert boundary_model.grammar["image_b"] == "A"
    print("million-atom materials benchmark: all assertions passed")


if __name__ == "__main__":
    main()
