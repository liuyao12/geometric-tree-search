"""Prospective metadata-only Darwin ledger, never a scientific dispatcher.

ROOT must freeze and review source, platform evidence, topology and activation.
The owner interface can reject partial observations, but cannot qualify a run.
The final gate additionally requires terminal ROOT execution provenance.
"""
import hashlib
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CAP_BYTES = 536870912
POSTLUDE_RESERVE_BYTES = 33554432
PS_RSS_BYTES_PER_UNIT = 1024


def need(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name, positive=False):
    need(type(value) is int and value >= (1 if positive else 0), name)
    return value


def clock(value, name):
    need(type(value) in (int, float) and math.isfinite(value) and value >= 0, name)
    return value


def peak(raw, name):
    need(type(raw) is dict and 'ru_maxrss' in raw, name + ' raw usage')
    return integer(raw['ru_maxrss'], name + ' Darwin byte-valued peak', True)


def exact_pin(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'exact three-field pin')
    path = Path(record['path'])
    if not path.is_absolute():
        path = ROOT / path
    h = hashlib.sha256()
    n = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
            n += len(block)
    need(n == record['bytes'] and h.hexdigest() == record['sha256'], 'unchanged pinned bytes')
    return path


def frame(value, role, pid=None):
    need(type(value) is dict and value['role'] == role and value['exit_code'] == 0,
         'successful exact-role closed SELF frame')
    actual_pid = integer(value['pid'], 'frame PID', True)
    if pid is not None:
        need(actual_pid == pid, 'frame direct owned PID')
    rss = integer(value['SELF_ru_maxrss_raw'], 'frame own peak bytes', True)
    elapsed = clock(value['seconds_after_all_artifact_close_before_fixed_postlude'], 'frame elapsed')
    began = clock(value['entry_monotone_clock'], 'frame entry')
    closed = clock(value['last_closed_monotone_clock'], 'frame closed')
    need(closed >= began and abs((closed - began) - elapsed) <= 0.000001,
         'finite coherent closed frame clocks')
    return actual_pid, rss, elapsed


