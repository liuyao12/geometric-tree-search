"""Paired construction pilot: the same fresh labels reach all formula writers."""
import gzip,hashlib,json,subprocess,time
from pathlib import Path
from semantic_receptor_points import Model
from semantic_inventory_search import search
from prefix_failure_markings import MarkedModel
from audit_prefix_failure_markings import check_learning,check_overlay,extended_tree
from semantic_inventory_worker import oracle_for,verify
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/certified-prefix-markings-20261011';TMP=Path('/private/tmp/gcts-certified-prefix-pilot-20261011')

def main():
    began=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True)
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP),executable=str(TMP/'oracle')))
    summaries=[]
    policy=json.loads((ROOT/'docs/research/gcts-rl-renewal/semantic-inventory-policy-001.json').read_text())
    try:
        for name in ('two-premise','pa-universal-equality','renamed-five'):
            path=OUT/'pilot-output-only'/(name+'-pilot.json.gz');raw_bytes=path.read_bytes()
            data=json.loads(gzip.decompress(raw_bytes));spec=data['case'];compiled=data['compiled'];inventory=data['inventory']
            learning=data['learning'];old_results=[dict(mode=r['mode'],marked=r['marked'],status=r['search']['status'],
                    attempts=r['search']['metrics'].get('attempts',0)) for r in data['results']]
            del data
            parent=Model(spec,compiled,inventory);cert=check_learning(parent,learning)
            records_start=len(oracle.records);results=[]
            for mode in ('base','fixed','learned'):
                base=Model(spec,compiled,inventory);model=MarkedModel(base,learning,cert);record=model.record()
                overlay=check_overlay(base,learning,cert,record)
                weights=policy['weights'] if mode=='learned' else None
                out=search(model,mode,weights=weights,attempts=5000,seconds=30,seed=65000)
                tree=extended_tree(spec,record,out,inventory,weights,record['initial_marks'])
                native=None
                if out['proof'] is not None:
                    q=verify(oracle,spec,out['proof'],inventory,'consumer_failure_marking_pilot')
                    if q['result']['status']!='accepted':raise ValueError('final pilot proof native check unfinished')
                    native=q['id'];fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free)
                results.append(dict(mode=mode,model=record,overlay_check=overlay,search=out,
                                    tree_check=tree,native_query=native))
                print(name,mode,out['status'],out['metrics'].get('attempts',0),
                      'affected',overlay['affected_candidates'],'native',native,flush=True)
            document=dict(version='prefix-consumer-pilot-001',case=spec,compiled=compiled,inventory=inventory,
                original_pilot_sha256=hashlib.sha256(raw_bytes).hexdigest(),learning=learning,certificate=cert,
                output_only_results=old_results,results=results,records=oracle.records[records_start:],
                scope='Paired propagation pilot using the same freshly learned current-turn prefix labels, independently replayed before activation. Native whole checks for successful roots; fresh native compiler but reused Notebook 63 admitted catalogs/lemmas and frozen policy. Not a cold benchmark or completed formal comparison.')
            target=OUT/(name+'-consumer-pilot.json.gz');target.write_bytes(gzip.compress(json.dumps(document,separators=(',',':')).encode(),mtime=0))
            summaries.append(dict(case=name,counts=learning['counts'],results=[dict(mode=r['mode'],
                status=r['search']['status'],attempts=r['search']['metrics'].get('attempts',0),
                affected_candidates=r['overlay_check']['affected_candidates'],native_query=r['native_query']) for r in results],
                artifact=target.name,bytes=target.stat().st_size))
            (OUT/'consumer-pilot-summary.json').write_text(json.dumps(dict(status='in_progress',cases=summaries),indent=2)+'\n')
        (OUT/'consumer-pilot-summary.json').write_text(json.dumps(dict(status='passed_pilot',cases=summaries,
            queries=len(oracle.records),seconds=time.perf_counter()-began),indent=2)+'\n')
        print('consumer pilot complete',round(time.perf_counter()-began,3),flush=True)
    finally:oracle.close()

if __name__=='__main__':main()
