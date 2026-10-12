"""ROOT one-shot dispatcher; standard-library ownership and metadata only.

No search/compiler/oracle imports. Exact frozen plans own all scientific calls.
The normalized receipt uses a prospective 1-second complete-launcher/final-write reserve;
the complete serialized bytes remain provisional until post-write time and
peak checks pass. Only then are identical bytes hard-linked to the normalized
terminal path; successful post-write observation is also required before use. No OS hard memory limit is claimed.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PRODUCER = ROOT / '.gcts-active/family-curriculum-context-source-v3-20261012'
INDEPENDENT = ROOT / '.gcts-active/family-curriculum-independent-source-v3-20261012'
SELECTORS = ('donor-two-guards', 'donor-two-equalities', 'donor-repeated-guard',
             'donor-repeated-equality', 'heldout-mixed-guard-equality')
CEILING_BYTES = 536870912
WRITE_RESERVE = 1.0
WRITE_MEMORY_RESERVE = 32 * 1024 * 1024


def require(test, text):
    if not test:
        raise ValueError(text)


def read(path):
    return json.loads(Path(path).read_text())


def pin(path, declared=None):
    path = Path(path)
    h = hashlib.sha256(); count = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            h.update(chunk); count += len(chunk)
    name = declared if declared is not None else str(path.resolve().relative_to(ROOT))
    return dict(path=name, sha256=h.hexdigest(), bytes=count)


def verify(record):
    path = Path(record['path'])
    if not path.is_absolute():
        path = ROOT / path
    require(pin(path, record['path']) == {k:record[k] for k in ('path','sha256','bytes')},
            'frozen byte identity: ' + record['path'])


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def peak(usage):
    return usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)


def process_table():
    # PID/PPID/PGID/RSS only: no command lines or unrelated private data.
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,rss='],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1, check=True)
    rows = {}
    for line in result.stdout.splitlines():
        values = line.split()
        if len(values) == 4:
            pid, ppid, pgid, rss = map(int, values)
            require(rss >= 0, 'nonnegative process metadata')
            rows[pid] = (ppid, pgid, rss * 1024)
    return rows


def descendants(table, leader, retained):
    active = {leader} | {pid for pid in retained if pid in table}
    while True:
        nxt = active | {pid for pid, row in table.items() if row[0] in active}
        if nxt == active:
            return {pid for pid in active if pid in table}
        active = nxt


def stop_owned(child, owned):
    # Supervisor/independent owner receive TERM and reap their worker first.
    for pid in sorted(owned - {child.pid}):
        try: os.kill(pid, signal.SIGTERM)
        except ProcessLookupError: pass
    try: os.kill(child.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    end = time.perf_counter() + 2
    while time.perf_counter() < end:
        pid, status, usage = os.wait4(child.pid, os.WNOHANG)
        if pid:
            child.returncode = os.waitstatus_to_exitcode(status)
            return usage
        time.sleep(.02)
    for pid in sorted(owned | {child.pid}):
        try: os.kill(pid, signal.SIGKILL)
        except ProcessLookupError: pass
    _, status, usage = os.wait4(child.pid, 0)
    child.returncode = os.waitstatus_to_exitcode(status)
    return usage


def main():
    started = time.perf_counter()
    require(len(sys.argv) == 3 and sys.argv[1] in ('preparation','static')
            and sys.argv[2] in SELECTORS, 'exact frozen phase and selector')
    phase, selector = sys.argv[1:]
    maximum = 60 if phase == 'preparation' else 180
    review_path = HERE / 'ROOT-source-review-v1.json'
    review = read(review_path)
    require(review['full_sources_reviewed'] is True and review['source_review_passed'] is True
            and review['scientific_calls'] == 0, 'full ROOT source review required')
    verify(review['curriculum_source_plan']); verify(review['independent_source_plan'])
    for item in review['source_records']:
        verify(item)
    base = PRODUCER if phase == 'preparation' else INDEPENDENT
    basename = ('preparation-' if phase == 'preparation' else 'actual-static-') + selector + '-plan-v1.json'
    plan_path = base / basename; plan = read(plan_path)
    require(plan['selector'] == selector, 'literal selected context')
    frozen_independent_source = read(INDEPENDENT/'source-plan-v1.json')
    if phase == 'preparation':
        require(plan['schema'] == 'frozen-curriculum-family-preparation-plan-v1', 'exact V3 preparation schema')
        expected = next(r for r in frozen_independent_source['inputs'] if r['role'] == 'preparation_plan_'+selector)
        require(pin(plan_path, expected['path']) == {k:expected[k] for k in ('path','sha256','bytes')},
                'exact reviewed V3 preparation plan')
    else:
        require(plan['schema'] == 'frozen-curriculum-independent-actual-static-plan-v1'
            and plan['stage'] == 'static' and plan['status'] == 'frozen_actual_inputs_pending_ROOT_activation'
            and plan['actual_execution_authorized'] is False and plan['ROOT_sole_actual_owner'] is True,
            'exact frozen actual independent static plan')
        require(plan['sources'] == frozen_independent_source['sources']
            and plan['libraries'] == frozen_independent_source['libraries'], 'exact independently reviewed sources')
    closure = {}
    for group in ('sources','libraries','inputs','preserved','preserved_files'):
        for item in plan.get(group,[]):
            if item['path'] not in closure:
                verify(item); closure[item['path']] = item
            else:
                require(all(closure[item['path']][k] == item[k] for k in ('path','sha256','bytes')),
                        'consistent closure pin')
    runtime = plan['runtime']
    verify(runtime['binary'])
    verify(runtime['process_metadata'] if phase == 'preparation' else runtime['observer'])
    require(runtime['executable'] == sys.executable and runtime['platform'] == sys.platform,
            'frozen runtime alias and platform')
    require(str(Path(sys.executable).resolve()) == runtime['binary']['path'], 'runtime resolved binary')
    stem = phase + '-' + selector
    terminal_path = HERE / (stem + '-ROOT-terminal-v1.json')
    provisional_path = HERE / (stem + '-provisional-ROOT-terminal-v1.json')
    observation_path = HERE / (stem + '-post-write-observation-v1.json')
    launch_path = HERE / (stem + '-ROOT-launch-v1.json')
    outpath = HERE / (stem + '-ROOT-stdout-v1.txt')
    errpath = HERE / (stem + '-ROOT-stderr-v1.txt')
    require(not any(p.exists() for p in (terminal_path, provisional_path, observation_path, launch_path, outpath, errpath)),
            'one immutable ROOT attempt; no retry')
    if phase == 'preparation':
        cfg = plan['phase']
        require(cfg['outer_seconds'] == 60 and cfg['bytes'] == CEILING_BYTES, 'unchanged producer limits')
        activation_path = base / plan['activation_basename']
        require(not (base / plan['output_directory']).exists(), 'fresh producer namespace')
        require(not any((base/p).exists() for p in plan['proposed_outputs']), 'no producer outputs yet')
        command = [sys.executable, '-B', str(base/'curriculum_outer_v1.py'), str(plan_path)]
        activation = dict(schema='ROOT-frozen-curriculum-preparation-activation-v1',
            authorized=True, selector=selector, plan=pin(plan_path),
            status='ROOT_authorized_exact_frozen_curriculum_context_preparation_v1')
    else:
        require(plan['limits']['whole_seconds'] == 180 and plan['limits']['peak_bytes'] == CEILING_BYTES,
                'unchanged independent limits')
        activation_path = Path(plan['activation_path'])
        require(not any(Path(p).exists() for p in plan['outputs'].values()), 'fresh independent outputs')
        command = [sys.executable, '-B', plan['owner_path'], str(plan_path)]
        activation = dict(schema='ROOT-independent-frozen-curriculum-static-activation-v1',
            authorized=True, selector=selector, plan=pin(plan_path))
    # Known sandbox metadata restriction is checked before activation/science.
    process_table()
    require(not activation_path.exists(), 'separate immutable activation absent')
    activation.update(ROOT_source_review=pin(review_path), ROOT_dispatcher=pin(Path(__file__)))
    save(activation_path, activation)
    child = None; usage = None; owned = set(); samples = []
    reason = None; error = None; observer_peak = peak(resource.getrusage(resource.RUSAGE_CHILDREN))
    def interrupted(*_):
        raise TimeoutError('ROOT owned gate interrupted')
    signal.signal(signal.SIGTERM, interrupted); signal.signal(signal.SIGINT, interrupted)
    try:
        with outpath.open('xb') as out, errpath.open('xb') as err:
            child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                start_new_session=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            save(launch_path, dict(phase=phase, selector=selector, pid=child.pid,
                preparation_or_static_plan=pin(plan_path), activation=pin(activation_path),
                dispatcher=pin(Path(__file__)), maximum_seconds=maximum, maximum_bytes=CEILING_BYTES))
            while True:
                pid, status, current = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    usage = current; child.returncode = os.waitstatus_to_exitcode(status); break
                elapsed = time.perf_counter() - started
                if elapsed >= maximum - WRITE_RESERVE:
                    raise TimeoutError('ROOT full phase deadline before receipt reserve')
                table = process_table(); owned |= descendants(table, child.pid, owned)
                observer_peak = max(observer_peak, peak(resource.getrusage(resource.RUSAGE_CHILDREN)))
                rss = sum(table[pid][2] for pid in owned if pid in table)
                combined = peak(resource.getrusage(resource.RUSAGE_SELF)) + rss + observer_peak
                samples.append(dict(seconds=elapsed, owned_rss_bytes=rss,
                    ROOT_peak_bytes=peak(resource.getrusage(resource.RUSAGE_SELF)),
                    observer_peak_bytes=observer_peak, combined_bytes=combined,
                    owned_pids=sorted(pid for pid in owned if pid in table)))
                if combined > CEILING_BYTES:
                    raise MemoryError('ROOT observer-inclusive sampled owned memory')
                time.sleep(.025)
    except BaseException as exc:
        reason = 'owned_phase_failure'; error = dict(type=type(exc).__name__, message=str(exc))
        if child is not None and usage is None:
            usage = stop_owned(child, owned)
    require(child is not None and usage is not None, 'actual terminal child ownership')
    table = process_table()
    owned |= {pid for pid,row in table.items() if row[1] == child.pid}
    survivors = sorted(pid for pid in owned if pid in table)
    if survivors:
        reason = reason or 'owned_descendants_still_live'
        for pid in survivors:
            try: os.kill(pid, signal.SIGKILL)
            except ProcessLookupError: pass
    inner = None; evidence = {}
    try:
        if phase == 'preparation':
            inner = read(base/cfg['lifetime']); supervision = read(base/cfg['supervision']); outcome = read(base/cfg['outcome'])
            require(inner['status'] == 'passed_full_fresh_context_preparation_lifetime'
                and inner['worker_reaped_confirmed'] is True and inner['supervisor_reaped'] is True
                and supervision['child_reaped'] is True and supervision['child_exit'] == 0,
                'fully reaped producer descendants and resources')
            require(outcome['selector'] == selector and outcome['plan'] == pin(plan_path), 'actual producer binding')
            evidence = dict(preparation_plan=pin(plan_path),
                compiled_context=pin(ROOT/outcome['compiled_context']['path']),
                preparation_evidence=pin(ROOT/outcome['preparation_evidence']['path']),
                outcome=pin(base/cfg['outcome']), lifetime=pin(base/cfg['lifetime']),
                supervision=pin(base/cfg['supervision']), activation=pin(activation_path))
            inner_observer_bound = supervision['kernel_child_peak_bytes']
            inner_peak = inner['conservative_host_peak_bytes'] + inner_observer_bound
        else:
            inner = read(plan['outputs']['lifetime']); result = read(plan['outputs']['result'])
            require(inner['status'] == plan['required_owner_success_status'] and inner['child_reaped'] is True
                and inner['child_exit'] == 0 and inner['static_context_pool_accepted'] is True
                and result['status'] == plan['required_result_status'] and result['static_context_pool_accepted'] is True,
                'actual independent result and fully reaped worker')
            evidence = dict(static_plan=pin(plan_path), static_result=pin(plan['outputs']['result']),
                static_lifetime=pin(plan['outputs']['lifetime']), static_activation=pin(activation_path),
                independent_source_plan=pin(INDEPENDENT/'source-plan-v1.json'), static_context_pool_accepted=True)
            inner_observer_bound = 0
            inner_peak = max(inner['kernel_conservative_peak_bytes'], inner['sampled_combined_peak_bytes'])
    except BaseException as exc:
        reason = reason or 'missing_or_rejected_inner_receipt'
        error = error or dict(type=type(exc).__name__, message=str(exc))
        inner_peak = 0; inner_observer_bound = 0
    observer_peak = max(observer_peak, peak(resource.getrusage(resource.RUSAGE_CHILDREN)))
    root_peak_before_write = peak(resource.getrusage(resource.RUSAGE_SELF))
    conservative = root_peak_before_write + max(
        peak(usage), inner_peak, max((s['owned_rss_bytes'] for s in samples), default=0)) + observer_peak
    conservative = max(conservative, max((s['combined_bytes'] for s in samples), default=0))
    conservative += WRITE_MEMORY_RESERVE
    elapsed = time.perf_counter() - started
    bound = elapsed + WRITE_RESERVE
    accepted = child.returncode == 0 and reason is None and not survivors and bool(samples) and bound <= maximum and conservative <= CEILING_BYTES
    receipt = dict(schema='ROOT-actual-frozen-curriculum-' + phase + '-terminal-v1',
        selector=selector, owner_exit_code=child.returncode, owner_terminal_reaped=True,
        worker_terminal_reaped=bool(inner and (inner.get('worker_reaped_confirmed') is True if phase == 'preparation' else inner.get('child_reaped') is True)),
        full_resource_accepted=accepted, full_outer_seconds_including_receipt_write=bound,
        conservative_combined_peak_bytes=conservative, maximum_seconds=maximum, maximum_bytes=CEILING_BYTES,
        receipt_write_reserve_seconds=WRITE_RESERVE, receipt_memory_reserve_bytes=WRITE_MEMORY_RESERVE,
        inner_observer_kernel_peak_upper_bound_bytes=inner_observer_bound,
        inner_observer_accounting='For producer: add full supervisor reaped-child kernel peak to bound one sequential short ps observer; may double-count worker. Independent owner already includes its observer peaks.',
        elapsed_before_ROOT_terminal_write_seconds=elapsed,
        timing_kind='Conservative elapsed-plus-reserve bound; post-write observation must pass before use',
        memory_scope='ROOT peak plus max of owned descendant RSS sum/owner kernel peak/inner conservative owned peaks with explicit inner observer bound plus ROOT observer kernel peak and 32MiB validated receipt/launcher reserve; retrospective estimate, no OS hard cap',
        ROOT_source_review=pin(review_path), dispatcher=pin(Path(__file__)), owner_pid=child.pid,
        live_owned_descendants_after_owner_reap=survivors, failure=reason, error=error,
        samples=samples, native_queries=0, new_training=False, target_searches=0, **evidence)
    save(provisional_path, receipt)
    post_write = time.perf_counter() - started
    root_peak_after_write = peak(resource.getrusage(resource.RUSAGE_SELF))
    post_conservative = conservative - WRITE_MEMORY_RESERVE + max(0, root_peak_after_write-root_peak_before_write)
    # Scientific calls are terminal before this observation; never use a
    # provisional positive normalized receipt if its reserve validation fails.
    post_accepted = accepted and post_write <= bound and post_write <= maximum and post_conservative <= conservative and post_conservative <= CEILING_BYTES
    if post_accepted:
        # No receipt-byte serialization follows the charged final write.
        # Metadata publication promotes the already-validated immutable bytes.
        os.link(provisional_path, terminal_path)
    observation = dict(schema='ROOT-context-gate-post-write-observation-v1', phase=phase, selector=selector,
        terminal=pin(terminal_path) if post_accepted else None,
        provisional_terminal=pin(provisional_path), actual_seconds_through_ROOT_terminal_write=post_write,
        peak_after_receipt_serialization_bytes=root_peak_after_write,
        conservative_peak_after_receipt_serialization_bytes=post_conservative,
        memory_reserve_validated=post_conservative <= conservative,
        conservative_terminal_bound_seconds=bound, reserve_validated=post_write <= bound,
        accepted_for_metadata_finalization=post_accepted,
        observation_write_scope='Hard-link metadata promotion and this standard-library observation are outside the charged phase; all immutable normalized receipt-byte serialization/close was charged; no further scientific work',
        scientific_calls_by_dispatcher=0)
    save(observation_path, observation)
    print(json.dumps(dict(phase=phase, selector=selector, accepted=post_accepted, owner_exit=child.returncode,
        actual_seconds_through_ROOT_terminal_write=post_write, conservative_combined_peak_bytes=conservative,
        terminal=pin(terminal_path) if post_accepted else None, provisional_terminal=pin(provisional_path),
        post_write_observation=pin(observation_path), failure=reason, error=error)), flush=True)
    return 0 if post_accepted else 1


if __name__ == '__main__':
    sys.exit(main())
