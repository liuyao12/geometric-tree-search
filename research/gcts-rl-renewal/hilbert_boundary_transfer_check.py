"""Check terminal reader bindings against every independently audited raw row."""
import copy,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011'
def need(v,msg):
    if not v:raise ValueError(msg)
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    data=json.loads((DOC/'hilbert_boundary_transfer_reader_001.json').read_text());plan=json.loads((OUT/'plan.json').read_text());audit=json.loads((OUT/'audit.json').read_text());progress=json.loads((OUT/'progress.json').read_text());fresh=load(OUT/'native.json.gz')
    inv=load(ROOT/(plan['prior_prefix']+'inventories.json.gz'));prior={origin:load(ROOT/(prefix+'native.json.gz')) for origin,prefix in [('prior-family',plan['prior_prefix']),('prior-control',plan['prior_control_prefix'])]};expected={};row_count=0
    for item in plan['schedule']:
        path=OUT/(item['tag']+'-final.json.gz')
        if not path.exists():continue
        obs=load(path);r=obs['search'];model=obs['model'];placements={tuple(p['key']):p for p in model['placements']};rows=[];totals={};marks={}
        for key in r['placements']:
            p=placements[tuple(key)]
            for point,value in p['occupancy']:totals[tuple(point)]=totals.get(tuple(point),0)+value
            for point,value in p['marks']:
                point=tuple(point);need(point not in marks or marks[point]==value,'actual selected marking agreement');marks[point]=value
        if r['proof'] is not None:need(set(totals)=={tuple(p) for p in model['roots']} and all(v==12 for v in totals.values()),'exact capacity at every required root')
        for j,c in enumerate(r['proof'] or []):
            tiles=[]
            for key in sorted((k for k in r['placements'] if k[0]==j),key=lambda k:k[1]):
                p=placements[tuple(key)];need(len(p['occupancy'])==1 and p['occupancy'][0]==[[4*j,key[1]],12],'actual normalized point tile occupancy');words=[]
                for point,value in p['marks']:
                    if point[0]%4==2 and point[1] in [0,1]:
                        kind=['formula','command'][point[1]];word=model['catalog'][kind][value]
                        need(word['id']==value and bytes.fromhex(word['word_hex'])==json.dumps(word['value'],sort_keys=True,separators=(',',':')).encode(),'injective canonical dictionary word')
                        words.append(dict(point=point,value=value,kind=kind,word=word['value']))
                tile=dict(key=p['key'],role=['C','G','I1','I2'][key[1]],occupancy=p['occupancy'],marks=p['marks'],kind=p['kind'],words=words)
                if 'source' in p:tile['source']=p['source']
                tiles.append(tile)
            need(len(tiles)==4 and [t['role'] for t in tiles]==['C','G','I1','I2'],'complete four-tile row')
            command=copy.deepcopy(next(w['word'] for w in tiles[0]['words'] if w['kind']=='command'))
            if command['rule']=='block':
                definition=next(d['definition'] for d in inv[item['language']]['definitions'] if d['name']==command['name']);command['inputs']=[tiles[2+k]['source'] for k in range(len(definition['premises']))]
            need(command==c and any(w['kind']=='formula' and w['word']==c['formula'] for w in tiles[0]['words']),'full line formula/command decoded from markings and sources')
            rows.append(dict(index=j+1,command=c,tiles=tiles))
        binding=obs['native_binding'];native=None
        if binding is not None:
            q=(fresh if binding['origin']=='fresh' else prior[binding['origin']])[binding['query']];native=dict(binding=binding,request=q['request'],request_sha256=q['request_sha256'],result=q['result'],seconds=q['seconds'])
            need(q['result']['status']==obs['certification'],'native unknown or accepted is represented exactly')
        feature=dict(vectors=sum(len(e['features']) for e in r['events']),expanded_mark_positions=sum(round(v[5]*1000) for e in r['events'] for it,v in zip(e['items'],e['features']) if it is not None))
        expected[item['tag']]=dict(item=item,audit=next(a for a in audit['observations'] if a['tag']==item['tag']),rows=rows,native=native,metrics=r['metrics'],search_seconds=r['seconds'],feature_work=feature,costs={k:obs[k] for k in ['setup_seconds','worker_seconds','worker_wall_seconds','certification_wall_seconds','peak_rss_bytes']},pre_certification_checkpoint_sha256=obs['pre_certification_checkpoint_sha256'],root_restored=r['root_restored']);row_count+=len(rows)
    preparation=[{k:q.get(k) for k in ['id','purpose','group','basis_index','request_sha256','seconds','result','production_budget']} for q in fresh if q['purpose'] in ['transfer_theory_admission','transfer_tautology_guard']]
    def validate(d):
        need(d['version']=='hilbert-boundary-transfer-001' and d['plan']==plan and plan['completed_observations_at_declaration']==0,'exact pre-search freeze')
        need(d['audit']==audit and audit['status']=='passed' and d['progress']==progress and audit['production_outcome']==progress['status'],'actual terminal independent gate')
        need(d['inventories']==inv and len(inv['level1']['definitions'])==28 and len(inv['promoted']['definitions'])==76,'complete unchanged library')
        need([o['item']['tag'] for o in d['observations']]==list(expected) and all(o==expected[o['item']['tag']] for o in d['observations']),'all raw tile rows/translations/commands/whole outcomes/costs')
        need(d['native_preparation']==preparation,'every actual native guard, outcome and overshoot')
        if progress['status']=='complete':need(len(d['observations'])==24,'all 24 complete observations')
        else:need(not d['observations'],'incomplete guard preparation yields no search result')
        for a in d['artifacts']:
            p=ROOT/a['path'];need(sha(p)==a['sha256'] and p.stat().st_size==a['bytes'],'byte-exact public evidence')
        names={a['path'].split('/')[-1] for a in d['artifacts']}
        for item in plan['schedule']:
            if item['tag'] in expected:need(all('hilbert_boundary_transfer_'+item['tag'].replace('-','_')+suffix in names for suffix in ['.json.gz','_final.json.gz']),'both pre-certification checkpoint and final artifact')
        s=d['summary'];need(s['status']==progress['status'] and s['planned_runs']==24 and s['observations']==len(expected),'terminal scope and run count')
        need(s['native_accepted']==sum(o['audit']['certification']=='accepted' for o in d['observations']) and s['point_proof_observations']==sum(bool(o['rows']) for o in d['observations']),'point proof and actual native acceptance kept separate')
        need(s['search_unknowns']==sum(o['audit']['status'].startswith('unknown') for o in d['observations']) and s['native_whole_unknowns']==sum(o['audit']['certification'].startswith('unknown') for o in d['observations']) and s['native_whole_rejections']==sum(o['audit']['certification']=='rejected' for o in d['observations']),'all unknown/rejected outcomes disclosed')
        need(s['exact_recipient_receptor_observations']==sum(any(r['exact_recipient_receptor'] for r in o['audit']['derived_receptors']) for o in d['observations']),'actual derived receptor count')
        need(s['native_budget_overshoots']==progress['native_budget_overshoots'] and s['native_budget_blocks']==progress['native_budget_blocks'] and s['inherited_costs']==plan['prior_cost_provenance'] and s['prior_full_replay_binding']==audit['prior_full_replay_binding'],'full native cost ceiling and prior costs/replay preserved')
        historical=json.loads((OUT/'historical-costs.json').read_text());need(s['historical_reporting']==d['historical_reporting']==historical,'actual additional historical source costs')
        for e in historical['source_evidence']:need(sha(ROOT/e['path'])==e['sha256'] and (ROOT/e['path']).stat().st_size==e['bytes'],'actual prior source-ground cost evidence')
        gn=load(DOC/'hilbert_receptors_native.json.gz');ga=json.loads((DOC/'hilbert_receptors_audit.json').read_text());gr=json.loads((DOC/'hilbert_receptors_reader_001.json').read_text());gc=historical['original_ground_source'];need(gc['production_seconds']==gr['summary']['seconds'] and gc['native_production_seconds']==sum(q['seconds'] for q in gn) and gc['audit_seconds']==ga['seconds'] and gc['native_queries']==ga['native_queries']==len(gn) and gc['native_micro_steps']==ga['native_micro_steps']==sum(q['result']['micro_steps'] for q in gn) and gc['source_request_sha256']==gn[56]['request_sha256'] and gn[56]['request']==json.loads((DOC/'hilbert_promotion_family_v3_source_ground.json').read_text())['request'],'original source-ground entire bill and actual searched input')
        need(s['fresh_native_whole_queries']==sum(q['purpose']=='transfer_discovered_whole' for q in fresh) and s['fresh_native_acceptance_reuse_observations']==sum(bool(o['native'] and o['native']['binding'].get('independent_replayed_record_sha256')) for o in d['observations']) and s['prior_native_acceptance_reuse_observations']==sum(bool(o['native'] and o['native']['binding']['origin']!='fresh') for o in d['observations']),'actual fresh whole count and exact acceptance reuse')
        n=s['native_preparation'];need(n['planned_queries']==audit['complete_guard_queries']==61 and n['actual_queries']==len(preparation) and n['complete']==(progress['status']=='complete') and n['outcome']==progress.get('native_outcome'),'complete guard scope and terminal unknown')
        c=s['incremental_costs'];need(c['fresh_native_queries']==len(fresh) and c['fresh_native_micro_steps']==sum(q['result']['micro_steps'] for q in fresh) and c['fresh_native_production_seconds']==sum(q['seconds'] for q in fresh) and c['independent_audit_seconds']==audit['seconds'] and c['independent_native_replay_seconds']==audit['fresh_native_replay_seconds'] and c['production_seconds']==progress['seconds'],'fresh full computation/replay bill')
        need(c['search_seconds']==sum(o['search_seconds'] for o in d['observations']) and c['model_setup_seconds']==sum(o['costs']['setup_seconds'] for o in d['observations']),'all search/setup cost')
        for k,v in s['policies'].items():
            lang,mode=k.split('-');xs=[o for o in d['observations'] if o['item']['language']==lang and o['item']['mode']==mode]
            need(v==dict(observations=len(xs),attempts=sum(o['audit']['attempts'] for o in xs),native_accepted=sum(o['audit']['certification']=='accepted' for o in xs),search_seconds=sum(o['search_seconds'] for o in xs),model_setup_seconds=sum(o['costs']['setup_seconds'] for o in xs),proposal_seconds=sum(o['metrics'].get('proposal_seconds',0) for o in xs),feature_vectors=sum(o['feature_work']['vectors'] for o in xs),expanded_mark_positions=sum(o['feature_work']['expanded_mark_positions'] for o in xs)),'complete equal-inventory policy aggregation')
        need(s['audit']['sha256']==sha(OUT/'audit.json') and s['audit']['complete_models']==audit['complete_models'],'actual audit receipt')
        return True
    validate(data);mutations=[]
    def test(label,change):
        d=copy.deepcopy(data);change(d)
        try:validate(d)
        except (ValueError,KeyError,IndexError):mutations.append(dict(label=label,status='rejected'));return
        raise ValueError('corruption accepted '+label)
    test('changed planned guard limit',lambda d:d['plan'].__setitem__('guard_native_steps',1))
    test('changed hypothesis dependencies',lambda d:d['plan']['cases'][0]['theory']['axioms'].pop('readiness'))
    test('omitted higher receptor',lambda d:d['inventories']['promoted']['definitions'].pop())
    test('hidden preparation outcome',lambda d:d['summary']['native_preparation'].__setitem__('outcome','invented'))
    test('hidden native bill',lambda d:d['summary']['incremental_costs'].__setitem__('fresh_native_micro_steps',0))
    test('hidden inherited training',lambda d:d['summary']['inherited_costs'].__setitem__('inherited_policy_training_seconds',0))
    test('hidden source-ground discovery',lambda d:d['historical_reporting']['original_ground_source'].__setitem__('production_seconds',0))
    test('hidden exact new acceptance reuse',lambda d:d['summary'].__setitem__('fresh_native_acceptance_reuse_observations',-1))
    test('counterfeit prior replay',lambda d:d['audit']['prior_full_replay_binding'].__setitem__('family_audit_sha256','0'*64))
    test('false acceptance count',lambda d:d['summary'].__setitem__('native_accepted',999))
    test('missing guard outcome',lambda d:d['native_preparation'].pop())
    test('hidden feature work',lambda d:d['summary']['policies']['promoted-learned'].__setitem__('feature_vectors',-1))
    if expected:
        test('missing observation',lambda d:d['observations'].pop())
        test('missing checkpoint artifact',lambda d:d['artifacts'].__setitem__(slice(None),[a for a in d['artifacts'] if not a['path'].endswith('_expanded.json.gz')]))
    proofindex=next((i for i,o in enumerate(data['observations']) if o['rows']),None)
    if proofindex is not None:
        test('wrong marking',lambda d:d['observations'][proofindex]['rows'][0]['tiles'][0]['marks'][0].__setitem__(1,-99))
        test('wrong occupancy',lambda d:d['observations'][proofindex]['rows'][0]['tiles'][0]['occupancy'][0].__setitem__(1,11))
        test('wrong row formula',lambda d:d['observations'][proofindex]['rows'][0]['tiles'][0]['words'][0].__setitem__('word',['bot']))
        test('missing proof row',lambda d:d['observations'][proofindex]['rows'].pop())
    nativeindex=next((i for i,o in enumerate(data['observations']) if o['native']),None)
    if nativeindex is not None:
        test('counterfeit native whole proof',lambda d:d['observations'][nativeindex]['native']['request'].__setitem__('proof',[]))
        test('invented native origin',lambda d:d['observations'][nativeindex]['native']['binding'].__setitem__('origin','invented'))
    result=dict(status='passed',terminal_outcome=progress['status'],observations=len(expected),proof_rows=row_count,actual_tiles=4*row_count,mutations=mutations,reader_sha256=sha(DOC/'hilbert_boundary_transfer_reader_001.json'),plan_sha256=sha(OUT/'plan.json'),audit_sha256=sha(OUT/'audit.json'))
    (OUT/'reader-checks.json').write_text(json.dumps(result,indent=2)+'\n');(DOC/'hilbert_boundary_transfer_reader_checks.json').write_bytes((OUT/'reader-checks.json').read_bytes());print(json.dumps(result))
if __name__=='__main__':main()
