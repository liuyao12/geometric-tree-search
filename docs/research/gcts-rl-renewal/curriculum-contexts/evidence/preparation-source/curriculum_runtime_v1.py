"""Exact source-only curriculum plan gates; scientific imports are deferred."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SELECTORS = ('donor-two-guards', 'donor-two-equalities',
             'donor-repeated-guard', 'donor-repeated-equality',
             'heldout-mixed-guard-equality')


def pin(path, declared_path=None):
    path = Path(path).resolve(); digest = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block); size += len(block)
    if declared_path is None:
        try:
            declared_path = str(path.relative_to(ROOT))
        except ValueError:
            declared_path = str(path)
    return {'path': declared_path, 'sha256': digest.hexdigest(), 'bytes': size}


def read(path):
    path = Path(path)
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as stream:
        return json.load(stream)


def plan_path(argument):
    path = Path(argument).resolve()
    if path.parent != HERE or path.name not in tuple('preparation-' + s + '-plan-v1.json' for s in SELECTORS):
        raise ValueError('one exact frozen per-selector preparation plan required')
    return path


def verify(plan):
    if (plan['schema'] != 'frozen-curriculum-family-preparation-plan-v1'
            or plan['selector'] not in SELECTORS
            or plan['phase']['kind'] != 'preparation'
            or plan['execution_authorized_by_source_freeze'] is not False):
        raise ValueError('unchanged source-only per-context preparation plan')
    seen = {}
    for record in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        literal = {k: record[k] for k in ('path', 'sha256', 'bytes')}
        if record['path'] not in seen:
            seen[record['path']] = pin(ROOT / record['path'], record['path'])
        if seen[record['path']] != literal:
            raise ValueError('exact source/input/preserved pin changed: ' + record['path'])
    runtime = plan['runtime']; executable = Path(sys.executable).resolve()
    if (str(executable) != runtime['binary']['path'] or sys.platform != runtime['platform']
            or hashlib.sha256(executable.read_bytes()).hexdigest() != runtime['binary']['sha256']
            or executable.stat().st_size != runtime['binary']['bytes']):
        raise ValueError('exact resolved owned runtime')
    observer = Path(runtime['process_metadata']['path'])
    if (observer != Path('/bin/ps') or hashlib.sha256(observer.read_bytes()).hexdigest() != runtime['process_metadata']['sha256']
            or observer.stat().st_size != runtime['process_metadata']['bytes']):
        raise ValueError('exact process metadata executable')
    prefix = 'outputs/' + plan['selector'] + '/'
    if (plan['output_directory'] != prefix[:-1]
            or any(type(name) is not str or not name.startswith(prefix)
                   or Path(name).parent != Path(prefix) for name in plan['proposed_outputs'])):
        raise ValueError('every immutable output stays in its exact selector namespace')
    if len(plan['proposed_outputs']) != len(set(plan['proposed_outputs'])):
        raise ValueError('output identities cannot alias')
    for name in ('compiled_context', 'preparation_evidence'):
        if plan['outputs'][name] not in plan['proposed_outputs']:
            raise ValueError('both full scientific artifacts must be declared')
    for name in ('stdout', 'stderr', 'launch', 'outcome', 'supervision', 'lifetime'):
        if plan['phase'][name] not in plan['proposed_outputs']:
            raise ValueError('complete owned lifetime artifact must be declared')
    return len(seen)


def activation(plan, path):
    record = read(HERE / plan['activation_basename'])
    if (record.get('schema') != 'ROOT-frozen-curriculum-preparation-activation-v1'
            or record.get('authorized') is not True or record.get('selector') != plan['selector']
            or record.get('status') != plan['activation_status'] or record.get('plan') != pin(path)):
        raise ValueError('exact ROOT reviewed per-context activation required')
    return record


def module(name, path):
    path = Path(path); sys.path.insert(0, str(path.parent))
    specification = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(specification); sys.modules[name] = value
    specification.loader.exec_module(value)
    return value


def load_life(roles):
    search = module('frozen_curriculum_prior_search_helper', roles['prior_search_helper'])
    life = search.load_lifecycle(roles['lifecycle_kernel'])
    proposals = module('frozen_curriculum_complete_proposal_grammar', roles['proposal_module'])
    return search, life, proposals


def save_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def save_gzip(path, value):
    encoder = json.JSONEncoder(indent=2, ensure_ascii=True, allow_nan=False)
    with Path(path).open('xb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as stream:
            for block in encoder.iterencode(value):
                stream.write(block.encode('utf8'))
            stream.write(b'\n')
