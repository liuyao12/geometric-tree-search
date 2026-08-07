#!/usr/bin/env python3

from materials_gcts_fibonacci_3d import evaluate


def main() -> None:
    result = evaluate()
    assert result.input_atoms == 729
    assert result.learned_image_a == "AB"
    assert result.learned_image_b == "A"
    assert result.grown_atoms == 42875
    assert result.gcts_axis_accuracy == 1.0
    assert result.gcts_species_accuracy == 1.0
    assert result.maximum_coordinate_error < 1e-12
    assert result.gcts_axis_accuracy > result.strongest_periodic_axis_accuracy
    assert result.gcts_species_accuracy > result.strongest_periodic_species_accuracy
    assert result.local_overlap_forced < result.local_overlap_hidden
    assert result.local_overlap_forced_accuracy == 1.0
    assert result.hierarchical_spatial_accuracy > result.hybrid_markov_spatial_accuracy
    print("3D Fibonacci inflation growth: all assertions passed", result)


if __name__ == "__main__":
    main()
