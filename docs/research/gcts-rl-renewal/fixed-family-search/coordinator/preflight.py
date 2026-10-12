"""Metadata-only ROOT source gate. No scientific module is imported."""
import ast
import hashlib
import json
import resource
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / '.gcts-active/fixed-family-pool-search-source-20261012'
PUB = Path('/private/tmp/gcts-family-router-publish-20261010')
BASE = '9490fab924508700d8fbb7133227b956fa6db818'
MAIN = 'docs/research/gcts-rl-renewal/index.html'

def pin(path):
    path = Path(path)
    return dict(path=str(path.relative_to(ROOT)) if ROOT in path.parents else str(path),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)

def main():
    started = time.perf_counter()
    planpath = SOURCE/'search-plan-v1.json'
    plan = json.loads(planpath.read_text())
    checked = {}
    occurrences = plan['sources'] + plan['inputs'] + plan['preserved_files']
    for item in occurrences:
        path = ROOT/item['path']
        expected = {k:item[k] for k in ('path','sha256','bytes')}
        assert pin(path) == expected, item['path']
        if item['path'] in checked:
            assert checked[item['path']] == expected
        checked[item['path']] = expected
    assert len(checked) == 803
    integration = json.loads((SOURCE/'integration-v1.json').read_text())
    for item in integration['files']:
        assert pin(ROOT/item['path']) == item
    parsed = []
    for item in plan['sources']:
        ast.parse((ROOT/item['path']).read_text(), filename=item['path'])
        parsed.append(item)
    archive = SOURCE/'source-only-v1.zip'
    with zipfile.ZipFile(archive) as z:
        members = []
        for name in z.namelist():
            raw = z.read(name)
            matches = [p for p in integration['files'] if p['path'] == name or name == Path(p['path']).name]
            assert len(matches) == 1, name
            assert hashlib.sha256(raw).hexdigest() == matches[0]['sha256']
            assert len(raw) == matches[0]['bytes']
            members.append(name)
        assert len(members) == 10
    runtime = plan['runtime']
    assert runtime['executable'] == sys.executable and runtime['platform'] == sys.platform
    assert runtime['binary'] == pin(Path(sys.executable).resolve())
    absent = plan['proposed_outputs'] + [plan['activation_basename']]
    assert all(not (SOURCE/name).exists() for name in absent)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=PUB,text=True).strip() == BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=PUB,text=True)
    baseline = subprocess.check_output(['git','show',BASE+':'+MAIN],cwd=PUB)
    assert (ROOT/MAIN).read_bytes() == baseline, 'concurrent main-report edit'
    with (HERE/'baseline-index.html').open('xb') as f: f.write(baseline)
    receipt = dict(status='passed_ROOT_metadata_preflight', plan=pin(planpath),
        unique_exact_paths=len(checked), pin_occurrences=len(occurrences),
        sources_AST_parsed=parsed, archive=pin(archive), archive_members=members,
        runtime=runtime, all_outputs_and_activation_absent=absent,
        public_baseline_commit=BASE, main_baseline=pin(HERE/'baseline-index.html'),
        scientific_modules_imported=0, scientific_functions_called=0, searches=0,
        metadata_seconds=time.perf_counter()-started,
        metadata_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    with (HERE/'preflight-v1.json').open('x') as f: json.dump(receipt,f,indent=2); f.write('\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('sources_AST_parsed','archive_members','runtime')}))

if __name__ == '__main__': main()
