"""Task-only publication gate for semantic lemma discovery and native proofs."""
import collections,gzip,hashlib,json,re,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
LEDGER=ROOT/'.gcts-active/semantic-receptor-inventory-20261010';BASE='221ab648b3fcbd5393c7987ce5cb7be012103390'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n):return json.loads(gzip.decompress((DOC/n).read_bytes()))
def same(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
def need(x,message):
    if not x:raise ValueError(message)
def main():
    began=time.perf_counter();data=load('semantic-inventory-001.json.gz');audit=load('semantic-inventory-audit-001.json.gz')
    need(audit['status']=='passed' and audit['producer_sha256']==sha(DOC/'semantic-inventory-001.json.gz')
         and audit['source_sha256']==sha(HERE/'audit_semantic_inventory.py'),'independent native and graph audit bindings')
    for n,p in audit['dependency_sha256'].items():need(sha(HERE/n)==p,'complete audit dependency '+n)
    for field,root in (('sources',HERE),('reused_sources',HERE),('reused_inputs',DOC)):
        for n,p in data[field].items():need(sha(root/n)==p,'frozen source/input '+n)
    closure=json.loads((DOC/'semantic-inventory-source-closure-001.json').read_text())
    need(closure['base_commit']==BASE and len(closure['sources'])==29 and audit['runtime_closure_sha256']==sha(DOC/'semantic-inventory-source-closure-001.json'),'full frozen worker runtime closure')
    for row in closure['sources']:need(sha(ROOT/row['path'])==row['sha256'],'runtime source '+row['path'])
    need(len(data['observations'])==96 and len(data['certificates'])==9 and audit['training']['episodes']==24
         and audit['training']['families']==4 and audit['finite_equivalence']['words']>0
         and audit['finite_equivalence']['accepted']==audit['finite_equivalence']['exact_regions'],'complete declared experiment and finite differential census')
    outcomes=dict(collections.Counter(o['status'] for o in data['observations']))
    for o in data['observations']:need(sha(DOC/o['artifact']['name'])==o['artifact']['sha256'],'whole cold artifact '+o['artifact']['name'])
    for c in data['certificates']:
        for k in ('grammar','events','responses'):need(sha(DOC/c[k]['name'])==c[k]['sha256'],'whole native certificate '+c[k]['name'])
    training=load(data['training']['name']);policy=json.loads((DOC/data['policy']['name']).read_text())
    view=json.loads((DOC/'semantic-inventory-reader-001.json').read_text())
    need(sha(DOC/data['training']['name'])==data['training']['sha256'] and sha(DOC/data['policy']['name'])==data['policy']['sha256'],'actual frozen training and policy')
    for k,p in dict(producer_sha256=sha(DOC/'semantic-inventory-001.json.gz'),audit_sha256=sha(DOC/'semantic-inventory-audit-001.json.gz'),
                    policy_sha256=data['policy']['sha256'],training_sha256=data['training']['sha256'],source_closure_sha256=sha(DOC/'semantic-inventory-source-closure-001.json')).items():
        need(view[k]==p,'reader provenance '+k)
    need(view['cases']==data['cases'] and view['observations']==data['observations'] and view['policy']==policy,'complete cold outcome and inventory projection')
    need(len(view['first_decisions'])==4,'all disclosed first-decision contrasts')
    for decision in view['first_decisions']:
        raw=load(decision['source']['name'])
        need(decision['event']==raw['search']['events'][0] and raw['case']['id']==decision['case']
             and raw['mode']==decision['mode'],'unaltered first held-out decision')
    need(view['training']['weights']==training['weights'] and view['training']['baseline']==training['baseline'],'all training updates projected')
    for projected,original in zip(view['training']['episodes'],training['episodes']):
        for k,v in original.items():
            if k=='search':
                for field,value in projected[k].items():need(value==v[field],'actual episode search '+field)
            else:need(projected[k]==v,'actual episode feedback '+k)
    for p,c,checked in zip(view['proofs'],data['certificates'],audit['certificates']):
        need(p['name']==c['name'] and p['case']==c['case_id'] and p['role']==c['role'] and same(p['request'],c['request'])
             and p['request_sha256']==checked['request_sha256'],'actual searched native certificate projection')
        if p['role']=='primitive_inventory_donor':raw=next(d for d in training['donors'] if d['case']['id']==p['case']);records=training['records']
        elif p['role']=='higher_inventory_donor':raw=training['promotion'];records=training['records']
        else:raw=load(p['trace']['source']['name']);records=raw['records']
        selected=set(map(tuple,raw['search']['placements']));expected=[q for q in raw['model']['placements'] if tuple(q['key']) in selected]
        need(p['trace']['selected']==expected and p['trace']['placements']==raw['search']['placements']
             and same(p['trace']['verification'],records[raw['verification_query']]),'unchanged point and native search projection')
        need(len(p['lines'])==len(checked['lines']),'all local/root lines projected')
        for line,a in zip(p['lines'],checked['lines']):
            need(line['input']==a['input_context'] and line['output']==a['output_context'] and line['label']==a['label']
                 and line['outcome']==a['outcome'] and line['node']==a['fragment']['node'],'actual native scope and line context')
    reader=json.loads((LEDGER/'reader-tests.log').read_text());bindings=json.loads((LEDGER/'reader-test-bindings.json').read_text())
    need(reader['status']=='passed' and reader['proofs']==9 and reader['lines']==sum(len(p['lines']) for p in view['proofs'])
         and len(reader['mutations_rejected'])==16,'native reader, policy and corruption checks')
    for n,p in bindings.items():need(sha(ROOT/n)==p,'checked reader test source/data '+n)
    html=(DOC/'semantic-inventory.html').read_text()
    need('mathjax@3' in html and "['\\\\(','\\\\)']" in html,'established LaTeX renderer')
    need(not re.search(r'[∀∃⇒∧∨¬ℕζ]|<su[bp][ >]',html) and not any(chr(i) in html for i in (11,12)),'mathematical notation and source escapes')
    for i in ('reader','inventory','native','training','results','evidence','assertion-control','scope-control','proof-line-control','family-control','episode-control','decision-control','proposal-control'):
        need('id="'+i+'"' in html,'interactive proof evidence '+i)
    for link in re.findall(r'(?:href|src)="([^"#]+)"',html):
        if link.startswith(('http:','https:')):continue
        path=(DOC/link.split('?')[0].split('#')[0]).resolve()
        if path==DOC/'semantic-inventory-validation-001.json':continue
        need(path.exists(),'local report reference '+link)
    index=(DOC/'index.html').read_text();old=subprocess.check_output(['git','-C','/private/tmp/gcts-family-router-publish-20261010','show',BASE+':docs/research/gcts-rl-renewal/index.html'],text=True)
    panel=re.search(r'  <section class="panel" id="semantic-inventory">.*?</section>\n\n',index,re.S)
    need(panel is not None and (index[:panel.start()]+index[panel.end():]).replace('RESEARCH NOTEBOOK · 63','RESEARCH NOTEBOOK · 62',1)==old,'every historical report byte preserved')
    result=dict(version='semantic-inventory-validation-001',status='passed',base_commit=BASE,
        producer_sha256=sha(DOC/'semantic-inventory-001.json.gz'),audit_sha256=sha(DOC/'semantic-inventory-audit-001.json.gz'),
        reader_sha256=sha(DOC/'semantic-inventory-reader-001.json'),reader_source_sha256=sha(DOC/'semantic-inventory.js'),
        html_sha256=sha(DOC/'semantic-inventory.html'),outcomes=outcomes,reader_checks=reader,seconds=time.perf_counter()-began,
        conformance=dict(point_roots='All finite C/G/B obligations active, including untouched points',
            scheduler='Full all-node dead/forced/generation audit; all roots in this finite model have generation zero',
            marks='Complete exact integer assignments, including distant points and inactive minus-one values',
            rollback='Every original state fingerprint and complete fallback independently replayed',
            learning='Ordering only; no learned candidate exclusion',
            specialized='Finite syntax, unit occupancy, semantic registration and grouped exact SMT control explicitly declared',
            gaps=['No arbitrary fractional-support or changing-rule cases in this adapter; shared kernel tests are earlier evidence',
                  'No geometric or infinite-domain equivalence claim','No universal high-level compiler theorem',
                  'No full PA/Hilbert completeness or competitive prover superiority',
                  'Single learned seed and two deterministic cold repetitions; auxiliary replay overlap limits timing inference']),
        sources={n:sha(HERE/n) for n in ('validate_semantic_inventory.py','test_semantic_inventory_reader.cjs','test_semantic_receptors.py','export_semantic_inventory.py')})
    (DOC/'semantic-inventory-validation-001.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
