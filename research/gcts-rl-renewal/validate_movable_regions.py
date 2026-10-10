import hashlib
import json
import subprocess
import time
from pathlib import Path
from export_movable_regions import build

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE = '/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    began = time.perf_counter()
    reader = json.loads((DOC/'movable-regions-reader-001.json').read_bytes())
    if reader != json.loads(json.dumps(build())):
        raise ValueError("exact audited reader projection")
    # The shared JavaScript proof checker is an exact extraction, not a changed
    # copy of the previously exercised quantifier semantics.
    s = (DOC/'quantified-receptors.js').read_text()
    part = (s[:s.index('function points(')]
            + s[s.index('function sourceCommands('):s.index('function compiled(')]
            + s[s.index('function tautology('):s.index('function validate(')]
            + s[s.index('function termTex('):s.index("if(typeof module!=='undefined')")])
    expected = ('(function(root){\n'+part
                +'const api={same,stable,need,free,subst,word,port,checkRows,sourceCommands,primitive,checkRequest,tex,termTex};\n'
                +'if(typeof module!=="undefined")module.exports=api;else root.QuantifiedProof=api;\n'
                +'})(typeof window!=="undefined"?window:undefined);\n')
    if (DOC/'quantified-proof-checks.js').read_text() != expected:
        raise ValueError("unchanged proof checker extraction")
    run = subprocess.run(['python3', '-m', 'unittest', 'discover', '-s', str(HERE),
                          '-p', 'test_movable_regions.py', '-v'], capture_output=True, text=True, check=True)
    print(run.stderr, flush=True)
    checks = json.loads(subprocess.check_output([NODE, str(HERE/'test_movable_reader.cjs')]))
    sources = ('movable_proof_regions.py', 'check_movable_regions.py', 'run_movable_regions.py',
               'audit_movable_regions.py', 'test_movable_regions.py', 'export_movable_regions.py',
               'test_movable_reader.cjs', 'validate_movable_regions.py')
    documents = ('movable-regions.html', 'movable-regions.js', 'quantified-proof-checks.js',
                 'movable-regions-reader-001.json')
    out = dict(version='movable-regions-validation-001', status='passed', tests=9, reader=checks,
               exact_projection=True, unchanged_shared_checker=True,
               sources={n: digest(HERE/n) for n in sources},
               documents={n: digest(DOC/n) for n in documents},
               seconds=time.perf_counter()-began, browser=dict(status='pending'))
    (DOC/'movable-regions-validation-001.json').write_text(json.dumps(out, separators=(',', ':'))+'\n')
    print(json.dumps(checks), flush=True)


if __name__ == '__main__':
    main()
