"""Publication gate: frozen measured sources, audited data and reader mutation checks."""
import gzip,hashlib,json,re,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';ROOT=HERE.parents[1]
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(t,m):
    if not t:raise ValueError(m)
def main():
    start=time.perf_counter();data=json.loads(gzip.decompress((DOC/'certificate-boundary-001.json.gz').read_bytes()));audit=json.loads(gzip.decompress((DOC/'certificate-boundary-audit-001.json.gz').read_bytes()))
    need(audit['status']=='passed' and audit['producer_sha256']==sha(DOC/'certificate-boundary-001.json.gz') and audit['source_sha256']==sha(HERE/'audit_certificate_boundary.py'),'audited manifest')
    for f,root in (('sources',HERE),('reused_sources',HERE),('reused_inputs',DOC)):
        for n,p in data[f].items():need(sha(root/n)==p,'frozen source/input '+n)
    need(len(data['observations'])==28 and len(data['certificates'])==4,'all cold/certificate runs');need(sum(o['queries'] for o in data['observations'])==audit['queries'],'all query replay coverage')
    outcomes={s:sum(o['status']==s for o in data['observations']) for s in ('native_proof_discovered','exhausted_finite_certificate_grammar','unknown_search_budget')};need(outcomes==dict(native_proof_discovered=12,exhausted_finite_certificate_grammar=8,unknown_search_budget=8),'bounded outcomes')
    for row in data['observations']:
        p=DOC/row['artifact']['name'];need(sha(p)==row['artifact']['sha256'],'cold raw trace pin')
    reader=json.loads(subprocess.check_output([NODE,str(HERE/'test_certificate_boundary_reader.cjs')],text=True));need(reader['status']=='passed','reader mutations')
    html=(DOC/'certificate-boundary.html').read_text();need(all('id="'+n+'"' in html for n in ('reader','search','results-panel','markings','case','proof-line-control','layer','literal','dependencies','query-table')),'reader controls');need('mathjax@3' in html and "['\\\\(','\\\\)']" in html,'established LaTeX renderer');need(not re.search(r'[∀∃⇒∧∨¬ℕζ]|<su[bp][ >]',html),'LaTeX notation')
    need(not any(chr(i) in html for i in (11,12)) and 'ARightarrow' not in html and 'orall' not in html.replace(r'\forall',''),'no damaged static math escapes')
    need(all(v in html for v in (r'\(28\)',r'\(128\)',r'\(10^9\)',r'\forall x',r'\vdash',r'\operatorname{Point}')),'static formulas retain LaTeX')
    for match in re.findall(r'(?:href|src)="([^"#]+)"',html):
        if match.startswith(('http:','https:')):continue
        p=(DOC/match.split('?')[0].split('#')[0]).resolve()
        if p==DOC/'certificate-boundary-validation-001.json':continue # generated below after this gate
        need(p.exists(),'local link '+match)
    index=(DOC/'index.html').read_text();need('RESEARCH NOTEBOOK · 60' in index and 'id="certificate-boundary"' in index,'current notebook entry')
    old=subprocess.check_output(['git','-C','/private/tmp/gcts-family-router-publish-20261010','show','47b5d0cf837133cc5d6a5c390ca09cee47ff2703:docs/research/gcts-rl-renewal/index.html'],text=True);section=re.search(r'  <section class="panel" id="certificate-boundary">.*?</section>\n\n',index,re.S);need(section is not None,'new panel');need((index[:section.start()]+index[section.end():]).replace('RESEARCH NOTEBOOK · 60','RESEARCH NOTEBOOK · 59',1)==old,'all historical notebook content preserved')
    out=dict(version='certificate-boundary-validation-001',status='passed',producer_sha256=sha(DOC/'certificate-boundary-001.json.gz'),audit_sha256=sha(DOC/'certificate-boundary-audit-001.json.gz'),reader_sha256=sha(DOC/'certificate-boundary-reader-001.json'),outcomes=outcomes,reader_checks=reader,seconds=time.perf_counter()-start,sources={n:sha(HERE/n) for n in ('validate_certificate_boundary.py','test_certificate_boundary_reader.cjs','export_certificate_boundary.py')})
    (DOC/'certificate-boundary-validation-001.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
