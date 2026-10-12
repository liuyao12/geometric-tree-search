"""Resolve frozen curriculum metadata references only; no mathematical engine.

This module is not executed/imported by the source freezer. A future source-
reviewed compiler/independent gate must validate every resolved formula, primitive
license/context, body, complete graph and pool before any trajectory. No proof
word is read or constructed here, and no success feasibility is asserted.
"""
from __future__ import annotations
import copy
import json


def resolve(record, metadata):
    if set(record) == {'literal_ast'}:
        return copy.deepcopy(record['literal_ast'])
    if set(record) != {'metadata_reference'}:
        raise ValueError('exact literal/reference schema required')
    value = metadata
    for token in record['metadata_reference']:
        if type(token) not in (str, int):
            raise ValueError('literal metadata path only')
        value = value[token]
    return copy.deepcopy(value)


def contexts(split, reference_metadata):
    """No outcome/model/trace input and no returned proof commands."""
    result = []
    for record in split['donors']:
        premises = [resolve(item, reference_metadata) for item in record['ordered_hypotheses']]
        target = resolve(record['target'], reference_metadata)
        result.append(dict(id=record['id'], split='donor', theory=copy.deepcopy(reference_metadata['theory_ast']),
                           ordered_hypotheses=premises, target=target, rows=24))
    heldout = split['held_out']
    recipient = dict(id=heldout['id'], split='heldout', theory=copy.deepcopy(reference_metadata['theory_ast']),
        ordered_hypotheses=resolve(heldout['ordered_hypotheses'], reference_metadata),
        target=resolve(heldout['target'], reference_metadata), rows=24)
    canonical = lambda record: json.dumps({k: record[k] for k in ('theory', 'ordered_hypotheses', 'target', 'rows')},
                                         sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    if canonical(recipient) in {canonical(record) for record in result}:
        raise ValueError('held-out context cannot occur among declared donors')
    if len({canonical(record) for record in result}) != len(result):
        raise ValueError('distinct complete donor contexts required')
    return result, recipient
