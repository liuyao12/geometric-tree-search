"""Metadata-only retrospective normalization of one terminal actual phase.

The frozen60/180s and512MiB caps are unchanged. No compiler/engine/oracle
imports, scientific calls, retries, discounts or outcome-conditioned settings.
The original predictive envelope, including any UNKNOWN, is immutable history.
The full already-measured dispatcher lifetime includes its original normalized
receipt-byte serialization/close and process exit/reap. This successor receipt
and its own metadata costs are additional to that historical phase.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
SELECTORS=('donor-two-guards','donor-two-equalities','donor-repeated-guard',
           'donor-repeated-equality','heldout-mixed-guard-equality')


def need(value,label):
    if not value:raise ValueError(label)


def pin(path,declared=None):
    path=Path(path);h=hashlib.sha256();n=0
    with path.open('rb') as stream:
        for raw in iter(lambda:stream.read(65536),b''):h.update(raw);n+=len(raw)
    return dict(path=str(path.relative_to(ROOT)) if declared is None else declared,sha256=h.hexdigest(),bytes=n)


def read(path):return json.loads(Path(path).read_text())


def read_pin(record):
    need(set(record)=={'path','sha256','bytes'},'exact raw three-field pin')
    path=Path(record['path']);path=path if path.is_absolute() else ROOT/path
    need(pin(path,record['path'])==record,'immutable actual raw byte identity')
    return read(path)


def bounded(value,maximum):
    return type(value) in (int,float) and math.isfinite(value) and 0<=value<=maximum


def save(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    began=time.perf_counter();phase,selector=sys.argv[1:]
    need(phase in ('preparation','static') and selector in SELECTORS,'literal frozen phase/context')
    stem=phase+'-'+selector;target=HERE/(stem+'-measured-ROOT-terminal-v2.json')
    audit_path=HERE/(stem+'-metadata-normalization-v1.json')
    need(not target.exists() and not audit_path.exists(),'one immutable metadata normalization; no retry')
    external_path=HERE/(stem+'-external-launcher-v1.json');external=read(external_path)
    need(external['schema']=='ROOT-context-gate-external-launcher-observation-v1'
         and external['phase']==phase and external['selector']==selector
         and external['owner_exit_code']==0 and external['owner_terminal_reaped'] is True
         and external['interruption'] is None,'fully measured clean one-shot dispatcher terminal')
    original_pin=external['terminal'] if external['accepted_for_metadata_finalization'] is True else external['rejected_terminal']
    need(original_pin is not None,'actual original normalization preserved')
    original=read_pin(original_pin);observation=read_pin(external['post_write_observation'])
    need(original['schema']=='ROOT-actual-frozen-curriculum-'+phase+'-terminal-v1'
        and original['selector']==selector and original['owner_exit_code']==0
        and original['owner_terminal_reaped'] is True and original['worker_terminal_reaped'] is True
        and original['full_resource_accepted'] is True and original['failure'] is None
        and original['error'] is None and original['live_owned_descendants_after_owner_reap']==[],
        'original clean measured phase and descendants, no failed scientific owner or cleanup')
    need(observation['accepted_for_metadata_finalization'] is True
        and observation['reserve_validated'] is True and observation['memory_reserve_validated'] is True
        and observation['terminal']['sha256']==original_pin['sha256']
        and observation['terminal']['bytes']==original_pin['bytes'], 'original receipt bytes and successful local post-write check')
    full=external['full_dispatcher_process_seconds_including_startup_imports_final_write_exit_reap']
    peak=external['observer_inclusive_phase_plus_launcher_peak_estimate_bytes']
    reconstructed_peak=(observation['conservative_peak_after_receipt_serialization_bytes']+external['launcher_peak_bytes']
        +max(0,external['dispatcher_kernel_peak_bytes']-observation['peak_after_receipt_serialization_bytes']))
    maximum=60 if phase=='preparation' else 180
    need(peak==reconstructed_peak and bounded(full,maximum) and bounded(peak,536870912),
         'full unchanged frozen observed wall/memory caps; retain conservative terminal growth, no discount')
    need(original['maximum_seconds']==maximum and original['maximum_bytes']==536870912,
         'unchanged prospective phase ceilings')
    if external['accepted_for_metadata_finalization'] is False:
        need(full<=original['full_outer_seconds_including_receipt_write']
            and peak>original['conservative_combined_peak_bytes'], 'failed auxiliary prediction is only memory envelope underreporting')
    for name in ('dispatcher','launcher'):read_pin(external[name])
    # Python sources are bytes, not JSON. Verify them without decoding/imports.
    review=read_pin(original['ROOT_source_review'])
    need(review['full_sources_reviewed'] is True and review['source_review_passed'] is True
        and review['scientific_calls']==0,'original full source review')
    for rec in review['source_records']:
        path=ROOT/rec['path'];need(pin(path,rec['path'])=={k:rec[k] for k in ('path','sha256','bytes')},'source still frozen')
    required=('preparation_plan','compiled_context','preparation_evidence','outcome','lifetime','supervision','activation') if phase=='preparation' else (
        'static_plan','static_result','static_lifetime','static_activation','independent_source_plan')
    raw={name:read_pin(original[name]) for name in required if name not in ('compiled_context','preparation_evidence')}
    for name in ('compiled_context','preparation_evidence') if phase=='preparation' else ():
        rec=original[name];need(pin(ROOT/rec['path'])==rec,'complete gzip artifact bytes; no model decoding')
    if phase=='preparation':
        need(raw['lifetime']['status']=='passed_full_fresh_context_preparation_lifetime'
            and raw['lifetime']['supervisor_reaped'] is True and raw['lifetime']['worker_reaped_confirmed'] is True
            and raw['lifetime']['supervisor_exit']==0 and raw['lifetime']['cleanup_reason'] is None
            and raw['supervision']['child_reaped'] is True and raw['supervision']['child_exit']==0
            and raw['supervision']['resource_reason'] is None and raw['supervision']['watchdog_error'] is None,
            'actual complete inner ownership/resource statuses')
        need(raw['outcome']['target_searches']==0 and raw['outcome']['native_queries']==0
            and raw['outcome']['new_RL_training'] is False,'unchanged preparation scope')
    else:
        need(original['static_context_pool_accepted'] is True and raw['static_result']['static_context_pool_accepted'] is True
            and raw['static_lifetime']['child_reaped'] is True and raw['static_lifetime']['child_exit']==0,
            'actual independent static result and ownership')
    normalized=dict(original)
    normalized.update(full_outer_seconds_including_receipt_write=full,conservative_combined_peak_bytes=peak,
        original_external_envelope_accepted=external['accepted_for_metadata_finalization'],
        original_predictive_envelope_receipt=original_pin,full_measured_external_launcher=pin(external_path),
        original_post_write_observation=external['post_write_observation'],metadata_normalizer=pin(Path(__file__)),
        normalization_successor='Retrospective exact historical measured resource normalization; original failed auxiliary envelope remains failed. No scientific rerun or setting/cap change.',
        timing_kind='Already measured full historical dispatcher startup/import/original receipt write/exit/reap. This successor metadata write is additional.',
        memory_scope='Retain the exact conservative full external observation including launcher and terminal kernel growth; no XNU discount or OS hard-cap claim.')
    save(target,normalized);elapsed=time.perf_counter()-began
    save(audit_path,dict(schema='ROOT-metadata-only-measured-context-normalization-v1',phase=phase,selector=selector,
        status='accepted_historical_full_measured_phase_resources_original_envelope_preserved',
        measured_terminal=pin(target),original_terminal=original_pin,external_launcher=pin(external_path),
        post_write_observation=external['post_write_observation'],normalizer=pin(Path(__file__)),
        metadata_seconds_through_successor_terminal_write=elapsed,
        scientific_calls=0,scientific_retries=0,original_external_envelope_accepted=external['accepted_for_metadata_finalization'],
        actual_phase_scientific_acceptance='Pending separate independent static gate; no mathematical/proof/RL acceptance by normalization',
        own_cost_scope='Additional standard JSON/hash metadata work; original historical charged phase was not rerun. This audit serialization is additional unmeasured metadata.'))
    print(json.dumps(dict(measured_terminal=pin(target),normalization=pin(audit_path),metadata_seconds=elapsed)),flush=True)


if __name__=='__main__':main()
