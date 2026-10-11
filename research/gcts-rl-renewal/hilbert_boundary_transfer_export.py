"""Export the exact terminal bounded transfer result, including unknowns."""
import gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=json.loads((OUT/'plan.json').read_text());progress=json.loads((OUT/'progress.json').read_text());audit=json.loads((OUT/'audit.json').read_text())
    if audit['status']!='passed' or audit['production_outcome']!=progress['status'] or progress['status'] not in ['complete','unknown_preparation','rejected_theory']:raise ValueError('independent terminal gate required')
    fresh=load(OUT/'native.json.gz');inventories=load(ROOT/(plan['prior_prefix']+'inventories.json.gz'))
    prior={origin:load(ROOT/(prefix+'native.json.gz')) for origin,prefix in [('prior-family',plan['prior_prefix']),('prior-control',plan['prior_control_prefix'])]}
    ground_reader=json.loads((DOC/'hilbert_receptors_reader_001.json').read_text());ground_native=load(DOC/'hilbert_receptors_native.json.gz');ground_audit=json.loads((DOC/'hilbert_receptors_audit.json').read_text())
    source_ground=json.loads((DOC/'hilbert_promotion_family_v3_source_ground.json').read_text())
    if ground_audit['status']!='passed' or ground_audit['native_queries']!=len(ground_native) or ground_audit['native_micro_steps']!=sum(q['result']['micro_steps'] for q in ground_native) or ground_native[56]['request']!=source_ground['request']:raise ValueError('actual original searched source and complete prior audit')
    reporting=dict(scope='Post-trial historical cost accounting only, never read by search or native preparation. Original source-ground discovery is additional inherited work. Aggregate stage clocks overlap component clocks; no sum of disjoint cold costs is claimed. Source authoring/planning/declaration time has no experiment timer; production starts at the frozen-plan producer.',
        original_ground_source=dict(production_seconds=ground_reader['summary']['seconds'],native_production_seconds=sum(q['seconds'] for q in ground_native),audit_seconds=ground_audit['seconds'],native_queries=len(ground_native),native_micro_steps=ground_audit['native_micro_steps'],source_query=56,source_request_sha256=ground_native[56]['request_sha256'],positive_preparation_elapsed_seconds=ground_reader['summary']['cases'][0]['compile_seconds']+ground_reader['summary']['cases'][0]['admission_seconds']),
        original_quantified_closure=dict(status=ground_reader['closure']['native']['result']['status'],native_production_seconds=ground_reader['closure']['native']['seconds'],audit_seconds=ground_reader['closure']['audit']['seconds'],scope='Unchanged original heap unknown; ground receptor transfer does not resolve it.'),
        source_evidence=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in [DOC/'hilbert_receptors_reader_001.json',DOC/'hilbert_receptors_native.json.gz',DOC/'hilbert_receptors_audit.json',DOC/'hilbert_promotion_family_v3_source_ground.json']])
    (OUT/'historical-costs.json').write_text(json.dumps(reporting,indent=2)+'\n')
    data=dict(version='hilbert-boundary-transfer-001',plan=plan,progress=progress,audit=audit,inventories=inventories,historical_reporting=reporting,observations=[],native_preparation=[])
    for q in fresh:
        if q['purpose'] in ['transfer_theory_admission','transfer_tautology_guard']:data['native_preparation'].append({k:q.get(k) for k in ['id','purpose','group','basis_index','request_sha256','seconds','result','production_budget']})
    for item in plan['schedule']:
        if not (OUT/(item['tag']+'-final.json.gz')).exists():continue
        obs=load(OUT/(item['tag']+'-final.json.gz'));r=obs['search'];placed={tuple(p['key']):p for p in obs['model']['placements']};rows=[]
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
            q=(fresh if binding['origin']=='fresh' else prior[binding['origin']])[binding['query']];native=dict(binding=binding,request=q['request'],request_sha256=q['request_sha256'],result=q['result'],seconds=q['seconds'])
        a=next(x for x in audit['observations'] if x['tag']==item['tag'])
        data['observations'].append(dict(item=item,audit=a,rows=rows,metrics=r['metrics'],native=native,search_seconds=r['seconds'],
            feature_work=dict(vectors=sum(len(e['features']) for e in r['events']),expanded_mark_positions=sum(round(v[5]*1000) for e in r['events'] for it,v in zip(e['items'],e['features']) if it is not None)),
            costs={k:obs[k] for k in ['setup_seconds','worker_seconds','worker_wall_seconds','certification_wall_seconds','peak_rss_bytes']},
            pre_certification_checkpoint_sha256=obs['pre_certification_checkpoint_sha256'],root_restored=r['root_restored']))
    names=['plan.json','declared-catalog.json.gz','catalog.json.gz','inventories.json.gz','compiled.json.gz','prior-family-export.json','prior-control-export.json','progress.json','audit.json','native.json.gz','native-audit-progress.json','historical-costs.json']
    names += [i['tag']+suffix for i in plan['schedule'] for suffix in ['.json.gz','-final.json.gz']]
    artifacts=[]
    for name in names:
        path=OUT/name
        if not path.exists():continue
        dest=DOC/('hilbert_boundary_transfer_'+name.replace('-','_'));dest.write_bytes(path.read_bytes());artifacts.append(dict(path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=dest.stat().st_size))
    data['artifacts']=artifacts;obs=data['observations'];policies={}
    for language in ['level1','promoted']:
        for mode in ['base','fixed','learned']:
            xs=[x for x in obs if x['item']['language']==language and x['item']['mode']==mode]
            policies[language+'-'+mode]=dict(observations=len(xs),attempts=sum(x['audit']['attempts'] for x in xs),native_accepted=sum(x['audit']['certification']=='accepted' for x in xs),search_seconds=sum(x['search_seconds'] for x in xs),model_setup_seconds=sum(x['costs']['setup_seconds'] for x in xs),proposal_seconds=sum(x['metrics'].get('proposal_seconds',0) for x in xs),feature_vectors=sum(x['feature_work']['vectors'] for x in xs),expanded_mark_positions=sum(x['feature_work']['expanded_mark_positions'] for x in xs))
    summary=dict(status=progress['status'],planned_runs=24,observations=len(obs),native_accepted=sum(x['audit']['certification']=='accepted' for x in obs),point_proof_observations=sum(bool(x['rows']) for x in obs),
        search_unknowns=sum(x['audit']['status'].startswith('unknown') for x in obs),finite_exhaustions=sum(x['audit']['status']=='exhausted_finite_marked_region' for x in obs),
        native_whole_unknowns=sum(x['audit']['certification'].startswith('unknown') for x in obs),native_whole_rejections=sum(x['audit']['certification']=='rejected' for x in obs),
        exact_recipient_receptor_observations=sum(any(r['exact_recipient_receptor'] for r in x['audit']['derived_receptors']) for x in obs),policies=policies,
        native_preparation=dict(planned_queries=audit['complete_guard_queries'],actual_queries=len(data['native_preparation']),complete=progress['status']=='complete',outcome=progress.get('native_outcome'),unresolved_group=progress.get('unresolved_group'),unresolved_basis_index=progress.get('unresolved_basis_index')),
        incremental_costs=dict(production_seconds=progress['seconds'],initial_setup_seconds=progress['initial_setup_seconds'],native_setup_seconds=progress['native_setup_seconds'],preparation_seconds=progress.get('preparation_seconds',progress['seconds']),
            search_seconds=sum(x['search_seconds'] for x in obs),model_setup_seconds=sum(x['costs']['setup_seconds'] for x in obs),worker_wall_seconds=sum(x['costs']['worker_wall_seconds'] for x in obs),certification_wall_seconds=sum(x['costs']['certification_wall_seconds'] for x in obs),
            fresh_native_queries=len(fresh),fresh_native_production_seconds=sum(q['seconds'] for q in fresh),fresh_native_micro_steps=sum(q['result']['micro_steps'] for q in fresh),
            native_preparation_seconds=sum(q['seconds'] for q in fresh if q['purpose']!='transfer_discovered_whole'),native_whole_seconds=sum(q['seconds'] for q in fresh if q['purpose']=='transfer_discovered_whole'),
            independent_audit_seconds=audit['seconds'],independent_native_replay_seconds=audit['fresh_native_replay_seconds'],independent_prior_input_binding_seconds=audit['prior_input_binding_seconds'],independent_native_setup_seconds=audit['native_setup_seconds'],
            peak_worker_rss_bytes=max([x['costs']['peak_rss_bytes'] for x in obs] or [0])),
        inherited_costs=plan['prior_cost_provenance'],historical_reporting=reporting,prior_full_replay_binding=audit['prior_full_replay_binding'],native_budget_overshoots=progress['native_budget_overshoots'],native_budget_blocks=progress['native_budget_blocks'],native_observation_origins=audit['native_observation_origins'],
        fresh_native_whole_queries=sum(q['purpose']=='transfer_discovered_whole' for q in fresh),fresh_native_acceptance_reuse_observations=sum(bool(o['native'] and o['native']['binding'].get('independent_replayed_record_sha256')) for o in obs),prior_native_acceptance_reuse_observations=sum(bool(o['native'] and o['native']['binding']['origin']!='fresh') for o in obs),
        feature_scope='Expanded marking positions and vectors count every scored proposal, including repeated state-dependent work. Inclusive proposal elapsed time includes proposal generation, validation, feature construction and scoring; no feature-only timer is inferred from the unchanged engine.',
        audit=dict(complete_models=audit['complete_models'],nodes=audit.get('nodes',0),events=audit.get('events',0),hints=audit.get('hints',0),sha256=sha(OUT/'audit.json')),
        assessment='The two new hypothesis patterns require actual premise derivation and one reverses line receptor roles. They are ground incidence consequences, with four finite recipient boundaries and one deterministic seed. Inventory expansion is distinct from policy ordering; all comparisons within a language use equal complete inventories. Frozen learned weights transfer with no new training. Native preparation and certification unknowns remain unknown, separate from point search results. No renamed-case difficulty, statistical significance, general speed, primitive Wang compiler equivalence, full Hilbert geometry or quantified closure claim.')
    data['summary']=summary;reader=DOC/'hilbert_boundary_transfer_reader_001.json';reader.write_text(json.dumps(data,separators=(',',':'))+'\n');summarypath=DOC/'hilbert_boundary_transfer_summary.json';summarypath.write_text(json.dumps(summary,indent=2)+'\n')
    result=dict(status='verified_terminal_export',reader=dict(path=str(reader.relative_to(ROOT)),sha256=sha(reader),bytes=reader.stat().st_size),summary=dict(path=str(summarypath.relative_to(ROOT)),sha256=sha(summarypath),bytes=summarypath.stat().st_size),artifacts=artifacts)
    (OUT/'export.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=summary['status'],observations=len(obs),rows=sum(len(o['rows']) for o in obs),accepted=summary['native_accepted'],artifacts=len(artifacts))))
if __name__=='__main__':main()
