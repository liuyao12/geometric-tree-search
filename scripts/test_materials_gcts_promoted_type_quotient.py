#!/usr/bin/env python3
"""False-positive controls and real IQC check for support quotienting."""

from dataclasses import replace

from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports


configuration, _ = oracle_patch(3, 9.0)
atomic = compile_irregular_port_program(
    configuration.species, configuration.positions)
mined = mine_port_graph_macros(atomic, maximum_nodes=3)
quotient = quotient_macro_supports(mined.macro_types)
assert quotient.source_types == 75
assert quotient.quotient_types == 32
assert quotient.retained_promotion_occurrences == 87
assert quotient.exact_train_support_cover_preserved
assert quotient.exact_geometry_preserved
assert quotient.chemistry_population_preserved
assert not quotient.uniform_scale_merged
assert not quotient.improper_reflections_merged
promoted = promote_macro_types(atomic, quotient.quotient_macros)
assert len(promoted.prototypes) == 32
assert promoted.pose_fit_failures == 0

# A deliberately colored scalene tetrahedron has a proper-frame handedness.
# Proper rotation is admissible; reflection, chemistry changes, and a scale
# change are not execution equivalences.
base = mined.macro_types[0]
sites = (("A", (0., 0., 0.)), ("B", (1., 0., 0.)),
         ("C", (.2, 1.3, 0.)), ("D", (.1, .3, 1.7)))
rotated = tuple((species, (-point[1], point[0], point[2]))
                for species, point in sites)
mirrored = tuple((species, (-point[0], point[1], point[2]))
                 for species, point in sites)
scaled = tuple((species, tuple(2.0 * value for value in point))
               for species, point in sites)
changed = tuple(("X" if species == "D" else species, point)
                for species, point in sites)

proper = quotient_macro_supports((
    replace(base, macro_id=0, atom_union=sites),
    replace(base, macro_id=1, atom_union=rotated)))
assert proper.quotient_types == 1
for counterexample in (mirrored, scaled, changed):
    controlled = quotient_macro_supports((
        replace(base, macro_id=0, atom_union=sites),
        replace(base, macro_id=1, atom_union=counterexample)))
    assert controlled.quotient_types == 2
scale_control = quotient_macro_supports((
    replace(base, macro_id=0, atom_union=sites),
    replace(base, macro_id=1, atom_union=scaled)))
assert scale_control.scale_similar_but_not_congruent_pairs == 1

print("train-only promoted support quotient: all assertions passed")
