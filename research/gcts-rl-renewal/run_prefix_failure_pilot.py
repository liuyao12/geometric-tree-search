"""Pilot only: reused audited native catalogs, newly discovered failure labels."""
import gzip,hashlib,json,time
from pathlib import Path
from semantic_receptor_points import Model
from semantic_inventory_search import search
from prefix_failure_markings import learn,MarkedModel
from audit_prefix_failure_markings import teacher,check_learning

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DOC=ROOT/'docs/research/gcts-rl-renewal';OUT=ROOT/'.gcts-active/certified-prefix-markings-20261011'

def load(name):
    raw=(DOC/name).read_bytes();return json.loads(gzip.decompress(raw)),hashlib.sha256(raw).hexdigest()

def main():
    began=time.perf_counter();manifest,_=load('semantic-inventory-001.json.gz')
    training,training_pin=load(manifest['training']['name'])
    if training_pin!=manifest['training']['sha256']:raise ValueError('previous audited training changed')
    policy=json.loads((DOC/manifest['policy']['name']).read_text());jobs=[]
    for name in ('two-premise','pa-universal-equality'):
        spec=next(s for s in training['cases'] if s['id']==name)
        jobs.append((spec,training['catalog'][name],training['registries'][name],manifest['training']))
    old=next(o for o in manifest['observations'] if o['case']=='renamed-five' and o['mode']=='fixed' and o['repetition']==1)
    raw,source_pin=load(old['artifact']['name'])
    if source_pin!=old['artifact']['sha256']:raise ValueError('previous audited cold context changed')
    jobs.append((raw['case'],raw['compiled'],raw['inventory'],old['artifact']))
    summaries=[];OUT.mkdir(parents=True,exist_ok=True)
    for spec,compiled,inventory,source in jobs:
        parent=Model(spec,compiled,inventory)
        def check(model,probe):
            checked=teacher(model,probe)
            print(spec['id'],'prefix',probe['id'],probe['length'],probe['label'],
                  probe['search']['metrics'].get('attempts',0),flush=True)
            return checked
        learned=learn(parent,attempts=1000,seconds=.5,check=check)
        cert=check_learning(parent,learned)
        results=[]
        for mode in ('base','fixed','learned'):
            for marked in (False,True):
                base=Model(spec,compiled,inventory)
                model=MarkedModel(base,learned,cert) if marked else base
                out=search(model,mode,weights=policy['weights'] if mode=='learned' else None,
                           attempts=5000,seconds=30,seed=65000)
                results.append(dict(mode=mode,marked=marked,model=model.record(),search=out))
                print(spec['id'],mode,'marked' if marked else 'original',out['status'],
                      out['metrics'].get('attempts',0),flush=True)
        document=dict(version='prefix-failure-pilot-001',case=spec,compiled=compiled,inventory=inventory,
            reused_native_context=source,learning=learned,certificate=cert,results=results,
            scope='Exploratory preprocessing and reference point searches using Notebook 63 audited native contexts and frozen policy. No imported failure labels, final native certificate materialization, independent marked-tree audit or timing superiority claim.')
        path=OUT/(spec['id']+'-pilot.json.gz')
        path.write_bytes(gzip.compress(json.dumps(document,separators=(',',':')).encode(),mtime=0))
        summary=dict(case=spec['id'],prefixes=len(learned['probes']),counts=learned['counts'],
            learning_seconds=learned['seconds'],teacher_nodes=cert['nodes'],
            results=[dict(mode=r['mode'],marked=r['marked'],status=r['search']['status'],
                          attempts=r['search']['metrics'].get('attempts',0)) for r in results],
            artifact=path.name,bytes=path.stat().st_size)
        summaries.append(summary)
        (OUT/'pilot-summary.json').write_text(json.dumps(dict(status='in_progress',cases=summaries),indent=2)+'\n')
    (OUT/'pilot-summary.json').write_text(json.dumps(dict(status='passed_pilot',cases=summaries,
        seconds=time.perf_counter()-began),indent=2)+'\n')
    print('pilot complete',round(time.perf_counter()-began,3),flush=True)

if __name__=='__main__':main()
