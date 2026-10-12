"""SOURCE-ONLY interface sketch for finite automatic family proposals.

This file is not an executor, registry factory, checker or activation adapter.
No scientific function has been implemented or run.  Its immutable records
make the prospective producer boundaries inspectable before ROOT decides
whether to authorize the implementation.  Formula values below are integer
codes in the unchanged finite registry, not new logical axioms.
"""

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class Pin:
    path: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class PrimitiveMember:
    canonical_row: int
    recipe_id: str
    formula_code: int
    ordered_input_rows: tuple[int, ...]


@dataclass(frozen=True)
class FamilyInterface:
    """Every field must be reconstructed from the pinned projection/body pair.

    The existing BodyAuthority drops conclusion metadata.  A future adapter
    must check full_frozen_definition_sha256 against the entire corresponding
    projection, then bind conclusion_row/code to an actual primitive member.
    It must not infer the conclusion by a target name or last-row convention.
    """

    name: str
    body_sha256: str
    source_body_sha256: str
    mapped_body_sha256: str
    full_frozen_definition_sha256: str
    ordered_input_rows: tuple[int, ...]
    ordered_premise_codes: tuple[int, ...]
    primitive_members: tuple[PrimitiveMember, ...]
    conclusion_row: int
    conclusion_code: int


@dataclass(frozen=True)
class RootAnchor:
    """An actual selected root placement, never an empty-row marking."""

    key: tuple[int, int, tuple[int, ...]]
    full_id: str
    formula_code: int
    generation: int


@dataclass(frozen=True)
class InputBinding:
    """Ordered occurrence binding; repeated bindings remain repeated ports.

    root_anchor indexes a frozen actual selected root placement.  Earlier
    output indexes an included prior component's declared conclusion member;
    that member is a conditional primitive obligation until really derived.
    It does not seed a premise or become an established logical fact.
    """

    kind: Literal["root_anchor", "earlier_component_output"]
    index: int


@dataclass(frozen=True)
class ComponentBinding:
    family_name: str
    ordered_inputs: tuple[InputBinding, ...]
    ordered_member_rows: tuple[int, ...]
    descriptor_sha256: str


@dataclass(frozen=True)
class GroupProposal:
    """A union of validated source-body instances, not a new admitted lemma.

    Components preserve ordered provenance even when distinct bodies share
    the same full decorated primitive key.  The eventual compilation adapter
    must bind each component through original BodyAuthority.expected/compile,
    validate the distinct-member t sum and compatible m union, and assign a
    separate proposal-authority epoch without mutating the 171-body authority.
    """

    version: str
    relation: str
    source_plan_pin: Pin
    graph_binding_sha256: str
    original_body_authority_epoch: str
    proposal_authority_epoch: str
    components: tuple[ComponentBinding, ...]
    distinct_member_ids: tuple[str, ...]
    ordered_component_member_ids: tuple[tuple[str, ...], ...]
    aggregate_t: tuple[tuple[int, int, int], ...]
    aggregate_m: tuple[tuple[int, int, int], ...]
    fixed_priority: int
    native_accepted: Literal[False]


@dataclass(frozen=True)
class PreparationReceipt:
    """Completeness is only for the declared bounded proposal grammar."""

    status: Literal["complete_declared_proposal_grammar", "unknown_preparation_budget"]
    family_interfaces_checked: int
    ordered_single_family_types_visited: int
    ordered_two_family_types_visited: int
    exact_binding_tuples_visited: int
    rejected_bindings_by_reason: tuple[tuple[str, int], ...]
    proposal_groups_before_dedup: int
    proposal_groups_after_full_record_dedup: int
    parent_occurrence_records_preserved: int
    preparation_seconds: float
    preparation_peak_bytes: int
    all_primitive_fallback_retained: Literal[True]
    native_queries: Literal[0]


class FrozenProposalAuthority(Protocol):
    """Prospective wrapper boundary expected by the unchanged Controller.

    compile reconstructs the complete expected group from the frozen grammar
    and original bodies.  A self-hash, arbitrary valid keys or copied source
    hashes are not sufficient.  It returns the existing CompiledDescriptor
    type, with the union treated as one whole hint.  This wrapper is NOT yet
    implemented, source reviewed, executed or authoritative.
    """

    graph_text: str
    epoch: str

    def check_graph(self, graph: object) -> None: ...

    def compile(self, graph: object, group: object) -> object: ...


class FrozenFamilyProposalProducer(Protocol):
    """Prospective construction-only interface, not an actual implementation.

    No target formula/name, proof word, outcome or empty-row marking is an
    input.  ROOT must separately freeze the implementation, complete grammar,
    resources, source/input closure and independent gates before it is called.
    """

    def prepare(
        self,
        *,
        graph: object,
        original_authority: object,
        interfaces: tuple[FamilyInterface, ...],
        actual_root_anchors: tuple[RootAnchor, ...],
        source_plan_pin: Pin,
    ) -> tuple[PreparationReceipt, tuple[GroupProposal, ...]]: ...
