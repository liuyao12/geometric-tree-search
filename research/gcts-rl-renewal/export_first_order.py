"""Compact selected proofs and compiler admissions; full tree evidence separate."""
import gzip,hashlib,json,shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal';OUT=ROOT/'.gcts-active/first-order-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    audit=json.loads((OUT/'audit.json').read_text());assert audit['status']=='passed';plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text());assert summary['status']=='complete'
    artifacts={};cases=[]
    def publish(name,data):
        p=DOC/name;p.write_bytes(data);artifacts[name]=dict(sha256=sha(p),bytes=p.stat().st_size)
    for spec in plan['cases']:
        path=OUT/(spec['id']+'.json.gz');publish('first-order-001-'+path.name,path.read_bytes());raw=load(path)
        lookup={tuple(c['key']):c for c in raw['model']['placements']};observations=[]
        for obs in raw['observations']:
            s=obs['search'];observations.append({k:obs[k] for k in ('mode','repetition','native_query','cached_native_acceptance','setup_seconds','worker_wall_seconds','peak_rss_bytes')}|dict(status=s['status'],proof=s['proof'],metrics=s['metrics'],seconds=s['seconds'],root_restored=s['root_restored'],tiles=[lookup[tuple(k)] for k in s['placements']]))
        cases.append(dict(spec=spec,compiled=raw['compiled'],initial_marks=raw['model']['initial_marks'],command_counts=raw['model']['command_counts'],
            complete_words=str(raw['model']['complete_words']),placement_count=len(raw['model']['placements']),observations=observations))
    publish('first-order-native-001.json.gz',(OUT/'native-records.json.gz').read_bytes())
    publish('first-order-audit-001.json',json.dumps(audit,indent=2).encode()+b'\n')
    publish('first-order-plan-001.json',json.dumps(plan,indent=2).encode()+b'\n')
    closure=dict(plan['prior_source_closure']);closure.update(plan['source_sha256'])
    for p in [Path(__file__),HERE/'test_first_order_reader.js',DOC/'first-order.js']:closure[str(p.relative_to(ROOT))]=sha(p)
    for f,h in closure.items():assert sha(ROOT/f)==h,f
    publish('first-order-source-closure-001.json',json.dumps(dict(version='first-order-source-closure-001',files=closure),indent=2).encode()+b'\n')
    native=[{k:q[k] for k in ('id','request','request_sha256','input_sha256','output_sha256','purpose','result','seconds')} for q in load(OUT/'native-records.json.gz')]
    data=dict(version='first-order-reader-001',cases=cases,native=native,audit=audit,artifacts=artifacts,
        modes=plan['modes'],repetitions=plan['repetitions'],limits=plan['search_limits'],pilot_seconds=summary['seconds'],
        distinct_final_proofs=summary['distinct_final_proofs'],scope=plan['gaps'],policy_sha256=plan['policy_sha256'])
    p=DOC/'first-order-reader-001.json';p.write_text(json.dumps(data,separators=(',',':'))+'\n')
    result=dict(status='passed',cases=len(cases),observations=sum(len(c['observations']) for c in cases),proofs=sum(o['proof'] is not None for c in cases for o in c['observations']),reader_bytes=p.stat().st_size,reader_sha256=sha(p),source_files=len(closure))
    (OUT/'export.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
