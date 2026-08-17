#!/usr/bin/env python3
"""Finite train-only calibration of persistent-beam root-rank values."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class RankValueObservation:
    source_digest: str
    correct_sites: tuple[int, ...]
    false_sites: tuple[int, ...]


@dataclass(frozen=True)
class FrozenRankValue:
    maximum_rank: int
    positive_counts: tuple[int, ...]
    total_counts: tuple[int, ...]
    posterior_values: tuple[float, ...]
    source_digests: tuple[str, ...]
    artifact_digest: str
    target_used_during_application: bool

    def as_mapping(self):
        return {rank: self.posterior_values[rank - 1]
                for rank in range(1, self.maximum_rank + 1)}


@dataclass(frozen=True)
class ContextualRankValueObservation:
    previous_rank: int
    observation: RankValueObservation


@dataclass(frozen=True)
class FrozenContextualRankValue:
    contexts: tuple[int, ...]
    models: tuple[FrozenRankValue, ...]
    artifact_digest: str
    maximum_context_order: int
    target_used_during_application: bool

    def as_mapping(self):
        return {context: model.as_mapping()
                for context, model in zip(self.contexts, self.models)}


def fit_rank_value(observations, *, maximum_rank=4,
                   prior_positive=1., prior_negative=1.):
    observations = tuple(observations)
    if (not observations or maximum_rank < 2 or prior_positive <= 0 or
            prior_negative <= 0):
        raise ValueError("invalid rank-value training contract")
    positives = [0] * maximum_rank
    totals = [0] * maximum_rank
    for observation in observations:
        if (not observation.correct_sites or
                len(observation.correct_sites) != len(
                    observation.false_sites) or
                len(observation.correct_sites) > maximum_rank or
                len(observation.source_digest) != 64):
            raise ValueError("rank observation is incomplete")
        for index, (correct, false) in enumerate(zip(
                observation.correct_sites, observation.false_sites)):
            if correct < 0 or false < 0 or not correct + false:
                raise ValueError("rank labels must describe a nonempty action")
            positives[index] += int(correct > 0 and false == 0)
            totals[index] += 1
    posterior = tuple(
        (positive + prior_positive) /
        (total + prior_positive + prior_negative)
        for positive, total in zip(positives, totals))
    payload = (maximum_rank, tuple(positives), tuple(totals), posterior,
               tuple(item.source_digest for item in observations))
    return FrozenRankValue(
        maximum_rank, tuple(positives), tuple(totals), posterior,
        tuple(item.source_digest for item in observations),
        hashlib.sha256(repr(payload).encode()).hexdigest(), False)


def fit_contextual_rank_value(observations, *, maximum_rank):
    observations = tuple(observations)
    if not observations or any(item.previous_rank < 0 for item in observations):
        raise ValueError("contextual rank observations are invalid")
    contexts = tuple(sorted({item.previous_rank for item in observations}))
    models = tuple(fit_rank_value(
        tuple(item.observation for item in observations
              if item.previous_rank == context),
        maximum_rank=maximum_rank) for context in contexts)
    payload = tuple((context, model.artifact_digest)
                    for context, model in zip(contexts, models))
    return FrozenContextualRankValue(
        contexts, models, hashlib.sha256(repr(payload).encode()).hexdigest(),
        1, False)
