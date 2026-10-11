"""Publishable immutable export of the separately audited weighting control."""
import gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-expanded-control-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=json.loads((OUT/'plan.json').read_text());progress=json.loads((OUT/'progress.json').read_text());audit=json.loads((OUT/'audit.json').read_text())
    if progress['status']!='complete' or audit['status']!='passed' or audit['production_outcome']!='complete' or len(audit['observations'])!=16:raise ValueError('complete independent gate required')
    prefix=ROOT/plan['prior_prefix'];prior=lambda n:Path(str(prefix)+n);oldnative=load(prior('native.json.gz'));fresh=load(OUT/'native.json.gz');inventory=load(prior('inventories.json.gz'))
    data=dict(version='hilbert-expanded-control-001',plan=plan,progress=progress,audit=audit,inventories=inventory,observations=[])
    for item in plan['schedule']:
        obs=load(OUT/(item['tag']+'-final.json.gz'));paired=load(ROOT/item['paired_final']);r=obs['search'];placed={tuple(p['key']):p for p in obs['model']['placements']};rows=[]
        for j,c in enumerate(r['proof'] or []):
            tiles=[]
            for key in sorted([k for k in r['placements'] if k[0]==j],key=lambda k:k[1]):
                p=placed[tuple(key)];words=[]
                for point,value in p['marks']:
                    if point[0]%4==2 and point[1] in [0,1]:
                        kind='formula' if point[1]==0 else 'command';words.append(dict(point=point,value=value,kind=kind,word=obs['model']['catalog'][kind][value]['value']))
                tile=dict(key=p['key'],role=['C','G','I1','I2'][key[1]],occupancy=p['occupancy'],marks=p['marks'],kind=p['kind'],words=words)
                if 'source' in p:tile['source']=p['source']
                tiles.append(tile)
            rows.append(dict(index=j+1,command=c,tiles=tiles))
        binding=obs['native_binding'];native=None
        if binding is not None:
            q=(oldnative if binding['origin']=='prior' else fresh)[binding['query']];native=dict(binding=binding,request=q['request'],request_sha256=q['request_sha256'],result=q['result'],seconds=q['seconds'])
        a=next(x for x in audit['observations'] if x['tag']==item['tag'])
        data['observations'].append(dict(item=item,audit=a,rows=rows,metrics=r['metrics'],paired_metrics=paired['search']['metrics'],native=native,
            feature_work=dict(fixed_vectors=sum(len(e['features']) for e in r['events']),paired_vectors=sum(len(e['features']) for e in paired['search']['events']),
                fixed_expanded_mark_positions=sum(round(v[5]*1000) for e in r['events'] for item,v in zip(e['items'],e['features']) if item is not None),
                paired_expanded_mark_positions=sum(round(v[5]*1000) for e in paired['search']['events'] for item,v in zip(e['items'],e['features']) if item is not None)),
            fixed_costs={k:obs[k] for k in ['setup_seconds','worker_seconds','worker_wall_seconds','certification_wall_seconds','peak_rss_bytes']},
            paired_costs={k:paired[k] for k in ['setup_seconds','worker_seconds','worker_wall_seconds','peak_rss_bytes']},
            pre_certification_checkpoint_sha256=obs['pre_certification_checkpoint_sha256'],root_restored=r['root_restored']))
    names=['plan.json','prior-export.json','progress.json','audit.json','native.json.gz','native-audit-progress.json']
    names+=[i['tag']+suffix for i in plan['schedule'] for suffix in ['.json.gz','-final.json.gz']]
    artifacts=[]
    for name in names:
        path=OUT/name
        if not path.exists():continue
        dest=DOC/('hilbert_expanded_control_'+name.replace('-','_'));dest.write_bytes(path.read_bytes())
        artifacts.append(dict(path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=dest.stat().st_size))
    data['artifacts']=artifacts
    pairs=data['observations'];directions={'learned_fewer':0,'equal':0,'learned_more':0}
    for p in pairs:
        d=p['audit']['learned_minus_fixed_attempts'];directions['learned_fewer' if d<0 else 'learned_more' if d>0 else 'equal']+=1
    summary=dict(status='complete_independently_audited',observations=16,deterministic_pairs=8,directions=directions,
        proof_observations=sum(p['native'] is not None and p['native']['result']['status']=='accepted' for p in pairs),
        finite_exhaustions=sum(p['audit']['status']=='exhausted_finite_marked_region' for p in pairs),
        search_unknowns=sum(p['audit']['status']=='unknown_search_budget' for p in pairs),
        native_whole_unknowns=sum(p['native'] is not None and p['native']['result']['status'].startswith('unknown') for p in pairs),
        fixed_attempts=sum(p['audit']['fixed_attempts'] for p in pairs),learned_attempts=sum(p['audit']['learned_attempts'] for p in pairs),
        incremental_costs=dict(production_seconds=progress['seconds'],preparation_seconds=progress['preparation_seconds'],native_setup_seconds=progress['native_setup_seconds'],
            fixed_search_seconds=sum(p['audit']['fixed_search_seconds'] for p in pairs),fixed_model_setup_seconds=sum(p['fixed_costs']['setup_seconds'] for p in pairs),
            fixed_worker_wall_seconds=sum(p['fixed_costs']['worker_wall_seconds'] for p in pairs),certification_wall_seconds=sum(p['fixed_costs']['certification_wall_seconds'] for p in pairs),
            fresh_native_production_seconds=sum(q['seconds'] for q in fresh),fresh_native_micro_steps=sum(q['result']['micro_steps'] for q in fresh),fresh_native_queries=len(fresh),
            independent_audit_seconds=audit['seconds'],independent_fresh_native_replay_seconds=audit['fresh_native_replay_seconds'],independent_prior_input_binding_seconds=audit['prior_input_binding_seconds'],
            peak_worker_rss_bytes=max(p['fixed_costs']['peak_rss_bytes'] for p in pairs)),
        frozen_paired_costs=dict(search_seconds=sum(p['audit']['learned_search_seconds'] for p in pairs),model_setup_seconds=sum(p['paired_costs']['setup_seconds'] for p in pairs),worker_wall_seconds=sum(p['paired_costs']['worker_wall_seconds'] for p in pairs)),
        historical_shared_costs=progress['prior_shared_costs'],native_prior_reuse_observations=audit['native_reused_prior_observations'],
        native_new_reuse_observations=audit['native_fresh_origin_observations']-len(fresh),
        feature_cost_accounting=dict(fixed_proposal_seconds=sum(p['metrics'].get('proposal_seconds',0) for p in pairs),paired_learned_proposal_seconds=sum(p['paired_metrics'].get('proposal_seconds',0) for p in pairs),
            fixed_feature_vectors=sum(p['feature_work']['fixed_vectors'] for p in pairs),paired_learned_feature_vectors=sum(p['feature_work']['paired_vectors'] for p in pairs),
            fixed_expanded_mark_positions=sum(p['feature_work']['fixed_expanded_mark_positions'] for p in pairs),paired_learned_expanded_mark_positions=sum(p['feature_work']['paired_expanded_mark_positions'] for p in pairs),
            scope='Expanded-word feature work is included in search and proposal elapsed times. The unchanged engine has one inclusive proposal timer covering generation, validation, feature construction and scoring; no separate feature-only time is inferred. Position and vector counts cover every scored proposal, including repeated work at different search states.'),
        audit=dict(complete_models=audit['complete_models'],nodes=audit['nodes'],events=audit['events'],hints=audit['hints'],sha256=sha(OUT/'audit.json')),
        assessment='This isolates fixed versus frozen learned ordering weights on exactly equal word-expanded point models. The four recipients are two hypothesis configurations at two finite boundary lengths, not four independent mathematical theorems. Any observed attempt difference is specific to these deterministic recipients; two same-seed timing repetitions are not independent samples. No new RL training, universal superiority, or total-cost speed claim. Prior cold preparation and full replay costs remain visible; new certificate verification costs and overlapping audit wait are charged separately.')
    data['summary']=summary
    reader=DOC/'hilbert_expanded_control_reader_001.json';reader.write_text(json.dumps(data,separators=(',',':'))+'\n')
    summarypath=DOC/'hilbert_expanded_control_summary.json';summarypath.write_text(json.dumps(summary,indent=2)+'\n')
    result=dict(status='verified_export',reader=dict(path=str(reader.relative_to(ROOT)),sha256=sha(reader),bytes=reader.stat().st_size),summary=dict(path=str(summarypath.relative_to(ROOT)),sha256=sha(summarypath),bytes=summarypath.stat().st_size),artifacts=artifacts)
    (OUT/'export.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(observations=16,rows=sum(len(o['rows']) for o in pairs),directions=directions,artifacts=len(artifacts))))
if __name__=='__main__':main()
