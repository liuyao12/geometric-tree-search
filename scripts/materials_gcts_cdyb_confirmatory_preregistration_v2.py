#!/usr/bin/env python3
"""Complete target-free preregistration for one-shot Cd--Yb confirmation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


SOURCE_COMMIT = "51090f27da810177f3b68c1cb3ebd90b4b17efe4"
PROTOCOL_V1_DIGEST = \
    "1f3c286fbc870307db1c158b9f7b5ed097c36681dc9403fe01c35888916e6204"
TRAIN_AUDIT_DIGEST = \
    "0796c2e60517fbf475ea383f1cc86b2f6cdd38efa2cad7f7c85b5818c3112c62"
TRAIN_CORPUS_MANIFEST_DIGEST = \
    "b59613a8be3f9d334e56642328bae41d40fb1c60b7bc93a84335f449bf4392d7"
TRAIN_CORPUS_DIGEST = \
    "d4ddc8ae825f0e8919a2fd107633b32931dceca44bade4b6f6e2370fec675542"
FROZEN_MODEL_DIGEST = \
    "da3aef6b32bbf69ce4013d846e1535a1d90521db446404c10c5dd3fcedf67dbe"

FROZEN_SOURCE_FILE_HASHES = (
    ("materials_gcts_cdyb_continuous_completion_marking.py",
     "1f4d654f7ce10c4aeca873c0ac878f7bb690aede7e2ab0814fbbaabd9144b1dd"),
    ("materials_gcts_partial_completion_executor.py",
     "066f52d08bb58e8d04ccdba76aede9af27506fb5479075b4cf8bf60089d2bdd7"),
    ("materials_gcts_partial_completion_execution_policy.py",
     "e314c1a508b30bd8e80dd3d6fac350b4c18f8ab77a00a63be6f8925e0e918f17"),
    ("materials_gcts_partial_promoted_frontier.py",
     "697141acb7de24a665675d6ecec994fa36e0aab8ad2589a7d2d96ac96813d83f"),
    ("materials_gcts_partial_completion_marking.py",
     "e62655a2cd0baf9a307b43de3ab8dd9bd3171b1b7564d59a8a6f3e4e74217341"),
)

FEATURE_NAMES = (
    "matched_child_fraction", "log_emitted_atoms", "log_macro_atoms",
    "species_entropy", "macro_radial_rms_nn", "macro_radial_cv",
    "log_port_evidence", "log_boundary_slots", "mean_boundary_frequency",
    "log_incoming_port_kinds")

FROZEN_CORPUS_MANIFEST = {
    "train_windows": 5, "base_frontiers": 5,
    "expanded_frontiers_considered": 35,
    "seed_shift_nn": 0.6714953619981409,
    "base_candidates": 14, "base_positive": 8, "base_negative": 6,
    "base_negative_roles": 2, "expanded_candidates": 28,
    "expanded_positive": 14, "expanded_negative": 14,
    "expanded_negative_roles": 3, "expanded_corpus_admitted": True,
    "admitted_candidates": 28, "admitted_positive": 14,
    "admitted_negative": 14, "feature_names": FEATURE_NAMES,
}

FROZEN_MODEL_MANIFEST = {
    "feature_names": FEATURE_NAMES,
    "means": (0.5, 3.1706736225731116, 3.430077639751079,
              0.46283921080967466, 7.151470499725585,
              0.32064472729538174, 4.232382174528115,
              2.6723152258426164, 0.6979449122306265,
              0.392361531667182),
    "scales": (1e-09, 0.24718869252552064, 0.18913265940595644,
               0.029792371158580733, 0.6651326424687124,
               0.03384140142469168, 0.9276355188675144,
               0.6010661542788321, 0.10264668917441239,
               0.5264082339382531),
    "weights": (0.0, -0.43006250973441656, 0.4731201859644888,
                0.43174363392065956, 0.3693907767157498,
                -0.8539121367066874, 0.8187037202009871,
                0.8012283067346325, -0.6873339416436661,
                0.6978218575646064),
    "intercept": -0.15306891383457402, "ridge_lambda": 1.0,
    "target_used": False, "id_family_cell_origin_features_used": False,
}

CORPUS_MANIFEST_FIELDS = tuple(FROZEN_CORPUS_MANIFEST)


def _canonical_digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CdYbConfirmatoryProtocolV2:
    version: str
    source_commit: str
    protocol_v1_digest: str
    train_audit_digest: str
    train_corpus_manifest_digest: str
    train_corpus_digest: str
    frozen_model_digest: str
    feature_names: tuple[str, ...]
    frozen_source_file_hashes: tuple[tuple[str, str], ...]
    expanded_shift_corpus_admitted: bool
    shift_rule: str
    independent_training_groups: int
    ranking_rule: str
    comparison_arms: tuple[str, ...]
    probability_threshold: float | None
    top_budget_per_wave: int
    maximum_waves_per_level: int
    maximum_hierarchy_levels: int
    public_boundary_radius: float
    first_wave_candidate_ids_identical_across_arms: bool
    later_wave_candidate_divergence_expected: bool
    shuffle_trials: int
    shuffle_seed_rule: str
    shuffle_strata: str
    shuffle_refit_rule: str
    null_tail_rule: str
    metric_definitions: tuple[tuple[str, str], ...]
    primary_gate_definition: str
    sustained_growth_gate_definition: str
    minimum_action_precision: float
    minimum_site_precision: float
    minimum_recoverable_action_recall: float
    maximum_empirical_p: float
    minimum_work_reduction: float
    minimum_self_fed_depth: int
    minimum_outer_atom_recall: float


PROTOCOL_V2 = CdYbConfirmatoryProtocolV2(
    "cdyb-partial-macro-confirmation-v2", SOURCE_COMMIT,
    PROTOCOL_V1_DIGEST, TRAIN_AUDIT_DIGEST, TRAIN_CORPUS_MANIFEST_DIGEST,
    TRAIN_CORPUS_DIGEST, FROZEN_MODEL_DIGEST, FEATURE_NAMES,
    FROZEN_SOURCE_FILE_HASHES, True,
    "per training window: origin and +/- one frozen train-NN along x,y,z",
    5, "descending frozen continuous-model score; stable candidate key tie",
    ("marked: frozen continuous model", "unmarked: stable candidate key",
     "diagnostic: frozen macro-frequency baseline",
     "nulls: within-window shuffled-label refits"),
    None, 5, 3, 4, 25.0, True, True, 31,
    "trial seed = 912701 + zero-based trial index",
    "permute action labels only within each original training-window ID",
    "for each null, refit the same standardized ridge-logistic procedure "
    "and grouped-lambda rule on the shuffled train labels",
    "exact-actions/sites: upper p=(1+count(null>=marked))/32; matched-work "
    "checks: lower p=(1+count(null<=marked))/32; ties count",
    (
        ("action_precision", "posthoc exact accepted actions / all accepted actions"),
        ("site_precision", "unique correct emitted sites / unique emitted sites"),
        ("recoverable_action_recall", "posthoc exact accepted marked actions / all exact actions in the common frozen first-wave candidate set"),
        ("matched_work", "scan each frozen first-wave order until it reaches the marked top-5 arm's unique-correct-site union count; statistic is proposal checks and lower is better"),
        ("matched_work_reduction", "unmarked matched-work checks / marked matched-work checks; gate fails if unmarked cannot reach the marked correct-site count"),
        ("self_fed_depth", "number of consecutive nonempty accepted waves across levels whose next frontier uses committed children"),
        ("outer_atom_recall", "unique correct emitted sites at R>14 / scorer target sites with 14<R<=25"),
    ),
    "marked versus stable unmarked and shuffled nulls: all precision, "
    "recoverable-recall, three plus-one p, and matched-work gates; frozen "
    "macro frequency is reported as a diagnostic but cannot replace a gate",
    "primary gate AND self_fed_depth and outer_atom_recall gates",
    .80, .95, .50, .05, 2.0, 3, .20)


def protocol_v2_digest() -> str:
    return _canonical_digest(asdict(PROTOCOL_V2))


def audit_frozen_manifests() -> dict:
    return {
        "source_commit": SOURCE_COMMIT,
        "protocol_v1_digest": PROTOCOL_V1_DIGEST,
        "corpus_digest": _canonical_digest(FROZEN_CORPUS_MANIFEST),
        "corpus_manifest_digest_matches":
            _canonical_digest(FROZEN_CORPUS_MANIFEST) ==
            TRAIN_CORPUS_MANIFEST_DIGEST,
        "actual_training_corpus_digest": TRAIN_CORPUS_DIGEST,
        "model_digest": _canonical_digest(FROZEN_MODEL_MANIFEST),
        "model_digest_matches":
            _canonical_digest(FROZEN_MODEL_MANIFEST) == FROZEN_MODEL_DIGEST,
        "target_or_oracle_imported": False,
    }


def audit_frozen_source_files(directory) -> tuple[tuple[str, bool], ...]:
    root = Path(directory)
    return tuple((name, hashlib.sha256((root / name).read_bytes()).hexdigest()
                  == expected) for name, expected in FROZEN_SOURCE_FILE_HASHES)


def derive_train_artifact_digests(train_audit) -> dict:
    """Reproduce frozen hashes from the authorized train-only audit object."""
    payload = asdict(train_audit)
    model = payload.pop("frozen_model")
    corpus = {field: payload[field] for field in CORPUS_MANIFEST_FIELDS}
    return {
        "train_audit_digest": _canonical_digest(
            {"audit": payload, "model": model}),
        "train_corpus_manifest_digest": _canonical_digest(corpus),
        "train_corpus_digest": payload.get("training_corpus_digest", ""),
        "frozen_model_digest": _canonical_digest(model),
        "all_match": (
            _canonical_digest({"audit": payload, "model": model}) ==
            TRAIN_AUDIT_DIGEST and
            _canonical_digest(corpus) == TRAIN_CORPUS_MANIFEST_DIGEST and
            payload.get("training_corpus_digest") == TRAIN_CORPUS_DIGEST and
            _canonical_digest(model) == FROZEN_MODEL_DIGEST),
    }


def plus_one_upper_tail(marked: float, null_values) -> float:
    values = tuple(float(value) for value in null_values)
    if len(values) != PROTOCOL_V2.shuffle_trials:
        raise ValueError("confirmatory null requires exactly 31 trials")
    return (1 + sum(value >= marked for value in values)) / (len(values) + 1)


def plus_one_lower_tail(marked: float, null_values) -> float:
    values = tuple(float(value) for value in null_values)
    if len(values) != PROTOCOL_V2.shuffle_trials:
        raise ValueError("confirmatory null requires exactly 31 trials")
    return (1 + sum(value <= marked for value in values)) / (len(values) + 1)


@dataclass(frozen=True)
class ConfirmatoryMetrics:
    action_precision: float
    site_precision: float
    recoverable_action_recall: float
    exact_action_p: float
    correct_site_p: float
    matched_work_p: float
    matched_work_reduction: float
    self_fed_depth: int
    outer_atom_recall: float


def evaluate_preregistered_gates(metrics: ConfirmatoryMetrics) -> tuple[bool, bool]:
    primary = all((
        metrics.action_precision >= PROTOCOL_V2.minimum_action_precision,
        metrics.site_precision >= PROTOCOL_V2.minimum_site_precision,
        metrics.recoverable_action_recall >=
        PROTOCOL_V2.minimum_recoverable_action_recall,
        metrics.exact_action_p <= PROTOCOL_V2.maximum_empirical_p,
        metrics.correct_site_p <= PROTOCOL_V2.maximum_empirical_p,
        metrics.matched_work_p <= PROTOCOL_V2.maximum_empirical_p,
        metrics.matched_work_reduction >= PROTOCOL_V2.minimum_work_reduction,
    ))
    sustained = (primary and
                 metrics.self_fed_depth >= PROTOCOL_V2.minimum_self_fed_depth and
                 metrics.outer_atom_recall >=
                 PROTOCOL_V2.minimum_outer_atom_recall)
    return primary, sustained


class OneShotOrderGuard:
    """Injectable single-use target latch; tests use a harmless fake factory."""

    def __init__(self):
        self.events = []
        self.target_factory_calls = 0
        self.execution_digest = None
        self._target_open = False

    def record(self, event: str, digest: str = "") -> None:
        if self._target_open:
            raise RuntimeError("no fitting, ranking, or execution after target open")
        allowed = (
            "protocol-verified", "training-artifacts-verified", "model-frozen",
            "seed-opened", "first-wave-candidates-frozen", "controls-frozen",
            "execution-frozen")
        if event not in allowed:
            raise ValueError("unknown one-shot event")
        if len(self.events) >= len(allowed) or event != allowed[len(self.events)]:
            raise RuntimeError("one-shot events must follow preregistered order")
        self.events.append((event, digest))
        if event == "execution-frozen":
            self.execution_digest = digest

    def open_target(self, factory):
        required = (
            "protocol-verified", "training-artifacts-verified", "model-frozen",
            "seed-opened", "first-wave-candidates-frozen", "controls-frozen",
            "execution-frozen")
        if tuple(event for event, _digest in self.events) != required:
            raise RuntimeError("target cannot open before every artifact freezes")
        if self.target_factory_calls:
            raise RuntimeError("confirmatory target factory is single-use")
        self.target_factory_calls += 1
        self._target_open = True
        self.events.append(("target-opened", ""))
        return factory()

    def record_score(self, execution_digest: str) -> None:
        if not self._target_open or self.target_factory_calls != 1:
            raise RuntimeError("scoring requires exactly one target opening")
        if execution_digest != self.execution_digest:
            raise RuntimeError("execution changed after target opening")
        if any(event == "scored" for event, _digest in self.events):
            raise RuntimeError("one-shot result may be scored only once")
        self.events.append(("scored", execution_digest))

    def audit(self) -> dict:
        return {
            "events": tuple(self.events),
            "target_factory_calls": self.target_factory_calls,
            "execution_frozen_before_target": bool(self.execution_digest),
            "scored_once": sum(event == "scored" for event, _ in self.events) == 1,
        }
