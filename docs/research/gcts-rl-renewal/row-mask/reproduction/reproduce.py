"""Reproduce the synthetic finite row-mask controls with Python 3.9 or newer.

Run `python3 reproduce.py` in this directory. Only the six authenticated local
source files are loaded. There is no production catalog, network, mathematical
proof, RL training, or claim of the complete production resource envelope.
"""
import time
ENTRY = time.perf_counter()
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType


def tick(label):
    if time.perf_counter() - ENTRY >= 60:
        raise TimeoutError('finite local deadline: ' + str(label))


def main():
    here = Path(__file__).resolve().parent
    manifest = json.loads((here / 'sources-v1.json').read_text())
    roles = {'core', 'old_compact', 'compact', 'old_raw', 'raw', 'finite_harness'}
    if set(manifest['sources']) != roles:
        raise ValueError('exact six source roles required')
    buffers = {}
    for role, record in manifest['sources'].items():
        if Path(record['file']).name != record['file']:
            raise ValueError('capsule source must be a local file')
        data = (here / record['file']).read_bytes()
        if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('complete source fingerprint mismatch: ' + role)
        buffers[role] = data
    modules = {}
    for role in sorted(buffers):
        tick('cold source import')
        name = '_finite_row_mask_capsule_' + role
        if name in sys.modules:
            raise ValueError('fresh capsule module required')
        module = ModuleType(name)
        module.__file__ = str(here / manifest['sources'][role]['file'])
        sys.modules[name] = module
        exec(compile(buffers[role], module.__file__, 'exec'), module.__dict__)
        modules[role] = module
    result = modules['finite_harness'].run_controls(modules=modules, tick=tick)
    tick('complete finite comparison')
    for role, data in buffers.items():
        if (here / manifest['sources'][role]['file']).read_bytes() != data:
            raise ValueError('source changed during the finite test')
    print(json.dumps({'evidence': result,
        'local_elapsed_seconds': time.perf_counter() - ENTRY,
        'full_production_accepted': False}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
