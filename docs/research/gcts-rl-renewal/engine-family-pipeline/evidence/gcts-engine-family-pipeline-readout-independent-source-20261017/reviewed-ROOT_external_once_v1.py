"""Root external measurement only; never imports any project/search/checker code.

One exact frozen plan is consumed under unchanged native meter2. The native
postterminal clock probe runs immediately after meter exit, including interpreter
startup in the stricter launch-to-postprobe twenty-second acceptance check.
All result interpretation is a later saved-data operation by Root.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

RUNTIME = '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'
RUNTIME_PIN = ('bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e', 102352)
METER = '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py'
METER_PIN = ('0129830110b8f46a1cfd376ced0cd147aa2f224665b4a0cce36ae82f2106d67e', 6734)


def raw_pin(path):
    raw = Path(path).read_bytes()
    return (hashlib.sha256(raw).hexdigest(), len(raw))


def emit(path, value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'
    with Path(path).open('xb') as stream:
        stream.write(raw)


def main(argv):
    if len(argv) != 4:
        raise ValueError('sole plan path, expected plan SHA, expected bytes, fresh external directory')
    plan_path, expected_sha, expected_bytes, external_path = argv
    external = Path(external_path)
    if not external.is_absolute() or external != external.resolve() or external.exists():
        raise ValueError('fresh canonical external directory')
    if raw_pin(RUNTIME) != RUNTIME_PIN or raw_pin(METER) != METER_PIN:
        raise ValueError('unchanged trusted runtime and native meter2')
    plan_raw = Path(plan_path).read_bytes()
    if (hashlib.sha256(plan_raw).hexdigest(), len(plan_raw)) != (expected_sha, int(expected_bytes)):
        raise ValueError('complete frozen plan identity')
    plan = json.loads(plan_raw)
    intake = plan['sources']['intake']
    if raw_pin(intake['path']) != (intake['sha256'], intake['bytes']):
        raise ValueError('exact frozen intake source')
    external.mkdir(mode=0o700)
    emit(external/'ONCE.json', {'schema':'ROOT-ordinary-once-consumed-v1',
        'plan_sha256':expected_sha,'plan_bytes':int(expected_bytes),
        'invocation_id':plan['invocation_id'],'purpose':plan['purpose']})
    began = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    argv_meter = [RUNTIME,'-I','-S','-B',METER,str(external/'native-terminal.json'),
                  RUNTIME,'-I','-S','-B',intake['path'],plan_path]
    with (external/'meter-stdout.txt').open('xb') as stdout, (external/'meter-stderr.txt').open('xb') as stderr:
        result = subprocess.run(argv_meter, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}, timeout=65)
    # This probe is a new native process, not a timestamp reconstructed later.
    probe_code = 'import time;print(time.clock_gettime_ns(time.CLOCK_MONOTONIC))'
    probe = subprocess.run([RUNTIME,'-I','-S','-B','-c',probe_code],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}, timeout=5)
    if probe.returncode != 0 or not probe.stdout.endswith(b'\n') or not probe.stdout[:-1].isdigit():
        raise RuntimeError('genuine postterminal native clock probe failed')
    (external/'postterminal-probe-stdout.txt').write_bytes(probe.stdout)
    (external/'postterminal-probe-stderr.txt').write_bytes(probe.stderr)
    observation = {'schema':'ROOT-ordinary-external-observation-v1',
        'external_began_ns':began,'postterminal_native_probe_ns':int(probe.stdout),
        'meter_returncode':result.returncode,'probe_returncode':probe.returncode,
        'plan_sha256':expected_sha,'plan_bytes':int(expected_bytes),
        'invocation_id':plan['invocation_id'],'purpose':plan['purpose'],
        'measurement_only':True,'ROOT_primary_accepted':False,'ROOT_resource_accepted':False}
    emit(external/'observation.json', observation)
    print(json.dumps(observation, sort_keys=True))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
