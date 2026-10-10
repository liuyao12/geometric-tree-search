"""Bind cold records, immutable sources, reader projection and corruption tests."""
import argparse,gzip,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
from export_native_families import project
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def need(value,why):
    if not value:raise ValueError(why)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reader-test',type=Path);args=parser.parse_args();began=time.perf_counter();data=json.loads((DOC/'native-families-001.json').read_text());audit=json.loads((DOC/'native-families-audit-001.json').read_text());reader=json.loads((DOC/'native-families-reader-001.json').read_text())
    for name,pin in data['sources'].items():need(sha(HERE/name)==pin,'measured immutable source '+name)
    for name,pin in data['reused_inputs'].items():need(sha(DOC/name)==pin,'immutable old input '+name)
    need(audit['status']=='passed' and audit['input_sha256']==sha(DOC/'native-families-001.json') and audit['source_sha256']==sha(HERE/'audit_native_families.py'),'whole-tree audit binding')
    for name,pin in audit['helpers'].items():need(sha(HERE/name)==pin,'independent audit helper '+name)
    refs=[d['raw'] for d in data['donors']]+[e['raw'] for e in data['training']['episodes']]+[r for c in data['cases'] for r in c['runs']];need(len(refs)==115 and len({r['file'] for r in refs})==115,'all fresh cold records');total_bytes=0
    for ref in refs:
        path=DOC/ref['file'];need(sha(path)==ref['sha256'] and path.stat().st_size==ref['bytes'],'whole raw cold digest');row=json.loads(gzip.decompress(path.read_bytes()));need(row['semantic_sha256']==ref['semantic_sha256'] and row['result']['status']==ref['status'] and row['result']['attempts']==ref['attempts'],'whole raw status binding');total_bytes+=ref['bytes']
    need(canonical(reader)==canonical(project(data,audit)),'exact reader projection of every declared record')
    old=(DOC/'native-wang-search.js').read_text().split('const api=',1)[0];current=(DOC/'native-families.js').read_text();need(current.startswith(old),'unchanged literal native membership and point kernel')
    need(reader['inventory']['tile_types']==264143617200 and len(reader['library'])==21 and reader['audit']['counts']==audit['counts'],'inventory and audit summaries')
    if args.reader_test:test=json.loads(args.reader_test.read_text())
    else:
        node=shutil.which('node') or '/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node';test=json.loads(subprocess.check_output([node,str(HERE/'test_native_family_reader.cjs')],text=True))
    need(test['status']=='passed' and test['reader_sha256']==sha(DOC/'native-families-reader-001.json') and test['checker_sha256']==sha(DOC/'native-families.js') and test['test_sha256']==sha(HERE/'test_native_family_reader.cjs') and len(test['mutations_rejected'])==33,'actual reader corruption test')
    html=(DOC/'native-families.html').read_text();need(all('id="'+v+'"' in html for v in ('reader','results','training','inventory-panel','rectangle','bindings','policy-pool')),'reader controls');need('native-families.js?v=20261010-nf1' in html and 'mathjax@3' in html and 'type="module"' not in html,'established math renderer');need(not re.search(r'[∀∃⇒∧∨¬ℕζ]|<su[bp][ >]',html),'LaTeX mathematical notation')
    out=dict(version='native-families-validation-001',status='passed',manifest_sha256=sha(DOC/'native-families-001.json'),reader_sha256=sha(DOC/'native-families-reader-001.json'),audit_sha256=sha(DOC/'native-families-audit-001.json'),source_sha256=sha(__file__),measured_sources=len(data['sources']),cold_records=len(refs),compressed_bytes=total_bytes,browser=test,independent_replay=audit['counts'],frozen_kernel='Literal successor, point assignments and rectangle checker copied verbatim from Notebook 58.',scope='Exact projections and digests; unchanged measured sources and old inputs; independent all-tree audit binding; actual reader corruption tests and HTML math/controls. Physical timers and a universal proof compiler theorem remain outside this validation.',seconds=time.perf_counter()-began)
    (DOC/'native-families-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out))
if __name__=='__main__':main()
