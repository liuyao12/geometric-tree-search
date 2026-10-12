"""Prospective metadata-only Darwin ledger, never a scientific dispatcher.

ROOT must freeze and review source, platform evidence, topology and activation.
The owner interface can reject partial observations, but cannot qualify a run.
The final gate additionally requires terminal ROOT execution provenance.
"""
import hashlib
import math
import struct
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
    need(type(record['path']) is str and bool(record['path']), 'nonempty declared pin path')
    need(type(record['sha256']) is str and len(record['sha256']) == 64
         and all(char in '0123456789abcdef' for char in record['sha256']), 'exact lowercase SHA256 pin')
    integer(record['bytes'], 'exact pin byte count')
    path = Path(record['path'])
    if not path.is_absolute():
        path = ROOT / path
    h = hashlib.sha256()
    n = 0
    with path.open('rb') as stream:
        import os
        before = os.fstat(stream.fileno())
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
            n += len(block)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    need(identity(before) == identity(after) == identity(path.stat())
         and n == record['bytes'] and h.hexdigest() == record['sha256'], 'unchanged pinned stream identity/bytes')
    return path


def frame(value, role, pid=None):
    expected = {'role', 'pid', 'exit_code', 'SELF_ru_maxrss_raw',
                'seconds_after_all_artifact_close_before_fixed_postlude',
                'entry_monotone_clock', 'last_closed_monotone_clock'}
    transport_fields = {'remaining_postlude', 'terminal_frame'}
    need(type(value) is dict and set(value) in (expected, expected | transport_fields)
         and type(role) is int and type(value['role']) is int and value['role'] == role
         and type(value['exit_code']) is int and value['exit_code'] == 0,
         'successful exact-role closed SELF frame')
    actual_pid = integer(value['pid'], 'frame PID', True)
    if pid is not None:
        need(actual_pid == integer(pid, 'registered frame PID', True), 'frame direct owned PID')
    rss = integer(value['SELF_ru_maxrss_raw'], 'frame own peak bytes', True)
    elapsed = clock(value['seconds_after_all_artifact_close_before_fixed_postlude'], 'frame elapsed')
    began = clock(value['entry_monotone_clock'], 'frame entry')
    closed = clock(value['last_closed_monotone_clock'], 'frame closed')
    need(closed >= began and abs((closed - began) - elapsed) <= 0.000001,
         'finite coherent closed frame clocks')
    if set(value) == expected | transport_fields:
        need(value['remaining_postlude'] == 'Fixed52-byte pack/write then os._exit; separately ROOT-reviewed reserve required',
             'exact original bounded postlude scope')
        path = exact_pin(value['terminal_frame'])
        need(value['terminal_frame']['bytes'] == 52, 'fixed raw frame length')
        with path.open('rb') as stream:
            raw = stream.read(53)
        need(len(raw) == 52 and hashlib.sha256(raw).hexdigest() == value['terminal_frame']['sha256'],
             'decoded buffer equals exact pinned terminal bytes')
        magic, tag, code, reserved, raw_pid, raw_rss, raw_elapsed, raw_start, raw_close = struct.unpack('!8sBBHQQddd', raw)
        need(magic == b'GCTSCMP1' and reserved == 0
             and (tag, code, raw_pid, raw_rss, raw_elapsed, raw_start, raw_close)
             == (value['role'], value['exit_code'], actual_pid, rss, elapsed, began, closed),
             'decoded values equal the independently pinned terminal binary')
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
        self.last_sample_clock = 0
        self.worker = None
        self.owner_before_receipt = None

    def add_observer(self, receipt):
        need(integer(receipt['observer_id'], 'observer ID') == self.observer_count, 'complete sequential observer IDs')
        need(integer(receipt['owner_pid'], 'observer owner PID', True) == self.owner_pid, 'same observer-owning PID')
        integer(receipt['observer_pid'], 'direct observer PID', True)
        need(receipt['observer_pid'] != self.owner_pid, 'observer is a distinct direct child')
        need(receipt['reaped'] is True and type(receipt['exit_code']) is int
             and receipt['exit_code'] == 0 and receipt['failure'] is None,
             'successful individually terminal-reaped observer')
        began = clock(receipt['clock_before_spawn'], 'observer pre-spawn')
        spawned = clock(receipt['clock_after_spawn'], 'observer registered')
        reaped = clock(receipt['clock_after_stream_close_and_terminal_reap'], 'observer terminal')
        closed = clock(receipt['clock_after_parse_and_stream_hash'], 'observer parsed/hashed')
        need(max(self.last_observer_closed, self.last_sample_clock) <= began <= spawned <= reaped <= closed,
             'sequential observer spawn/close/reap/parse clocks')
        need(closed - began <= 1, 'unchanged full observer one-second bound')
        current = peak(receipt['terminal_wait4_raw'], 'verified leaf observer')
        self.observer_peak = max(self.observer_peak, current)
        self.last_observer_closed = closed
        self.observer_count += 1

    def add_sample(self, sample):
        need(integer(sample['observer_id'], 'sample observer ID') == self.sample_count
             and self.sample_count == self.observer_count - 1, 'one sample per just-owned observer')
        now = clock(sample['clock'], 'sample clock')
        appended = clock(sample['observer_detail_append_close_clock'], 'closed observer detail')
        need(max(self.last_observer_closed, self.last_sample_clock) <= appended <= now,
             'monotone sample follows closed observer detail')
        own = sample['owner_SELF_row']
        need(integer(own['pid'], 'sample owner PID', True) == self.owner_pid
             and integer(own['pgid'], 'sample owner group', True) == self.owner_pid,
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
            need(integer(row['pid'], 'sample worker PID', True) == worker_pid
                 and integer(row['ppid'], 'sample worker parent', True) == self.owner_pid
                 and integer(row['pgid'], 'sample worker group', True) == self.owner_pid,
                 'worker inherits exact owned group')
            worker_bytes = integer(row['RSS_ps_raw'], 'worker PS units', True) * PS_RSS_BYTES_PER_UNIT
        self.owner_sample_maximum = max(self.owner_sample_maximum, owner_bytes)
        self.worker_sample_maximum = max(self.worker_sample_maximum, worker_bytes)
        self.sample_maximum = max(self.sample_maximum, owner_bytes + worker_bytes)
        self.sample_count += 1
        self.last_sample_clock = now

    def add_leaf_worker(self, raw, closed_SELF, seconds, expected_pid=None):
        need(self.worker is None, 'one direct terminal worker, no replacement or retry')
        pid, own_peak, elapsed = frame(closed_SELF, 1, self.sample_worker_pid)
        need(pid != self.owner_pid, 'distinct direct leaf even without samples')
        if expected_pid is not None:
            need(pid == integer(expected_pid, 'registered direct leaf PID', True), 'frame matches registered direct leaf')
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
        need(self.observer_count == self.sample_count, 'complete one-to-one observer/sample census')
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


def validate_provisional(value):
    expected = {'schema', 'owner_pid', 'owner_SELF_before_receipt_bytes', 'leaf_worker',
                'sequential_observer_count', 'sequential_observer_peak_bytes', 'sample_count',
                'saved_simultaneous_owner_worker_max_bytes', 'owner_sample_maximum_bytes',
                'worker_sample_maximum_bytes', 'postlude_reserve_bytes',
                'partial_distinct_role_envelope_bytes', 'missing', 'resource_accepted',
                'all_five_qualification', 'scope'}
    need(type(value) is dict and set(value) == expected, 'exact complete provisional projection')
    need(value['schema'] == 'prospective-distinct-owned-Darwin-provisional-ledger-v1'
         and value['resource_accepted'] is False and value['all_five_qualification'] is False,
         'strict pending provisional scope')
    owner = integer(value['owner_pid'], 'provisional owner PID', True)
    own = integer(value['owner_SELF_before_receipt_bytes'], 'provisional owner SELF', True)
    worker = value['leaf_worker']
    need(type(worker) is dict and set(worker) == {'pid', 'terminal_peak_bytes',
         'closed_SELF_peak_bytes', 'full_seconds'}, 'exact direct-leaf projection')
    need(integer(worker['pid'], 'provisional worker PID', True) != owner, 'distinct transported leaf PID')
    terminal = integer(worker['terminal_peak_bytes'], 'provisional leaf terminal peak', True)
    closed = integer(worker['closed_SELF_peak_bytes'], 'provisional leaf closed SELF', True)
    need(closed <= terminal and clock(worker['full_seconds'], 'provisional full leaf clock') <= 170,
         'transported leaf own/terminal/full-clock relation')
    observers = integer(value['sequential_observer_count'], 'provisional observer census')
    samples = integer(value['sample_count'], 'provisional sample census')
    observer = integer(value['sequential_observer_peak_bytes'], 'provisional observer peak')
    need(samples == observers and ((observers == 0 and observer == 0) or (observers > 0 and observer > 0)),
         'transported paired observer census/maximum')
    owner_sample = integer(value['owner_sample_maximum_bytes'], 'provisional owner sampled maximum')
    worker_sample = integer(value['worker_sample_maximum_bytes'], 'provisional worker sampled maximum')
    combined = integer(value['saved_simultaneous_owner_worker_max_bytes'], 'provisional simultaneous sample maximum')
    need(owner_sample <= own and worker_sample <= terminal
         and max(owner_sample, worker_sample) <= combined <= owner_sample + worker_sample,
         'transported samples are consistent with individually observed peaks')
    need((samples == 0 and combined == owner_sample == worker_sample == 0)
         or (samples > 0 and combined > 0 and owner_sample > 0), 'sample census matches saved observations')
    need(value['postlude_reserve_bytes'] == POSTLUDE_RESERVE_BYTES
         and type(value['postlude_reserve_bytes']) is int, 'exact prospective fixed reserve')
    need(integer(value['partial_distinct_role_envelope_bytes'], 'provisional subtotal')
         == own + terminal + observer + POSTLUDE_RESERVE_BYTES, 'reconstructed provisional subtotal')
    need(value['missing'] == ['owner_SELF_after_receipt_close', 'ROOT_SELF_after_all_metadata',
                             'ROOT_terminal_execution_and_full_clock'], 'complete pending missing-scope declaration')
    need(value['scope'] == 'Known pinned one-leaf worker and sequential observers only; retrospective envelope, no hard OS cap.',
         'unchanged known-topology scope')
    return value


def finish_root_ledger(provisional, owner_frame, owner_terminal_raw, ROOT_SELF_raw,
                       full_owner_seconds, ROOT_entry_seconds, execution_provenance):
    """Candidate is finalized only after a trusted terminal ROOT tool receipt.

    Parent wait4 roll-up is retained as corroboration, never an extra summand.
    Source review must separately bind all frames/pins, platform evidence and
    complete topology. The fixed reserve covers reviewed bounded postludes;
    this is neither whole-host memory nor an OS-enforced cap.
    """
    validate_provisional(provisional)
    pid, owner_peak, elapsed = frame(owner_frame, 2, provisional['owner_pid'])
    full_owner_seconds = clock(full_owner_seconds, 'owner complete creation/reap clock')
    ROOT_entry_seconds = clock(ROOT_entry_seconds, 'ROOT through closed metadata clock')
    need(elapsed <= full_owner_seconds + 0.000001 and full_owner_seconds <= 175,
         'unchanged full owner 175-second bound')
    need(provisional['leaf_worker']['full_seconds'] <= full_owner_seconds + 0.000001,
         'direct leaf creation/reap lifetime lies inside owned owner lifetime')
    need(full_owner_seconds <= ROOT_entry_seconds + 0.000001 and ROOT_entry_seconds <= 180,
         'unchanged ROOT 180-second bound before terminal confirmation')
    worker_peak = integer(provisional['leaf_worker']['terminal_peak_bytes'], 'leaf terminal peak', True)
    observer_peak = integer(provisional['sequential_observer_peak_bytes'], 'sequential observer maximum')
    owner_before = integer(provisional['owner_SELF_before_receipt_bytes'], 'owner pre-close peak', True)
    need(owner_before <= owner_peak, 'closed owner SELF covers its earlier snapshot')
    rolled = peak(owner_terminal_raw, 'owner descendant-inclusive terminal wait4')
    need(max(owner_peak, worker_peak, observer_peak) <= rolled,
         'raw owner terminal maximum covers each individually measured child scope')
    need(rolled <= max(owner_peak, worker_peak, observer_peak) + POSTLUDE_RESERVE_BYTES,
         'unexplained terminal roll-up exceeds reviewed residual reserve')
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
