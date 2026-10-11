"""Publish compact checked interfaces and actual selected proof-role tiles."""
import gzip,hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal';OUT=ROOT/'.gcts-active/first-order-families-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def selected(obs,model):
    s=obs['search'];lookup={tuple(c['key']):c for c in model['placements']}
    return {k:obs[k] for k in ('native_query','cached_native_acceptance','setup_seconds','worker_wall_seconds','peak_rss_bytes')}|dict(status=s['status'],proof=s['proof'],metrics=s['metrics'],seconds=s['seconds'],root_restored=s['root_restored'],tiles=[lookup[tuple(k)] for k in s['placements']],mode=s['mode'],seed=s['seed'],stochastic=s['stochastic'],limits=s['limits'])
def descriptor(model):return {k:model[k] for k in ('initial_marks','command_counts','arity','families_enabled')}|dict(complete_words=str(model['complete_words']),placement_count=len(model['placements']))
def main():
    audit=json.loads((OUT/'audit.json').read_text());assert audit['status']=='passed';summary=json.loads((OUT/'summary.json').read_text());assert summary['status']=='complete';plan=json.loads((OUT/'plan.json').read_text());training=load(OUT/'training.json.gz');artifacts={}
    def publish(name,b):
        p=DOC/name;p.write_bytes(b);artifacts[name]=dict(sha256=sha(p),bytes=p.stat().st_size)
    # Each complete case is retained. Export can shard observations if a case
    # exceeds the destination's individual-file limit without changing evidence.
    cases=[]
    for spec in plan['cases']:
        path=OUT/(spec['id']+'.json.gz');raw=load(path)
        if path.stat().st_size<95*1024*1024:publish('first-order-families-001-'+path.name,path.read_bytes())
        else:
            core={k:v for k,v in raw.items() if k!='observations'};publish('first-order-families-001-'+spec['id']+'-model.json.gz',gzip.compress(json.dumps(core,separators=(',',':')).encode(),mtime=0))
            for o in raw['observations']:
                publish('first-order-families-001-'+spec['id']+'-'+o['lane']+'-r'+str(o['repetition'])+'.json.gz',gzip.compress(json.dumps(o,separators=(',',':')).encode(),mtime=0))
        observations=[dict(selected(o,raw['models'][o['model_id']]),lane=o['lane'],repetition=o['repetition'],model_id=o['model_id']) for o in raw['observations']]
        cases.append(dict(spec=spec,compiled=raw['compiled'],inventory=raw['inventory'],models={k:descriptor(v) for k,v in raw['models'].items()},observations=observations))
    promotion=training['promotion'];p=promotion['observation'];promotion_compact={k:promotion[k] for k in ('case','compiled','inventory','family')}|dict(observation=selected(p,p['model']),model=descriptor(p['model']))
    tc=[]
    for item in training['cases']:
        episode=next(e for e in training['episodes'] if e['case']==item['case']['id']);tc.append(dict(**item,model=descriptor(episode['observation']['model'])))
    episodes=[{k:e[k] for k in ('id','case','weights_before','weights_after','baseline_after','learning')}|dict(observation=selected(e['observation'],e['observation']['model']),events=e['observation']['search']['events']) for e in training['episodes']]
    t=dict(donors=training['donors'],promotion=promotion_compact,library=training['library'],cases=tc,episodes=episodes,weights=training['weights'],baseline=training['baseline'],features=training['features'],rate=training['rate'],discovery_and_matching_seconds=training['discovery_and_matching_seconds'],training_seconds=training['training_seconds'])
    for name,file in [('first-order-families-training-001.json.gz','training.json.gz'),('first-order-families-native-001.json.gz','native-records.json.gz')]:publish(name,(OUT/file).read_bytes())
    publish('first-order-families-audit-001.json',json.dumps(audit,indent=2).encode()+b'\n');publish('first-order-families-plan-001.json',json.dumps(plan,indent=2).encode()+b'\n')
    closure={**plan['prior_source_closure'],**plan['source_sha256']}
    for p in [Path(__file__),HERE/'test_first_order_families_reader.js',DOC/'first-order-families.js']:closure[str(p.relative_to(ROOT))]=sha(p)
    for f,h in closure.items():assert sha(ROOT/f)==h,f
    publish('first-order-families-source-closure-001.json',json.dumps(dict(version='first-order-families-source-closure-001',files=closure),indent=2).encode()+b'\n')
    native=[{k:q[k] for k in ('id','request','request_sha256','input_sha256','output_sha256','purpose','result','seconds')} for q in load(OUT/'native-records.json.gz')]
    old=load(DOC/'first-order-native-001.json.gz');source=[{k:old[d['source_query']][k] for k in ('id','request','request_sha256','input_sha256','output_sha256','purpose','result','seconds')} for d in training['donors']]
    data=dict(version='first-order-families-reader-001',cases=cases,training=t,source_native=source,native=native,audit=audit,artifacts=artifacts,plan={k:plan[k] for k in ('lanes','schedules','repetitions','arity','episodes','seed','rate','features','fixed_weights','search_limits','training_limits','countermodels','gaps')},pilot_seconds=summary['seconds'],distinct_whole_proofs=summary['distinct_whole_proofs'])
    p=DOC/'first-order-families-reader-001.json';p.write_text(json.dumps(data,separators=(',',':'))+'\n')
    result=dict(status='passed',families=len(t['library']),episodes=len(t['episodes']),cases=len(cases),observations=sum(len(c['observations']) for c in cases),reader_bytes=p.stat().st_size,reader_sha256=sha(p),source_files=len(closure))
    (OUT/'export.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