class AccountingAdapter:
    """One owner, one leaf worker and sequential individually reaped observers.

    No growing sample/PID table is retained. Every observer detail is streamed
    separately by the owner. A descendant-inclusive wait4 maximum is never
    subtracted or counted again as an additional process.
    """
    def __init__(self, source_pin, platform_evidence_pin, owner_pid):
        self.source_pin = source_pin
        self.platform_evidence_pin = platform_evidence_pin
        need(exact_pin(source_pin).resolve() == Path(__file__).resolve(), 'same adapter source')
        exact_pin(platform_evidence_pin)
        self.owner_pid = integer(owner_pid, 'owner PID', True)
        self.observer_count = 0
        self.observer_peak = 0
        self.last_observer_closed = 0
        self.sample_count = 0
        self.sample_maximum = 0
        self.owner_sample_maximum = 0
        self.worker_sample_maximum = 0
        self.sample_worker_pid = None
        self.worker = None
        self.owner_before_receipt = None

    def add_observer(self, receipt):
        need(receipt['observer_id'] == self.observer_count, 'complete sequential observer IDs')
        need(receipt['owner_pid'] == self.owner_pid, 'same observer-owning PID')
        integer(receipt['observer_pid'], 'direct observer PID', True)
        need(receipt['reaped'] is True and receipt['exit_code'] == 0 and receipt['failure'] is None,
             'successful individually terminal-reaped observer')
        began = clock(receipt['clock_before_spawn'], 'observer pre-spawn')
        spawned = clock(receipt['clock_after_spawn'], 'observer registered')
        reaped = clock(receipt['clock_after_stream_close_and_terminal_reap'], 'observer terminal')
        closed = clock(receipt['clock_after_parse_and_stream_hash'], 'observer parsed/hashed')
        need(self.last_observer_closed <= began <= spawned <= reaped <= closed,
             'sequential observer spawn/close/reap/parse clocks')
        need(closed - began <= 1, 'unchanged full observer one-second bound')
        current = peak(receipt['terminal_wait4_raw'], 'verified leaf observer')
        self.observer_peak = max(self.observer_peak, current)
        self.last_observer_closed = closed
        self.observer_count += 1

    def add_sample(self, sample):
        need(sample['observer_id'] == self.observer_count - 1, 'sample uses just-owned observer')
        now = clock(sample['clock'], 'sample clock')
        appended = clock(sample['observer_detail_append_close_clock'], 'closed observer detail')
        need(self.last_observer_closed <= appended <= now, 'sample follows closed observer detail')
        own = sample['owner_SELF_row']
        need(own['pid'] == self.owner_pid and own['pgid'] == self.owner_pid,
             'fresh session/group leader own sample')
        owner_bytes = integer(own['RSS_ps_raw'], 'owner PS units', True) * PS_RSS_BYTES_PER_UNIT
        worker_pid = integer(sample['direct_worker_PID'], 'direct worker PID', True)
        need(worker_pid != self.owner_pid, 'distinct owner and worker')
        if self.sample_worker_pid is not None:
            need(worker_pid == self.sample_worker_pid, 'one direct worker lifetime')
        self.sample_worker_pid = worker_pid
        rows = sample['worker_rows']
        need(type(rows) is list and len(rows) <= 1, 'one leaf worker, no observed descendants')
        worker_bytes = 0
        for row in rows:
            need(row['pid'] == worker_pid and row['ppid'] == self.owner_pid
                 and row['pgid'] == self.owner_pid, 'worker inherits exact owned group')
            worker_bytes = integer(row['RSS_ps_raw'], 'worker PS units', True) * PS_RSS_BYTES_PER_UNIT
        self.owner_sample_maximum = max(self.owner_sample_maximum, owner_bytes)
        self.worker_sample_maximum = max(self.worker_sample_maximum, worker_bytes)
        self.sample_maximum = max(self.sample_maximum, owner_bytes + worker_bytes)
        self.sample_count += 1

    def add_leaf_worker(self, raw, closed_SELF, seconds):
        need(self.worker is None, 'one direct terminal worker, no replacement or retry')
        pid, own_peak, elapsed = frame(closed_SELF, 1, self.sample_worker_pid)
        terminal_peak = peak(raw, 'verified leaf worker terminal wait4')
        seconds = clock(seconds, 'worker creation-through-terminal-reap seconds')
        need(elapsed <= seconds + 0.000001 and seconds <= 170,
             'unchanged full worker 170-second bound includes closed bytes')
        need(max(own_peak, self.worker_sample_maximum) <= terminal_peak,
             'leaf terminal bound covers saved SELF and samples')
        self.worker = dict(pid=pid, terminal_peak_bytes=terminal_peak,
                           closed_SELF_peak_bytes=own_peak, full_seconds=seconds)

    def add_SELF_before_receipt(self, raw):
        need(self.owner_before_receipt is None, 'one pre-receipt own observation')
        self.owner_before_receipt = peak(raw, 'owner SELF before receipt')
        need(self.owner_sample_maximum <= self.owner_before_receipt,
             'own peak covers earlier own samples')

    def rejects_current_caps(self):
        # Partial samples can reject. Absence of rejection is never acceptance:
        # ROOT and the owner's final receipt/postlude are still missing here.
        known = self.sample_maximum + self.observer_peak + POSTLUDE_RESERVE_BYTES
        if self.worker is not None and self.owner_before_receipt is not None:
            known = max(known, self.worker['terminal_peak_bytes']
                        + self.owner_before_receipt + self.observer_peak + POSTLUDE_RESERVE_BYTES)
        return known > CAP_BYTES

    def finish_provisional(self):
        need(self.worker is not None and self.owner_before_receipt is not None,
             'complete leaf and pre-receipt own observations')
        subtotal = (self.worker['terminal_peak_bytes'] + self.owner_before_receipt
                    + self.observer_peak + POSTLUDE_RESERVE_BYTES)
        return dict(schema='prospective-distinct-owned-Darwin-provisional-ledger-v1',
                    owner_pid=self.owner_pid, owner_SELF_before_receipt_bytes=self.owner_before_receipt,
                    leaf_worker=self.worker, sequential_observer_count=self.observer_count,
                    sequential_observer_peak_bytes=self.observer_peak,
                    sample_count=self.sample_count, saved_simultaneous_owner_worker_max_bytes=self.sample_maximum,
                    owner_sample_maximum_bytes=self.owner_sample_maximum,
                    worker_sample_maximum_bytes=self.worker_sample_maximum,
                    postlude_reserve_bytes=POSTLUDE_RESERVE_BYTES,
                    partial_distinct_role_envelope_bytes=subtotal,
                    missing=['owner_SELF_after_receipt_close', 'ROOT_SELF_after_all_metadata',
                             'ROOT_terminal_execution_and_full_clock'],
                    resource_accepted=False, all_five_qualification=False,
                    scope='Known pinned one-leaf worker and sequential observers only; retrospective envelope, no hard OS cap.')


