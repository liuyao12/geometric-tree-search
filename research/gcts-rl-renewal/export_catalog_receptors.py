"""Export actual measured selections, exact dictionaries, costs and audit scope."""
import gzip,hashlib,json,shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/catalog-receptors-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def main():
    plan=json.loads((DOC/'catalog-receptors-plan-001.json').read_text());audit=json.loads((OUT/'audit.json').read_text());summary=json.loads((OUT/'summary.json').read_text())
    assert audit['status']=='passed' and summary['status']=='complete'
    files={};cases=[]
    def copy(src,dest):
        shutil.copyfile(OUT/src,DOC/dest);p=DOC/dest;files[dest]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    for name in plan['cases']:
        raw=load(OUT/(name+'.json.gz'));copy(name+'.json.gz','catalog-receptors-001-'+name+'.json.gz')
        models={r:load(OUT/(name+'-'+r+'-model.json.gz')) for r in ('word','compact')}
        lookup={r:{tuple(t['key']):t for t in m['placements']} for r,m in models.items()}
        for r in models:copy(name+'-'+r+'-model.json.gz','catalog-receptors-model-001-'+name+'-'+r+'.json.gz')
        observations=[]
        for obs in raw['observations']:
            rep=plan['lanes'][obs['lane']]['representation'];s=obs['search']
            observations.append({k:obs[k] for k in ('lane','repetition','setup_seconds','model_reporting_seconds','model_stats','worker_wall_seconds','peak_rss_bytes','native_query','cached_native_acceptance')}|{k:s[k] for k in ('status','proof','metrics','graph_metrics','mode','feature_semantics','seconds','limits','seed','root_restored')}|dict(tiles=[lookup[rep][tuple(k)] for k in s['placements']]))
        case=dict(spec=raw['case'],inventory=raw['inventory'],catalog=models['compact']['catalog'],observations=observations,audit=next(x for x in audit['cases'] if x['id']==name),prior_preparation=dict(compile_seconds=raw['compiled']['seconds'],matching_seconds=raw['inventory']['matching_seconds'],admission_seconds=raw['inventory']['admission_seconds']))
        cases.append(case);print('exported',name,flush=True)
    for src,dest in [('native.json.gz','catalog-receptors-native-001.json.gz'),('audit.json','catalog-receptors-audit-001.json'),('summary.json','catalog-receptors-summary-001.json'),('host-context.json','catalog-receptors-host-context-001.json')]:copy(src,dest)
    closure=dict(plan['sources'])
    for f in ['research/gcts-rl-renewal/export_catalog_receptors.py','docs/research/gcts-rl-renewal/catalog-receptors.js','research/gcts-rl-renewal/test_catalog_receptors_reader.js']:
        closure[f]=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
    (DOC/'catalog-receptors-source-closure-001.json').write_text(json.dumps(dict(version='catalog-receptors-closure-001',files=closure),indent=2)+'\n')
    for n in ['catalog-receptors-plan-001.json','catalog-receptors-source-closure-001.json']:
        p=DOC/n;files[n]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    data=dict(version='catalog-receptors-reader-001',plan=plan,cases=cases,native=load(OUT/'native.json.gz'),audit=audit,summary=summary,host_context=json.loads((OUT/'host-context.json').read_text()),artifacts=files,plan_sha256=hashlib.sha256((DOC/'catalog-receptors-plan-001.json').read_bytes()).hexdigest())
    p=DOC/'catalog-receptors-reader-001.json';p.write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False)+'\n')
    (OUT/'export.json').write_text(json.dumps(dict(status='complete',reader_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),reader_bytes=p.stat().st_size,artifact_files=len(files)),indent=2)+'\n')

if __name__=='__main__':main()
