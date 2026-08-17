#!/usr/bin/env python3
"""Measure transfer of ID-free GCTS port channels across IQC nuclei."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment import score_frontier_attachments
from materials_gcts_frontier_attachment_benchmark import (
    _augmented_frontier, _dominant_source_color)
from materials_gcts_iqc_channel_count_confirmation import (
    CONFIRMATION_CENTER as EIGHTH_CENTER)
from materials_gcts_iqc_contextual_value_confirmation import (
    CONFIRMATION_CENTER as NINTH_CENTER)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    CONFIRMATION_CENTER as FOURTH_CENTER, _bounded_proposals,
    fit_multinucleus_marking)
from materials_gcts_iqc_rank_value_confirmation import (
    CONFIRMATION_CENTER as SIXTH_CENTER)
from materials_gcts_iqc_robust_persistent_beam_confirmation import (
    CONFIRMATION_CENTER as FIFTH_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    _open_target, _seed_crop)
from materials_gcts_iqc_three_context_confirmation import (
    CONFIRMATION_CENTER as TENTH_CENTER)
from materials_gcts_persistent_frontier_beam import (
    semantic_channel_descriptor)


TRAIN_CENTERS = (FOURTH_CENTER, FIFTH_CENTER, SIXTH_CENTER,
                 EIGHTH_CENTER, NINTH_CENTER)
HELDOUT_CENTER = TENTH_CENTER


@dataclass(frozen=True)
class NucleusChannelAudit:
    center: tuple[float, float, float]
    candidate_ranks: tuple[int, ...]
    channel_digests: tuple[str, ...]
    port_channel_digests: tuple[str, ...]
    coarse_channel_digests: tuple[str, ...]
    chemistry_channel_digests: tuple[str, ...]
    exact_actions: tuple[bool, ...]
    target_opened_after_channel_freeze: bool


@dataclass(frozen=True)
class SemanticChannelCorpus:
    training_nuclei: int
    heldout_nuclei: int
    training_channel_types: int
    training_exact_channel_types: int
    training_mixed_channel_types: int
    heldout_exact_actions: int
    heldout_exact_actions_with_seen_channel: int
    heldout_exact_actions_with_train_exact_channel: int
    heldout_channel_coverage: float
    heldout_port_channel_coverage: float
    heldout_coarse_channel_coverage: float
    heldout_chemistry_channel_coverage: float
    heldout_exact_actions_with_train_exact_port_channel: int
    heldout_exact_actions_with_train_exact_coarse_channel: int
    heldout_exact_actions_with_train_exact_chemistry_channel: int
    semantic_channel_transfers: bool
    target_used_for_channel_construction: bool
    training: tuple[NucleusChannelAudit, ...]
    heldout: NucleusChannelAudit
    honest_status: str


def _audit_center(center, prototypes, connection, marker, refinement,
                  learned_factor):
    seed = _seed_crop(center)
    proposals = _bounded_proposals(connection, prototypes, seed, center)
    frontier = score_frontier_attachments(
        marker, proposals, seed.positions, seed.species)
    augmented = _augmented_frontier(
        proposals, frontier, seed.positions, seed.species,
        min(len(frontier), 2 * max(1, round(
            len(seed.positions) * learned_factor) - len(seed.positions))))
    scores = score_frontier_attachments(
        refinement, proposals, *augmented)
    levels = sorted(set(scores.values()), reverse=True)[:12]
    frozen = tuple((rank,
        tuple(sorted(point for point, score in scores.items()
                     if abs(score - level) <= 1e-12)))
        for rank, level in enumerate(levels, 1))
    channels = tuple(semantic_channel_descriptor(proposals, band)
                     for _rank, band in frozen)
    port_channels = tuple(semantic_channel_descriptor(
        proposals, band, "port") for _rank, band in frozen)
    coarse_channels = tuple(semantic_channel_descriptor(
        proposals, band, "coarse") for _rank, band in frozen)
    chemistry_channels = tuple(semantic_channel_descriptor(
        proposals, band, "chemistry") for _rank, band in frozen)
    species = tuple(tuple(_dominant_source_color(proposals, point)
                          for point in band) for _rank, band in frozen)

    # The target is unavailable until ranks, sites, colors and channels freeze.
    target = _open_target(center)
    target_colors = {
        tuple(round(value, 6) for value in point): color
        for point, color in zip(target.positions, target.species)}
    exact = tuple(bool(band) and all(
        target_colors.get(tuple(round(value, 6) for value in point)) == color
        for point, color in zip(band, colors))
        for (_rank, band), colors in zip(frozen, species))
    return NucleusChannelAudit(
        tuple(center), tuple(rank for rank, _band in frozen), channels,
        port_channels, coarse_channels, chemistry_channels,
        exact, True)


def evaluate():
    (prototypes, connection, seeds, targets, _proposals, _marker,
     _refinement, robust_marker,
     robust_refinement) = fit_multinucleus_marking()
    learned_factor = sum(len(target.positions) / len(seed.positions)
                         for seed, target in zip(seeds, targets)) / len(seeds)
    training = tuple(_audit_center(
        center, prototypes, connection, robust_marker, robust_refinement,
        learned_factor)
        for center in TRAIN_CENTERS)
    heldout = _audit_center(
        HELDOUT_CENTER, prototypes, connection,
        robust_marker, robust_refinement, learned_factor)

    def stats(field):
        counts = {}
        for audit in training:
            for channel, exact in zip(getattr(audit, field),
                                      audit.exact_actions):
                counts.setdefault(channel, Counter())[exact] += 1
        exact_channels = {channel for channel, count in counts.items()
                          if count[True] and not count[False]}
        mixed = {channel for channel, count in counts.items()
                 if count[True] and count[False]}
        heldout_exact = tuple(channel for channel, exact in zip(
            getattr(heldout, field), heldout.exact_actions) if exact)
        seen = sum(channel in counts for channel in heldout_exact)
        safe = sum(channel in exact_channels for channel in heldout_exact)
        coverage = sum(channel in counts for channel in getattr(
            heldout, field)) / max(1, len(getattr(heldout, field)))
        return counts, exact_channels, mixed, heldout_exact, seen, safe, coverage

    exact_stats = stats("channel_digests")
    port_stats = stats("port_channel_digests")
    coarse_stats = stats("coarse_channel_digests")
    chemistry_stats = stats("chemistry_channel_digests")
    counts, exact_channels, mixed, heldout_exact, seen, safe, coverage = \
        exact_stats
    transfers = bool(heldout_exact) and safe == len(heldout_exact)
    return SemanticChannelCorpus(
        len(training), 1, len(counts), len(exact_channels), len(mixed),
        len(heldout_exact), seen, safe, coverage,
        port_stats[6], coarse_stats[6], chemistry_stats[6],
        port_stats[5], coarse_stats[5], chemistry_stats[5],
        transfers, False,
        training, heldout,
        ("semantic port channels transfer to the heldout nucleus"
         if transfers else
         "exact semantic port channels remain unseen or ambiguous"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
