#!/usr/bin/env python3

from materials_gcts_semantic_action_quotient import (
    ExactActionTerminal, SemanticDescriptor,
    select_semantic_action_quotient)
from materials_gcts_oriented_overlap_ports import IDENTITY
from dataclasses import replace


def _terminal(index, distances=(1., 1.4, 1.8)):
    return ExactActionTerminal(
        f"patch-{index:02d}", f"exact-alternative-{index:02d}",
        ("directed-path", 3), ("A|exact", "B|exact", "C|exact"),
        distances, (("X", index, 0, 0),),
        ((0, IDENTITY, (index * .3, 0., 0.)),), (("out",),))


def test_semantic_grammar_pools_but_preserves_every_exact_terminal():
    result = select_semantic_action_quotient(
        tuple(_terminal(index) for index in range(18)),
        descriptors=(SemanticDescriptor("semantic", "exact", .25, 1),),
        required_deployments=16)
    assert result.selected_descriptor is not None
    assert result.types_with_required_deployments == 1
    grammar = result.grammar_types[0]
    assert grammar.independent_patches == 18
    assert len(grammar.exact_alternatives) == 18
    assert grammar.exact_replay_payload_complete
    assert result.exact_terminals_preserved
    assert not result.approximate_grammar_called_exact
    assert not result.strict_stationarity_claimed


def test_topology_only_is_rejected_when_controls_compress_equally_well():
    result = select_semantic_action_quotient(
        tuple(_terminal(index) for index in range(18)),
        descriptors=(SemanticDescriptor("topology", "terminal", None, 1),))
    assert result.selected_descriptor is None
    assert not result.grammar_types
    assert "controls" in result.reason


def test_action_adapter_is_invariant_to_input_child_order():
    from materials_gcts_action_macro_promotion import promote_batch_action_macros
    from materials_gcts_action_submacro_mining import ActionMacroCorpusEntry
    from materials_gcts_semantic_action_quotient import (
        terminals_from_action_corpus)
    from test_materials_gcts_action_macro_promotion import (
        _synthetic_three_wave_result)
    program, batch = _synthetic_three_wave_result()
    macro = max(promote_batch_action_macros(program, batch).macros,
                key=lambda item: len(item.children))
    order = tuple(reversed(range(len(macro.children))))
    remap = {old: new for new, old in enumerate(order)}
    permuted = replace(
        macro, children=tuple(macro.children[index] for index in order),
        edges=tuple(replace(edge, source=remap[edge.source],
                            target=remap[edge.target])
                    for edge in macro.edges),
        boundary_slots=tuple(replace(slot, child=remap[slot.child])
                             for slot in macro.boundary_slots))
    left = terminals_from_action_corpus(
        program, (ActionMacroCorpusEntry("patch", macro),))
    right = terminals_from_action_corpus(
        program, (ActionMacroCorpusEntry("patch", permuted),))
    signature = lambda values: sorted((
        item.exact_key, item.topology_key, item.chemistry_roles,
        item.normalized_distances, item.exact_children) for item in values)
    assert signature(left) == signature(right)


def test_selected_records_compile_to_exact_execution_alternatives():
    from materials_gcts_oriented_overlap_ports import make_prototype
    from materials_gcts_semantic_action_quotient import (
        adapt_quotient_production, production_records)
    from materials_gcts_semantic_production_grammar import (
        compile_from_semantic_quotient)
    result = select_semantic_action_quotient(
        tuple(_terminal(index) for index in range(18)),
        descriptors=(SemanticDescriptor("semantic", "exact", .25, 1),),
        required_deployments=16)
    prototypes = (make_prototype(0, (
        ("X", (0., 0., 0.)), ("X", (.1, 0., 0.)),
        ("X", (0., .1, 0.)))),)
    grammar = compile_from_semantic_quotient(
        prototypes, production_records(result), adapt_quotient_production,
        overlap_tolerance=1e-6, exclusion_distance=.05)
    assert len(grammar.alternatives) == 18
    assert len({item.semantic_parent_type
                for item in grammar.alternatives}) == 1
    assert all(item.atom_union and item.inclusion_certificate_digest
               for item in grammar.alternatives)


if __name__ == "__main__":
    test_semantic_grammar_pools_but_preserves_every_exact_terminal()
    test_topology_only_is_rejected_when_controls_compress_equally_well()
    test_action_adapter_is_invariant_to_input_child_order()
    test_selected_records_compile_to_exact_execution_alternatives()
    print("semantic action quotient: all assertions passed")
