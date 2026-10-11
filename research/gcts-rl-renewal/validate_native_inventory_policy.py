"""Publication gate for the audited point/inventory/policy/native experiment."""
import collections,gzip,hashlib,json,re,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
LEDGER=ROOT/'.gcts-active/native-inventory-policy-20261010'
BASE='93a11131f48f720891463f7f86797194a9b2917b'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n):return json.loads(gzip.decompress((DOC/n).read_bytes()))
def need(x,message):
    if not x:raise ValueError(message)
def main():
    began=time.perf_counter();data=load('native-inventory-001.json.gz');audit=load('native-inventory-audit-001.json.gz')
    need(audit['status']=='passed' and audit['producer_sha256']==sha(DOC/'native-inventory-001.json.gz') and audit['source_sha256']==sha(HERE/'audit_native_inventory_policy.py'),'independent source/data bindings')
    for field,root in (('sources',HERE),('reused_sources',HERE),('reused_inputs',DOC)):
        for n,p in data[field].items():need(sha(root/n)==p,'frozen measured source/input '+n)
    need(len(data['observations'])==70 and len(data['certificates'])==8 and audit['queries']==501 and audit['point_nodes']==16577 and audit['policy_events']==2469 and len(audit['mutations_rejected'])==18,'complete pilot coverage')
    outcomes=dict(collections.Counter(o['status'] for o in data['observations']))
    need(outcomes==dict(native_proof_discovered=44,unknown_search_budget=16,exhausted_finite_marked_region=10),'all bounded outcomes retained')
    for o in data['observations']:need(sha(DOC/o['artifact']['name'])==o['artifact']['sha256'],'entire cold artifact '+o['artifact']['name'])
    for c in data['certificates']:
        for k in ('grammar','events','responses'):need(sha(DOC/c[k]['name'])==c[k]['sha256'],'full certificate artifact '+c[k]['name'])
    training=load(data['training']['name']);policy=json.loads((DOC/data['policy']['name']).read_text());view=json.loads((DOC/'native-inventory-reader-001.json').read_text())
    need(sha(DOC/data['training']['name'])==data['training']['sha256'] and sha(DOC/data['policy']['name'])==data['policy']['sha256'],'frozen training and policy artifacts')
    need(view['producer_sha256']==sha(DOC/'native-inventory-001.json.gz') and view['audit']['sha256']==sha(DOC/'native-inventory-audit-001.json.gz') and view['policy_sha256']==data['policy']['sha256'] and view['training_sha256']==data['training']['sha256'],'reader artifact pins')
    need(view['cases']==data['cases'] and view['observations']==data['observations'] and view['policy']==policy and view['training']['episodes']==training['episodes'] and view['training']['weights']==training['weights'],'all raw evaluation and learning records projected exactly')
    for p,c,checked in zip(view['proofs'],data['certificates'],audit['certificates']):
        need(p['name']==c['name'] and p['case']==c['case_id'] and p['role']==c['role'] and p['request']==c['request'] and p['request_sha256']==checked['request_sha256'],'actual discovered request projection')
        if p['role']=='inventory_donor':
            donor=next(d for d in training['donors'] if d['case']['id']==p['case'])
            trace=dict(**donor,proof=donor['search']['proof'],status='native_proof_discovered',records=training['records'],queries=training['queries'])
        else:
            o=next(o for o in data['observations'] if o['case']==p['case'] and o['mode']=='learned' and o['status']=='native_proof_discovered')
            trace=load(o['artifact']['name'])
        need(p['trace']==trace,'unmodified actual source trace '+p['case'])
        for l,a in zip(p['lines'],checked['lines']):
            need(l['input']==a['input_context'] and l['output']==a['output_context'] and l['label']==a['label'] and l['outcome']==a['outcome'] and l['node']==a['fragment']['node'],'native contexts and semantic labels')
    reader=json.loads((LEDGER/'reader-tests.log').read_text());binding=json.loads((LEDGER/'reader-test-bindings.json').read_text())
    need(reader['status']=='passed' and reader['checks']['lines']==39 and len(reader['mutations_rejected'])==44,'reader/native/policy mutation checks')
    for n,p in binding.items():need(sha(ROOT/n)==p,'checked reader test source/data '+n)
    html=(DOC/'native-inventory-policy.html').read_text()
    need('mathjax@3' in html and "['\\\\(','\\\\)']" in html,'established LaTeX renderer')
    need(not re.search(r'[∀∃⇒∧∨¬ℕζ]|<su[bp][ >]',html) and not any(chr(i) in html for i in (11,12)),'mathematical notation and source escapes')
    for i in ('reader','graph','native','inventory','training','results-panel','conformance','case','proof-line-control','layer','node-control','family-control','decision-control','proposal-control','episode-control'):
        need('id="'+i+'"' in html,'interactive evidence '+i)
    for link in re.findall(r'(?:href|src)="([^"#]+)"',html):
        if link.startswith(('http:','https:')):continue
        p=(DOC/link.split('?')[0].split('#')[0]).resolve()
        if p==DOC/'native-inventory-validation-001.json':continue
        need(p.exists(),'local reference '+link)
    index=(DOC/'index.html').read_text();old=subprocess.check_output(['git','-C','/private/tmp/gcts-family-router-publish-20261010','show',BASE+':docs/research/gcts-rl-renewal/index.html'],text=True)
    panel=re.search(r'  <section class="panel" id="native-inventory-policy">.*?</section>\n\n',index,re.S)
    need(panel is not None and (index[:panel.start()]+index[panel.end():]).replace('RESEARCH NOTEBOOK · 62','RESEARCH NOTEBOOK · 61',1)==old,'every historical report byte preserved')
    result=dict(version='native-inventory-validation-001',status='passed',base_commit=BASE,producer_sha256=sha(DOC/'native-inventory-001.json.gz'),audit_sha256=sha(DOC/'native-inventory-audit-001.json.gz'),reader_sha256=sha(DOC/'native-inventory-reader-001.json'),reader_source_sha256=sha(DOC/'native-inventory-policy.js'),html_sha256=sha(DOC/'native-inventory-policy.html'),outcomes=outcomes,reader_checks=reader,seconds=time.perf_counter()-began,sources={n:sha(HERE/n) for n in ('validate_native_inventory_policy.py','test_native_inventory_reader.cjs','test_native_inventory.py','export_native_inventory_policy.py')})
    (DOC/'native-inventory-validation-001.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
