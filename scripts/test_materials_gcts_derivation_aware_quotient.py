#!/usr/bin/env python3

from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import (
    fit_derivation_alternative_marking, quotient_macro_supports,
    rank_derivation_alternatives)


configuration, _ = oracle_patch(3, 9.)
atomic = compile_irregular_port_program(
    configuration.species, configuration.positions)
mined = mine_port_graph_macros(atomic, maximum_nodes=3)
quotient = quotient_macro_supports(mined.macro_types)

assert len(quotient.derivation_classes) == quotient.quotient_types
assert len(quotient.alternative_macros) == quotient.source_types
assert sum(len(item.alternatives) for item in quotient.derivation_classes) == (
    quotient.source_types)
assert all(item.occurrences and all(occurrence.alternatives
                                    for occurrence in item.occurrences)
           for item in quotient.derivation_classes)
assert all(macro.promotion_derivations for macro in quotient.quotient_macros)

marking = fit_derivation_alternative_marking(quotient)
assert marking.training_samples >= quotient.retained_promotion_occurrences
assert not marking.target_used
for geometry in quotient.derivation_classes:
    ranked = rank_derivation_alternatives(
        quotient, marking, geometry.geometry_class_id)
    assert set(ranked) == {item.alternative_id
                           for item in geometry.alternatives}

# Both modes preserve exact colored geometry. The optimistic mode is explicitly
# diagnostic; the safe mode assigns mutually exclusive derivations distinct
# promoted types.
optimistic = promote_macro_types(
    atomic, quotient.quotient_macros, union_derivation_witnesses=True)
safe = promote_macro_types(atomic, quotient.alternative_macros)
assert optimistic.prototypes
assert safe.prototypes
assert not optimistic.target_used and not safe.target_used

print("derivation-aware exact-support quotient: all assertions passed")
