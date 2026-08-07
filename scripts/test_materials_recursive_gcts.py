#!/usr/bin/env python3

from materials_recursive_gcts import evaluate


def main() -> None:
    result = evaluate()
    for structured in (result.crystal, result.quasicrystal):
        assert structured.atoms >= 500
        assert structured.rotation_invariant
        assert structured.levels[0].recurring_types > 0
        assert structured.levels[-1].largest_recurring_support > 0
        assert structured.levels[-1].learned_marking_types > 0

    assert result.crystal.geometric_amplification
    assert result.quasicrystal.geometric_amplification
    assert result.amorphous.levels[0].recurring_center_fraction < 0.1
    assert not result.amorphous.geometric_amplification

    print("recursive GCTS hierarchy: all assertions passed")
    print(result)


if __name__ == "__main__":
    main()
