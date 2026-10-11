"""Terminal receipt reconciliation only. Never reruns a loader or replay."""
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = ROOT / '.gcts-active/stochastic-replay-memory-v5-20261011'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(65536), b''):
            h.update(part)
    return h.hexdigest()


def need(test, message):
    if not test:
        raise ValueError(message)


def main():
    began = time.perf_counter()
    phase_path = DATA / 'helpers-v5/phase-receipt.json'
    phase = json.loads(phase_path.read_bytes())
    plan_path = DATA / 'helper-plan-v5.json'
    plan = json.loads(plan_path.read_bytes())
    activation_path = ROOT / plan['root_activation_path']
    activation = json.loads(activation_path.read_bytes())
    need(activation['status'] == 'authorized_by_root_after_independent_review', 'exact root helper authorization')
    need(activation['plan_sha256'] == digest(plan_path), 'root helper plan binding')
    for p, h in activation['prerequisite_sha256'].items():
        need(digest(ROOT / p) == h, 'root prerequisite pin')
    need(phase['plan_sha256'] == digest(plan_path), 'phase exact frozen plan')
    need(phase['status'] == 'passed_complete_loading_value_correspondence_helpers', 'whole helper gate passed')
    names = [j['job'] for j in plan['jobs']]
    need(phase['attempted'] == names and not phase['failed'] and not phase['unexecuted'], 'all seven helpers completed')
    need(len(phase['observations']) == 7, 'seven distinct terminal receipts')
    pins, by = {}, {}
    for job, observed in zip(plan['jobs'], phase['observations']):
        output = ROOT / job['output_path']
        lifetime_path = output.parent / (job['job'] + '-lifetime.json')
        receipt = json.loads(output.read_bytes())
        lifetime = json.loads(lifetime_path.read_bytes())
        need(receipt == observed['receipt'] and lifetime == observed['lifetime'], 'phase binds actual per-job bytes')
        need(receipt['job'] == job['job'] and receipt['plan_sha256'] == job['plan_sha256'], 'worker exact job')
        need(receipt['status'] == 'passed_complete_loading_value_helper', 'worker logical gate')
        need(lifetime['status'] == 'passed_owned_loading_worker_lifetime', 'owned resource gate')
        need(lifetime['terminal_and_reaped'] is True and lifetime['exit_code'] == 0 and lifetime['failure'] is None,
             'child exited and was reaped')
        need(lifetime['receipt_sha256'] == digest(output), 'lifetime output SHA')
        need(lifetime['full_worker_seconds'] <= 30 and receipt['seconds_before_receipt_write'] <= 25,
             'owned/internal helper times')
        need(lifetime['conservative_owner_plus_worker_peak_bytes'] <= 536870912,
             'combined helper memory cap')
        need(lifetime['conservative_owner_plus_worker_peak_bytes'] ==
             lifetime['kernel_owner_peak_bytes'] + lifetime['kernel_fresh_worker_peak_bytes'], 'combined peak accounting')
        by[job['job']] = receipt
        for p in (output, lifetime_path):
            pins[str(p.relative_to(ROOT))] = digest(p)
    controls = by['synthetic-controls']['controls']
    need(controls['status'] == 'passed_complete_synthetic_loading_value_controls', 'synthetic positive/negative gate')
    need(len(controls['positive']) == 9 and len(controls['compact_byte_correspondence']) == 9,
         'every nine complete synthetic values and byte gates')
    need(len(controls['rejected']) == 13 and len(controls['lexical_noncompact_rejected']) == 4,
         'all scope/parser and lexical negatives')
    need(controls['byte_gate_mutants_rejected'] == ['changed-assigned-zero'], 'assigned-zero corruption')
    pair_controls = controls['pair_type_controls']
    for name in ('plain_list_preserved', 'tuple_mutant_distinguished',
                 'alias_sensitive_mutating_consumer_distinguished', 'sharing_only_saved_trace'):
        need(pair_controls[name] is True, 'trace-only alias limitation fixture ' + name)
    expected = {
        'effect-pilot-reference': (16922271, '7ca7507338f5ab5db2036556a76a0487305f4ed8dad2b0496bacc93fa6c357e5', 41),
        'train-01-reference': (17013409, 'b9670306501356bb717a20d3e7e375b4accb17b7d30a4e97d22bcabbd84b05f2', 51),
        'train-08-reference': (17286616, 'f5cb7920e4a029b29b5471f618cb237ad4b33e090ed38416e094206d4e9b24ed', 62),
    }
    pairs = []
    for a, b in plan['correspondence_pairs']:
        ref, repaired = by[a], by[b]
        for field in ('canonical', 'observation', 'nodes', 'events', 'weights_sha256'):
            need(ref[field] == repaired[field], 'reference/repaired complete fingerprint and metadata')
        byte_count, h, events = expected[a]
        need(ref['nodes'] == 501 and ref['events'] == events, 'unchanged pilot trace nodes/events')
        for value in (ref, repaired):
            gate = value['complete_original_trace_byte_correspondence']
            need(gate['status'] == 'passed_complete_original_compact_json_byte_correspondence', 'full original-byte gate')
            need(gate['bytes'] == byte_count and gate['original_uncompressed_sha256'] == h
                 and gate['emitted_sha256'] == h, 'every original byte and same decoded value')
        pairs.append({'reference': a, 'repaired': b, 'bytes': byte_count, 'uncompressed_sha256': h,
                      'nodes': 501, 'events': events})
    elapsed = phase['seconds_before_phase_receipt_write']
    need(elapsed <= 180 and phase['conservative_owner_plus_worker_peak_bytes'] <= 536870912, 'whole helper owner cap')
    need(phase['historical_failed_audit_seconds'] == 226.66065275
         and phase['helper_phase_seconds_already_charged'] == 0, 'once-only helper bill')
    need(abs(phase['cumulative_audit_seconds_before_phase_receipt_write'] - (226.66065275 + elapsed)) < 1e-8,
         'all historical and new helper charges')
    remaining = 780 - phase['cumulative_audit_seconds_before_phase_receipt_write']
    receipt = dict(status='passed_independent_v5_terminal_helper_receipt_and_full_byte_pair_review',
        helper_phase_sha256=digest(phase_path), helper_plan_sha256=digest(plan_path),
        root_activation_sha256=digest(activation_path), exact_per_job_receipt_pins=pins,
        complete_pairs=pairs, synthetic_positive_values=9, parser_scope_rejections=13,
        lexical_rejections=4, altered_zero_rejected=True, plain_list_type_retained=True,
        unsupported_alias_mutating_consumer_exposed=True, all_owned_children_terminal_and_reaped=True,
        helper_seconds=elapsed, helper_conservative_peak_bytes=phase['conservative_owner_plus_worker_peak_bytes'],
        cumulative_audit_seconds=phase['cumulative_audit_seconds_before_phase_receipt_write'],
        original_cumulative_remaining_seconds=remaining,
        disposition='Root may independently authorize the separately frozen actual six-replay owner phase. This review grants no dispatch and no actual evaluation acceptance.',
        scope='Terminal artifact reconciliation only. No loaders/helpers/graph replays/training/search/native reruns; producer helper checks are not a full semantic evaluation gate.',
        review_seconds_before_receipt_write=time.perf_counter()-began)
    target = HERE / 'helper-terminal-review-v5.json'
    with target.open('x') as f:
        f.write(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'receipt_sha256': digest(target),
                      'remaining_seconds': remaining}))


if __name__ == '__main__':
    main()
