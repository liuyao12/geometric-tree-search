#!/usr/bin/env python3
"""Finite train-only prototype marking for local GCTS incidence graphs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample)


@dataclass(frozen=True)
class IncidenceCodebookSpec:
    token_families: tuple[str, ...]
    nearest_prototypes: int = 1
    minimum_groups: int = 1


@dataclass(frozen=True)
class FrozenIncidenceCodebook:
    spec: IncidenceCodebookSpec
    prototypes: tuple[tuple[tuple[str, frozenset[Hashable]], ...], ...]
    training_groups: int


def incidence_codebook_view(descriptor: CandidateIncidenceDescriptor,
                            families: tuple[str, ...]):
    selected = {family: set() for family in families}
    for token in descriptor.tokens:
        if not isinstance(token, tuple) or not token:
            continue
        family = token[0]
        if family in selected:
            selected[family].add(token)
    return tuple((family, frozenset(selected[family]))
                 for family in families)


def _canonical_view(view):
    return tuple((family, tuple(sorted(tokens, key=repr)))
                 for family, tokens in view)


def fit_incidence_codebook(
        examples: Sequence[IncidenceTokenExample], *,
        spec: IncidenceCodebookSpec) -> FrozenIncidenceCodebook:
    if (not examples or not spec.token_families or
            len(set(spec.token_families)) != len(spec.token_families) or
            spec.nearest_prototypes < 1 or spec.minimum_groups < 1):
        raise ValueError("invalid incidence codebook settings")
    positive = tuple(row for row in examples if row.successful)
    if not positive:
        raise ValueError("incidence codebook needs positive actions")
    groups_by_view = {}
    for row in positive:
        view = incidence_codebook_view(row.descriptor, spec.token_families)
        groups_by_view.setdefault(view, set()).add(row.group)
    prototypes = tuple(sorted((
        view for view, groups in groups_by_view.items()
        if len(groups) >= spec.minimum_groups),
        key=lambda view: repr(_canonical_view(view))))
    if not prototypes:
        raise ValueError("no recurrent positive incidence prototypes")
    return FrozenIncidenceCodebook(
        spec, prototypes, len({row.group for row in examples}))


def _family_balanced_similarity(left, right) -> float:
    scores = []
    for (left_family, left_tokens), (right_family, right_tokens) in zip(
            left, right):
        if left_family != right_family:
            raise ValueError("incompatible incidence codebook schemas")
        union = left_tokens | right_tokens
        if not union:
            continue
        scores.append(len(left_tokens & right_tokens) / len(union))
    return sum(scores) / len(scores) if scores else 0.


def score_incidence_codebook(
        codebook: FrozenIncidenceCodebook,
        descriptor: CandidateIncidenceDescriptor) -> float:
    view = incidence_codebook_view(
        descriptor, codebook.spec.token_families)
    return score_incidence_codebook_view(codebook, view)


def score_incidence_codebook_view(
        codebook: FrozenIncidenceCodebook, view) -> float:
    similarities = incidence_codebook_similarities(codebook, view)
    selected = similarities[:codebook.spec.nearest_prototypes]
    return sum(selected) / len(selected) if selected else 0.


def incidence_codebook_similarities(
        codebook: FrozenIncidenceCodebook, view) -> tuple[float, ...]:
    return tuple(sorted((
        _family_balanced_similarity(view, prototype)
        for prototype in codebook.prototypes), reverse=True))


def incidence_codebook_digest(codebook: FrozenIncidenceCodebook) -> str:
    payload = (codebook.spec, tuple(
        _canonical_view(view) for view in codebook.prototypes),
        codebook.training_groups)
    return hashlib.sha256(repr(payload).encode()).hexdigest()
