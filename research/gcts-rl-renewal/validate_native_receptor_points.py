"""Publication gate for the new point/native bridge and historical reader."""
import collections,gzip,json,re,subprocess,time
from pathlib import Path
from audit_tree_kernel import need
from audit_certificate_boundary import sha
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def load(n):return json.loads(gzip.decompress((DOC/n).read_bytes()))
def main():
    began=time.perf_counter();data=load('native-receptor-points-001.json.gz');audit=load('native-receptor-points-audit-001.json.gz')
    need(audit['status']=='passed' and audit['producer_sha256']==sha(DOC/'native-receptor-points-001.json.gz') and audit['source_sha256']==sha(HERE/'audit_native_receptor_points.py'),'independent audit source/data binding')
    for field,root in (('sources',HERE),('reused_sources',HERE),('reused_inputs',DOC)):
        for name,pin in data[field].items():need(sha(root/name)==pin,'measured source/input frozen '+name)
    outcomes=dict(collections.Counter(o['status'] for o in data['observations']))
    need(outcomes==dict(native_proof_discovered=10,exhausted_finite_marked_region=2,exhausted_finite_certificate_grammar=2,unknown_search_budget=5,unknown_native_compilation=1),'all bounded statuses')
    need(len(data['observations'])==20 and len(data['certificates'])==6 and sum(o['queries'] for o in data['observations'])==audit['queries']==360 and audit['point_nodes']==316,'all search and native observations')
    for o in data['observations']:need(sha(DOC/o['artifact']['name'])==o['artifact']['sha256'],'complete cold artifact '+o['case']+o['mode'])
    small=[r for r in audit['finite_equivalence'] if r['status'].startswith('all_words')];need(len(small)==7 and sum(r['words'] for r in small)==4422,'all small grammar words')
    reader=json.loads(subprocess.check_output([NODE,str(HERE/'test_native_receptor_reader.cjs')],text=True));need(reader['status']=='passed' and reader['checks']['lines']==21,'browser-independent reader and native tile checks')
    html=(DOC/'native-receptor-points.html').read_text();need('mathjax@3' in html and "['\\\\(','\\\\)']" in html,'established LaTeX renderer');need(not re.search(r'[∀∃⇒∧∨¬ℕζ]|<su[bp][ >]',html) and not any(chr(i) in html for i in (11,12)),'mathematical notation and escapes')
    need(all('id="'+i+'"' in html for i in ('reader','graph','native','node-control','proof-line-control','case','layer','results-panel','conformance')),'interactive controls and evidence')
    for match in re.findall(r'(?:href|src)="([^"#]+)"',html):
        if match.startswith(('http:','https:')):continue
        p=(DOC/match.split('?')[0].split('#')[0]).resolve()
        if p==DOC/'native-receptor-points-validation-001.json':continue
        need(p.exists(),'local reference '+match)
    index=(DOC/'index.html').read_text();old=subprocess.check_output(['git','-C','/private/tmp/gcts-family-router-publish-20261010','show','2802994c825bdb64de9e0db08c5fb64fe7b82845:docs/research/gcts-rl-renewal/index.html'],text=True)
    panel=re.search(r'  <section class="panel" id="native-receptor-points">.*?</section>\n\n',index,re.S);need(panel is not None,'notebook entry');need((index[:panel.start()]+index[panel.end():]).replace('RESEARCH NOTEBOOK · 61','RESEARCH NOTEBOOK · 60',1)==old,'every historical report byte preserved')
    result=dict(version='native-receptor-points-validation-001',status='passed',producer_sha256=sha(DOC/'native-receptor-points-001.json.gz'),audit_sha256=sha(DOC/'native-receptor-points-audit-001.json.gz'),reader_sha256=sha(DOC/'native-receptor-points-reader-001.json'),reader_source_sha256=sha(DOC/'native-receptor-points.js'),html_sha256=sha(DOC/'native-receptor-points.html'),outcomes=outcomes,reader_checks=reader,seconds=time.perf_counter()-began,sources={n:sha(HERE/n) for n in ('validate_native_receptor_points.py','test_native_receptor_reader.cjs','export_native_receptor_points.py')})
    (DOC/'native-receptor-points-validation-001.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
