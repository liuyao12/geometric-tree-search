"""Stage only the checked task manifest into the established clean Pages clone."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PUB=Path('/private/tmp/gcts-family-router-publish-20261010')
BASE='a4adb7b113338e6b8753b880356954b6a26d2086'
PREFIX='docs/research/gcts-rl-renewal/receptor-matching/'
MAIN='docs/research/gcts-rl-renewal/index.html'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=PUB)


def main():
    entries=json.loads((HERE/'task-files.json').read_text());expected={e['path'] for e in entries}
    assert len(entries)==len(expected)
    assert all(p==MAIN or p.startswith(PREFIX) for p in expected)
    assert git('rev-parse','HEAD').decode().strip()==BASE
    existing=set(git('diff','--cached','--name-only','-z').decode().split('\0'))-{''}
    assert not existing or existing==expected,'unrelated staged clone changes'
    for e in entries:
        source=ROOT/e['path'];raw=source.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==e['sha256'] and len(raw)==e['bytes']
        target=PUB/e['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    paths=HERE/'publication-paths.nul';paths.write_bytes(b''.join(e['path'].encode()+b'\0' for e in entries))
    subprocess.check_call(['git','add','--pathspec-from-file='+str(paths),'--pathspec-file-nul'],cwd=PUB)
    staged=set(git('diff','--cached','--name-only','-z').decode().split('\0'))-{''}
    assert staged==expected,(staged-expected,expected-staged)
    for e in entries:
        raw=git('show',':'+e['path'])
        assert hashlib.sha256(raw).hexdigest()==e['sha256'] and len(raw)==e['bytes']
    subprocess.check_call(['git','diff','--cached','--check'],cwd=PUB)
    result={'status':'passed_exact_task_only_staging_and_blob_hashes','baseline_commit':BASE,'task_files':len(entries),'total_bytes':sum(e['bytes'] for e in entries),'prefix':PREFIX,'main_scope':'Single additive panel and106to107counter','unrelated_root_work_staged':False,'task_manifest_sha256':hashlib.sha256((HERE/'task-files.json').read_bytes()).hexdigest(),'staged_exact_manifest':True}
    (HERE/'publication-staging.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
