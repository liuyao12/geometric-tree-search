"""Prospective typed API only; no engine import or runtime adapter implementation.

The existing root-fixed Controller stays unchanged. ROOT's separately audited
single/pair wrapper supplies these immutable records and paired checkpoints.
Opaque keys are the original exact geometry/arithmetic candidate identities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class FamilyPoolRecord:
    identifier: str
    kind: str  # source-single, source-composed-pair; open-builder is a later lane
    source_provenance: tuple
    members: tuple
    ordered_receptor_ports: tuple
    aggregate_t: tuple
    aggregate_m: tuple
    full_identity_preimages: tuple
    model_epoch: str
    authority_epoch: str
    compiled_descriptor_ids: tuple
    native_accepted: bool  # literal existing authority, never inferred by policy


@dataclass(frozen=True)
class AvailableFact:
    row: int
    formula: Any
    ordered_source_rows: tuple
    physically_selected_roles: tuple
    dependency_complete: bool
    context_epoch: str
    primitive_license_binding: str


@dataclass(frozen=True)
class FamilyMenu:
    pool_epoch: str
    decision: tuple
    complete_base_domain_sha256: str
    action_ids: tuple  # canonical sorted IDs, including explicit NULL
    records: tuple
    feature_vectors: tuple
    feature_schema_sha256: str
    source_available_facts_sha256: str
    proposal_budget_status: str


@dataclass(frozen=True)
class PairedPoolCheckpoint:
    root_controller_checkpoint: tuple
    pool_epoch: str
    pool_revision: int
    active_descriptor_id: str | None
    active_controller_view_checkpoint: tuple | None
    all_hint_states_sha256: str
    graph_and_pool_semantic_sha256: str
    branch_exclusions_sha256: str


class AuditedFamilyPoolBridge(Protocol):
    """Interface requirements; scientific implementation is deliberately absent.

    Menus are advice. Global dead/forced/earliest decisions and every legal base
    key come from the unchanged point graph. Complete fallback and all remote
    assigned-zero/absence dependencies remain in that graph. Selecting a family
    activates preference only; it never establishes an external premise/fact.
    """

    def current_global_decision(self) -> tuple: ...

    def complete_base_candidates(self, decision: tuple) -> tuple: ...

    def dependency_complete_facts(self) -> tuple[AvailableFact, ...]: ...

    def ready_menu(self, decision: tuple) -> FamilyMenu: ...

    def revalidate_exact_whole_record(self, record: FamilyPoolRecord) -> bool: ...

    def activate_existing_record(self, identifier: str | None) -> None: ...

    def preferred_eligible_members(self, decision: tuple) -> tuple: ...

    def after_primitive_graph_step(self) -> None: ...

    def checkpoint(self) -> PairedPoolCheckpoint: ...

    def rollback(self, checkpoint: PairedPoolCheckpoint) -> None: ...

    def semantic_projection(self) -> dict: ...


class ProspectiveOpenConstructionBridge(Protocol):
    """Deferred topology/membership construction, distinct from pool selection.

    A future source freeze must supply complete action-pool and transaction
    semantics. This API does not claim an existing model supports these calls.
    """

    def legal_scheduler_anchors(self, decision: tuple) -> tuple: ...

    def append_actions(self, members: tuple, ordered_ports: tuple) -> tuple: ...

    def bind_external_port_actions(self, members: tuple, port: int) -> tuple: ...

    def validate_commit(self, members: tuple, ordered_ports: tuple) -> FamilyPoolRecord | None: ...
