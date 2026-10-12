"""Exact metadata gates and deferred module loading, no work on import."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def pin(path):
    path=Path(path);h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):h.update(block)
    return {'path':str(path.relative_to(ROOT)),'sha256':h.hexdigest(),'bytes':path.stat().st_size}

def read(path):
    path=Path(path)
    with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as stream:return json.load(stream)

def verify(plan):
    for p in plan['sources']+plan['inputs']+plan['preserved_files']:
        if pin(ROOT/p['path'])!={k:p[k] for k in ('path','sha256','bytes')}:raise ValueError('exact pin mismatch: '+p['path'])
    executable=Path(sys.executable).resolve();runtime=plan['runtime']
    if (str(executable)!=runtime['binary']['path'] or sys.platform!=runtime['platform']
            or hashlib.sha256(executable.read_bytes()).hexdigest()!=runtime['binary']['sha256']
            or executable.stat().st_size!=runtime['binary']['bytes']):raise ValueError('exact resolved runtime binary')
    metadata=Path(runtime['process_metadata']['path'])
    if hashlib.sha256(metadata.read_bytes()).hexdigest()!=runtime['process_metadata']['sha256'] or metadata.stat().st_size!=runtime['process_metadata']['bytes']:
        raise ValueError('exact owned process metadata executable')

def activation(plan,path):
    a=read(HERE/plan['activation_basename'])
    if a.get('status')!=plan['activation_status'] or a.get('plan')!=pin(path):raise ValueError('ROOT exact reviewed activation required')
    return a

def module(name,path):
    path=Path(path);sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value

def load_life(roles):
    # Import only after exact phase/source/prerequisite activation gates.
    search=module('fresh_transfer_prior_search_helper',roles['prior_search_helper'])
    life=search.load_lifecycle(roles['lifecycle_kernel'])
    proposals=module('fresh_transfer_literal_proposal_grammar',roles['proposal_module'])
    return search,life,proposals

def save_json(path,data):
    with Path(path).open('x') as stream:json.dump(data,stream,indent=2,allow_nan=False);stream.write('\n')

def save_gzip(path,data):
    # Streaming serializer; whole decoded expansion files are never loaded here.
    encoder=json.JSONEncoder(indent=2,ensure_ascii=True,allow_nan=False)
    with Path(path).open('xb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as out:
            for block in encoder.iterencode(data):out.write(block.encode('utf8'))
            out.write(b'\n')
