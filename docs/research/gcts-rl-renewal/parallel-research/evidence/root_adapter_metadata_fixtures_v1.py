"""ROOT-only synthetic record checks. This is not a resource experiment.

No scientific module, ps, subprocess, random stream, or owner is invoked.
All process identifiers, clocks and peaks in fixtures are invented values.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import struct
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ADAPTER = dict(path=str(HERE / 'root_accounting_adapter_v3.py'),
               sha256='821397eeb6e8efde19380024f2edd2181d9c12e21ee007aa1f2e327d01754f53', bytes=21094)


def exact_pin(path):
    data = Path(path).read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def main():
    started = time.perf_counter()
    assert exact_pin(ADAPTER['path']) == ADAPTER
    outdir = HERE / 'metadata-fixtures-v1'
    outdir.mkdir(exist_ok=False)
    evidence_path = outdir / 'synthetic-evidence.json'
    with evidence_path.open('xb') as stream:
        stream.write(b'{"scope":"invented fixture evidence; never platform qualification"}\n')
    evidence = exact_pin(evidence_path)
    spec = importlib.util.spec_from_file_location('synthetic_record_adapter_v3', ADAPTER['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = []

    def check(label, expected_rejection, action):
        try:
            action()
        except (ValueError, KeyError, TypeError, OverflowError, struct.error) as error:
            rejected = True
            error_record = dict(type=type(error).__name__, message=str(error))
        else:
            rejected = False
            error_record = None
        results.append(dict(name=label, expected_rejection=expected_rejection,
                            rejected=rejected, passed=rejected == expected_rejection,
                            error=error_record))

    def frame(role, pid, rss, elapsed):
        return dict(role=role, pid=pid, exit_code=0, SELF_ru_maxrss_raw=rss,
                    seconds_after_all_artifact_close_before_fixed_postlude=elapsed,
                    entry_monotone_clock=0.0, last_closed_monotone_clock=elapsed)

    worker = frame(1, 102, 50000, 8.0)
    owner = frame(2, 101, 35000, 20.0)
    observer = dict(observer_id=0, owner_pid=101, observer_pid=103, reaped=True,
                    exit_code=0, failure=None, clock_before_spawn=1.0, clock_after_spawn=1.01,
                    clock_after_stream_close_and_terminal_reap=1.05,
                    clock_after_parse_and_stream_hash=1.10, terminal_wait4_raw=dict(ru_maxrss=5000))
    sample = dict(observer_id=0, clock=1.12, observer_detail_append_close_clock=1.11,
                  owner_SELF_row=dict(pid=101, pgid=101, RSS_ps_raw=20), direct_worker_PID=102,
                  worker_rows=[dict(pid=102, ppid=101, pgid=101, RSS_ps_raw=30)])

    def new():
        return module.AccountingAdapter(ADAPTER, evidence, 101)

    def coherent(sampled=True):
        accounting = new()
        if sampled:
            accounting.add_observer(copy.deepcopy(observer))
            accounting.add_sample(copy.deepcopy(sample))
        accounting.add_leaf_worker(dict(ru_maxrss=60000), worker, 10.0, expected_pid=102)
        accounting.add_SELF_before_receipt(dict(ru_maxrss=30000))
        return accounting.finish_provisional()

    execution = dict(terminal=True, exit_code=0, cancelled=False, emergency_group_kill=False,
                     containment_latched=False, complete_known_topology=True,
                     full_tool_boundary_seconds=31.0)

    def final(provisional=None, owner_value=None, provenance=None, ROOT_usage=None, rolled=None, owner_seconds=20.0):
        return module.finish_root_ledger(coherent() if provisional is None else provisional,
            owner if owner_value is None else owner_value,
            dict(ru_maxrss=60000) if rolled is None else rolled,
            dict(ru_maxrss=40000) if ROOT_usage is None else ROOT_usage,
            owner_seconds, 30.0, execution if provenance is None else provenance)

    def positive():
        candidate = final()
        assert candidate['complete_distinct_role_envelope_bytes'] == 33694432
        assert candidate['resource_accepted'] is True
        assert candidate['all_five_qualification'] is False
        assert candidate['owner_terminal_peak_is_not_an_additional_summand'] is True

    check('coherent invented scopes give expected conditional arithmetic', False, positive)
    check('fast leaf without samples remains representable', False, lambda: module.validate_provisional(coherent(False)))
    raw_path = outdir / 'synthetic-worker-frame.bin'
    with raw_path.open('xb') as stream:
        stream.write(struct.pack('!8sBBHQQddd', b'GCTSCMP1', 1, 0, 0, 102, 50000, 8.0, 0.0, 8.0))
    full_frame = dict(worker, remaining_postlude='Fixed52-byte pack/write then os._exit; separately ROOT-reviewed reserve required',
                      terminal_frame=exact_pin(raw_path))
    check('original nine-field authenticated wire format accepted', False, lambda: module.frame(full_frame, 1, 102))
    wrong_wire = dict(full_frame, SELF_ru_maxrss_raw=49999)
    check('decoded value differing from pinned binary rejected', True, lambda: module.frame(wrong_wire, 1, 102))
    check('unknown frame field rejected', True, lambda: module.frame(dict(worker, extra=True), 1, 102))
    check('boolean role rejected', True, lambda: module.frame(dict(worker, role=True), 1, 102))
    check('floating exit tag rejected', True, lambda: module.frame(dict(worker, exit_code=0.0), 1, 102))
    check('nonfinite clock rejected', True, lambda: module.frame(dict(worker, entry_monotone_clock=float('nan')), 1, 102))
    check('missing frame field rejected', True, lambda: module.frame({'role':1}, 1, 102))
    check('same owner and leaf PID without samples rejected', True,
          lambda: new().add_leaf_worker(dict(ru_maxrss=60000), dict(worker, pid=101), 10.0))
    check('leaf frame differing from registered direct PID rejected', True,
          lambda: new().add_leaf_worker(dict(ru_maxrss=60000), worker, 10.0, expected_pid=104))
    check('boolean pin byte count rejected', True, lambda: module.exact_pin(dict(evidence, bytes=True)))
    check('malformed hash rejected', True, lambda: module.exact_pin(dict(evidence, sha256='x'*64)))
    check('empty pin path rejected', True, lambda: module.exact_pin(dict(evidence, path='')))

    def duplicate_sample():
        accounting = new(); accounting.add_observer(observer)
        accounting.add_sample(sample); accounting.add_sample(sample)
    check('duplicate sample for one observer rejected', True, duplicate_sample)
    check('sample before observer rejected', True, lambda: new().add_sample(sample))
    check('boolean observer ID rejected', True, lambda: new().add_observer(dict(observer, observer_id=False)))
    check('observer over complete one-second bound rejected', True,
          lambda: new().add_observer(dict(observer, clock_after_parse_and_stream_hash=2.01)))

    def missing_sample():
        accounting = new(); accounting.add_observer(observer)
        accounting.add_leaf_worker(dict(ru_maxrss=60000), worker, 10.0, expected_pid=102)
        accounting.add_SELF_before_receipt(dict(ru_maxrss=30000)); accounting.finish_provisional()
    check('missing sample in observer census rejected', True, missing_sample)

    def backward_sample():
        accounting = new(); accounting.add_observer(observer)
        accounting.add_sample(dict(sample, clock=1.09))
    check('sample clock preceding closed detail rejected', True, backward_sample)

    for label, update in [
            ('false transported subtotal', dict(partial_distinct_role_envelope_bytes=1)),
            ('false transported sample census', dict(sample_count=2)),
            ('false missing-scope declaration', dict(missing=[])),
            ('transport grants itself acceptance', dict(resource_accepted=True)),
            ('transport claims all-five acceptance', dict(all_five_qualification=True)),
            ('unknown transported ledger field', dict(extra=True))]:
        check(label + ' rejected', True, lambda update=update: final(dict(coherent(), **update)))
    check('missing raw ROOT SELF rejected', True, lambda: final(ROOT_usage={}))
    check('owner roll-up below known leaf scope rejected', True, lambda: final(rolled=dict(ru_maxrss=50000)))
    check('unexplained owner roll-up over residual reserve rejected', True,
          lambda: final(rolled=dict(ru_maxrss=60000+33554432+1)))
    check('leaf full lifetime outside owner lifetime rejected', True, lambda: final(owner_value=frame(2,101,35000,9.0), owner_seconds=9.0))
    check('boolean external terminal code rejected', True, lambda: final(provenance=dict(execution, exit_code=False)))

    def unknown(update):
        candidate = final(provenance=dict(execution, **update))
        assert candidate['resource_accepted'] is False and candidate['disposition'] == 'UNKNOWN'
    for label, update in [
            ('cancelled terminal remains UNKNOWN', dict(cancelled=True)),
            ('emergency kill remains UNKNOWN', dict(emergency_group_kill=True)),
            ('containment latch remains UNKNOWN', dict(containment_latched=True)),
            ('missing terminal remains UNKNOWN', dict(terminal=False)),
            ('unknown topology remains UNKNOWN', dict(complete_known_topology=False)),
            ('whole boundary over 180 seconds remains UNKNOWN', dict(full_tool_boundary_seconds=180.01))]:
        check(label, False, lambda update=update: unknown(update))

    def over_cap():
        candidate = final(ROOT_usage=dict(ru_maxrss=536870912))
        assert candidate['resource_accepted'] is False and candidate['disposition'] == 'UNKNOWN'
    check('over-cap distinct envelope remains UNKNOWN', False, over_cap)
    result = dict(schema='ROOT-synthetic-accounting-record-fixtures-v1',
        status='PASS_SYNTHETIC_METADATA_ONLY' if all(row['passed'] for row in results) else 'FAIL_SYNTHETIC_METADATA_ONLY',
        adapter=ADAPTER, fixture_source=exact_pin(Path(__file__)),
        synthetic_evidence=evidence, synthetic_frame=exact_pin(raw_path),
        cases=len(results), passed=sum(row['passed'] for row in results), results=results,
        fixture_seconds=time.perf_counter()-started,
        scope='Invented IDs/clocks/peaks and two local synthetic files; actual wrapper/PS/science not invoked. Positive conditional arithmetic is not actual resource acceptance.',
        scientific_calls=0, owner_or_process_PS_calls=0, RNG_draws=0,
        actual_platform_or_curriculum_qualification=False, all_five_qualification=False,
        historical_first_resource_UNKNOWN_preserved=True)
    with (outdir/'result-v1.json').open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:result[key] for key in ('status','cases','passed','fixture_seconds','actual_platform_or_curriculum_qualification')}))
    if result['passed'] != result['cases']:
        raise RuntimeError('metadata fixture failure preserved; do not rerun')


if __name__ == '__main__':
    main()