def finish_root_ledger(provisional, owner_frame, owner_terminal_raw, ROOT_SELF_raw,
                       full_owner_seconds, ROOT_entry_seconds, execution_provenance):
    """Candidate is finalized only after a trusted terminal ROOT tool receipt.

    Parent wait4 roll-up is retained as corroboration, never an extra summand.
    Source review must separately bind all frames/pins, platform evidence and
    complete topology. The fixed reserve covers reviewed bounded postludes;
    this is neither whole-host memory nor an OS-enforced cap.
    """
    need(provisional['schema'] == 'prospective-distinct-owned-Darwin-provisional-ledger-v1'
         and provisional['resource_accepted'] is False, 'same pending owner ledger')
    pid, owner_peak, elapsed = frame(owner_frame, 2, provisional['owner_pid'])
    full_owner_seconds = clock(full_owner_seconds, 'owner complete creation/reap clock')
    ROOT_entry_seconds = clock(ROOT_entry_seconds, 'ROOT through closed metadata clock')
    need(elapsed <= full_owner_seconds + 0.000001 and full_owner_seconds <= 175,
         'unchanged full owner 175-second bound')
    need(full_owner_seconds <= ROOT_entry_seconds + 0.000001 and ROOT_entry_seconds <= 180,
         'unchanged ROOT 180-second bound before terminal confirmation')
    worker_peak = integer(provisional['leaf_worker']['terminal_peak_bytes'], 'leaf terminal peak', True)
    observer_peak = integer(provisional['sequential_observer_peak_bytes'], 'sequential observer maximum')
    owner_before = integer(provisional['owner_SELF_before_receipt_bytes'], 'owner pre-close peak', True)
    need(owner_before <= owner_peak, 'closed owner SELF covers its earlier snapshot')
    rolled = peak(owner_terminal_raw, 'owner descendant-inclusive terminal wait4')
    need(max(owner_peak, worker_peak, observer_peak) <= rolled,
         'raw owner terminal maximum covers each individually measured child scope')
    root_peak = peak(ROOT_SELF_raw, 'saved raw ROOT SELF after metadata')
    need(provisional['postlude_reserve_bytes'] == POSTLUDE_RESERVE_BYTES, 'unchanged fixed reserve')
    envelope = root_peak + owner_peak + worker_peak + observer_peak + POSTLUDE_RESERVE_BYTES
    need(type(execution_provenance) is dict, 'explicit external terminal provenance')
    required = ('terminal', 'exit_code', 'cancelled', 'emergency_group_kill',
                'containment_latched', 'complete_known_topology', 'full_tool_boundary_seconds')
    need(all(key in execution_provenance for key in required), 'complete external terminal fields')
    for key in ('terminal', 'cancelled', 'emergency_group_kill', 'containment_latched', 'complete_known_topology'):
        need(type(execution_provenance[key]) is bool, 'strict boolean execution field')
    need(type(execution_provenance['exit_code']) is int, 'integer ROOT exit code')
    tool_seconds = clock(execution_provenance['full_tool_boundary_seconds'], 'complete external tool boundary')
    need(ROOT_entry_seconds <= tool_seconds + 0.001, 'external terminal boundary covers ROOT closed clock')
    accepted = (execution_provenance['terminal'] and execution_provenance['exit_code'] == 0
                and not execution_provenance['cancelled'] and not execution_provenance['emergency_group_kill']
                and not execution_provenance['containment_latched'] and execution_provenance['complete_known_topology']
                and tool_seconds <= 180 and envelope <= CAP_BYTES)
    return dict(schema='prospective-distinct-owned-Darwin-ROOT-ledger-v1',
                terms_bytes=dict(ROOT_SELF_after_metadata=root_peak,
                                 owner_SELF_after_receipt_close=owner_peak,
                                 leaf_worker_terminal_wait4=worker_peak,
                                 sequential_leaf_observer_terminal_max=observer_peak,
                                 reviewed_fixed_postlude_reserve=POSTLUDE_RESERVE_BYTES),
                complete_distinct_role_envelope_bytes=envelope, maximum_peak_bytes=CAP_BYTES,
                owner_terminal_descendant_inclusive_peak_bytes=rolled,
                owner_terminal_peak_is_not_an_additional_summand=True,
                full_owner_seconds=full_owner_seconds, ROOT_closed_metadata_seconds=ROOT_entry_seconds,
                full_tool_boundary_seconds=tool_seconds, maximum_whole_seconds=180,
                resource_accepted=accepted, disposition='accepted_known_topology_envelope' if accepted else 'UNKNOWN',
                execution_provenance=execution_provenance, all_five_qualification=False,
                OS_hard_cap_claim=False, whole_host_cap_claim=False,
                historical_donor_two_guards_UNKNOWN_preserved=True,
                scope='Prospective known pinned topology and individually saved scopes only; no mathematical/search/RL acceptance.')
