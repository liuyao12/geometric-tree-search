"""Bind the HTML reader to independently audited raw proof tiles and costs."""
import copy,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/hilbert-expanded-control-20261011'
def need(v,msg):
    if not v:raise ValueError(msg)
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    data=json.loads((DOC/'hilbert_expanded_control_reader_001.json').read_text());plan=json.loads((OUT/'plan.json').read_text());audit=json.loads((OUT/'audit.json').read_text());progress=json.loads((OUT/'progress.json').read_text())
    prior=lambda n:ROOT/(plan['prior_prefix']+n);prior_native=load(prior('native.json.gz'));fresh=load(OUT/'native.json.gz');inv=load(prior('inventories.json.gz'));expected={};row_count=0
    for item in plan['schedule']:
        obs=load(OUT/(item['tag']+'-final.json.gz'));paired=load(ROOT/item['paired_final']);r=obs['search'];model=obs['model'];placements={tuple(p['key']):p for p in model['placements']};rows=[];totals={};marks={}
        for key in r['placements']:
            p=placements[tuple(key)]
            for point,value in p['occupancy']:totals[tuple(point)]=totals.get(tuple(point),0)+value
            for point,value in p['marks']:
                point=tuple(point);need(point not in marks or marks[point]==value,'actual selected marking agreement');marks[point]=value
        if r['proof'] is not None:need(set(totals)=={tuple(p) for p in model['roots']} and all(v==12 for v in totals.values()),'exact capacity and complete required point set')
        for j,c in enumerate(r['proof'] or []):
            tiles=[]
            for key in sorted((k for k in r['placements'] if k[0]==j),key=lambda k:k[1]):
                p=placements[tuple(key)];need(len(p['occupancy'])==1 and p['occupancy'][0]==[[4*j,key[1]],12],'normalized one-point tile occupancy')
                words=[]
                for point,value in p['marks']:
                    if point[0]%4==2 and point[1] in [0,1]:
                        kind=['formula','command'][point[1]];word=model['catalog'][kind][value]
                        need(word['id']==value and bytes.fromhex(word['word_hex'])==json.dumps(word['value'],sort_keys=True,separators=(',',':')).encode(),'exact canonical scalar dictionary')
                        words.append(dict(point=point,value=value,kind=kind,word=word['value']))
                tile=dict(key=p['key'],role=['C','G','I1','I2'][key[1]],occupancy=p['occupancy'],marks=p['marks'],kind=p['kind'],words=words)
                if 'source' in p:tile['source']=p['source']
                tiles.append(tile)
            need(len(tiles)==4 and [t['role'] for t in tiles]==['C','G','I1','I2'],'entire actual tile row')
            decoded=copy.deepcopy(next(w['word'] for w in tiles[0]['words'] if w['kind']=='command'))
            if decoded['rule']=='block':
                definition=next(d['definition'] for d in inv[item['language']]['definitions'] if d['name']==decoded['name'])
                decoded['inputs']=[tiles[2+r]['source'] for r in range(len(definition['premises']))]
            need(any(w['kind']=='formula' and w['word']==c['formula'] for w in tiles[0]['words']) and decoded==c,'formula and entire command decode from command tile plus actual source receptors')
            rows.append(dict(index=j+1,command=c,tiles=tiles))
        binding=obs['native_binding'];native=None
        if binding is not None:
            q=(prior_native if binding['origin']=='prior' else fresh)[binding['query']];native=dict(binding=binding,request=q['request'],request_sha256=q['request_sha256'],result=q['result'],seconds=q['seconds'])
            need(q['result']['status']=='accepted','exact whole acceptance')
        feature=dict(fixed_vectors=sum(len(e['features']) for e in r['events']),paired_vectors=sum(len(e['features']) for e in paired['search']['events']),
            fixed_expanded_mark_positions=sum(round(v[5]*1000) for e in r['events'] for item,v in zip(e['items'],e['features']) if item is not None),
            paired_expanded_mark_positions=sum(round(v[5]*1000) for e in paired['search']['events'] for item,v in zip(e['items'],e['features']) if item is not None))
        expected[item['tag']]=dict(item=item,audit=next(a for a in audit['observations'] if a['tag']==item['tag']),rows=rows,native=native,feature_work=feature,metrics=r['metrics'],paired_metrics=paired['search']['metrics'],
            fixed_costs={k:obs[k] for k in ['setup_seconds','worker_seconds','worker_wall_seconds','certification_wall_seconds','peak_rss_bytes']},paired_costs={k:paired[k] for k in ['setup_seconds','worker_seconds','worker_wall_seconds','peak_rss_bytes']},
            pre_certification_checkpoint_sha256=obs['pre_certification_checkpoint_sha256'],root_restored=True)
        row_count+=len(rows)
    def validate(d):
        need(d['version']=='hilbert-expanded-control-001' and d['plan']==plan and plan['completed_observations_at_declaration']==0,'exact pre-search freeze, feature units and weights')
        need(d['audit']==audit and audit['status']=='passed' and audit['production_outcome']=='complete' and d['progress']==progress,'complete independent gate and actual native costs')
        need(d['inventories']==inv and len(inv['level1']['definitions'])==28 and len(inv['promoted']['definitions'])==76,'all complete interfaces retained')
        need(len(d['observations'])==16 and [o['item']['tag'] for o in d['observations']]==[x['tag'] for x in plan['schedule']],'all 16 predeclared observations')
        for o in d['observations']:need(o==expected[o['item']['tag']],'every actual raw proof row, tile, word, decoded formula, whole request and measured feature cost')
        artifact_names={a['path'].split('/')[-1] for a in d['artifacts']}
        need(all('hilbert_expanded_control_'+i['tag'].replace('-','_')+s in artifact_names for i in plan['schedule'] for s in ['.json.gz','_final.json.gz']),'all pre-certification checkpoints and final observations exported')
        for a in d['artifacts']:
            p=ROOT/a['path'];need(sha(p)==a['sha256'] and p.stat().st_size==a['bytes'],'exact public artifact SHA and bytes')
        s=d['summary'];need(s['observations']==16 and s['deterministic_pairs']==8 and s['directions']=={'learned_fewer':8,'equal':8,'learned_more':0} and s['proof_observations']==12 and s['finite_exhaustions']==4 and s['search_unknowns']==0 and s['native_whole_unknowns']==0,'actual pair aggregation')
        need(s['fixed_attempts']==sum(x['audit']['fixed_attempts'] for x in d['observations']) and s['learned_attempts']==sum(x['audit']['learned_attempts'] for x in d['observations']),'all paired attempt work charged')
        need(s['historical_shared_costs']==progress['prior_shared_costs'] and s['native_prior_reuse_observations']==8 and s['native_new_reuse_observations']==2,'prior historical bill and cached native origins visible')
        c=s['incremental_costs'];need(c['production_seconds']==progress['seconds'] and c['preparation_seconds']==progress['preparation_seconds'] and c['independent_audit_seconds']==audit['seconds'] and c['independent_fresh_native_replay_seconds']==audit['fresh_native_replay_seconds'] and c['fresh_native_queries']==2 and c['fresh_native_micro_steps']==sum(q['result']['micro_steps'] for q in fresh) and c['fresh_native_production_seconds']==sum(q['seconds'] for q in fresh),'actual preparation and fresh native/replay costs')
        f=s['feature_cost_accounting'];need(f['fixed_proposal_seconds']==sum(o['metrics'].get('proposal_seconds',0) for o in d['observations']) and f['paired_learned_proposal_seconds']==sum(o['paired_metrics'].get('proposal_seconds',0) for o in d['observations']) and f['fixed_feature_vectors']==sum(o['feature_work']['fixed_vectors'] for o in d['observations']) and f['fixed_expanded_mark_positions']==sum(o['feature_work']['fixed_expanded_mark_positions'] for o in d['observations']),'inclusive feature timer and all counted feature work')
        need(s['audit']['sha256']==sha(OUT/'audit.json'),'actual independent receipt pin')
        return True
    validate(data)
    proofindex=next(i for i,o in enumerate(data['observations']) if o['rows']);mutations=[]
    def test(label,change):
        d=copy.deepcopy(data);change(d)
        try:validate(d)
        except (ValueError,KeyError,IndexError):mutations.append(dict(label=label,status='rejected'));return
        raise ValueError('corruption accepted '+label)
    test('missing observation',lambda d:d['observations'].pop())
    test('wrong fixed weights',lambda d:d['plan']['fixed_weights'].__setitem__(0,0))
    test('wrong feature units',lambda d:d['plan'].__setitem__('feature_semantics','physical'))
    test('omitted promoted receptor',lambda d:d['inventories']['promoted']['definitions'].pop())
    test('missing pre-certification artifact',lambda d:d['artifacts'].__setitem__(slice(None),[a for a in d['artifacts'] if not a['path'].endswith('_r1.json.gz')]))
    test('wrong native origin',lambda d:d['observations'][proofindex]['native']['binding'].__setitem__('origin','invented'))
    test('wrong actual whole certificate',lambda d:d['observations'][proofindex]['native']['request'].__setitem__('proof',[]))
    test('wrong marking assignment',lambda d:d['observations'][proofindex]['rows'][0]['tiles'][0]['marks'][0].__setitem__(1,-99))
    test('wrong occupancy',lambda d:d['observations'][proofindex]['rows'][0]['tiles'][0]['occupancy'][0].__setitem__(1,11))
    test('wrong formula translation',lambda d:d['observations'][proofindex]['rows'][0]['tiles'][0]['words'][0].__setitem__('word',['bot']))
    test('missing actual proof row',lambda d:d['observations'][proofindex]['rows'].pop())
    test('hidden historical preparation',lambda d:d['summary']['historical_shared_costs'].__setitem__('production_seconds',0))
    test('hidden fresh native bill',lambda d:d['summary']['incremental_costs'].__setitem__('fresh_native_micro_steps',0))
    test('counterfeit prior replay binding',lambda d:d['audit']['prior_full_replay_binding'].__setitem__('audit_sha256','0'*64))
    test('hidden feature work',lambda d:d['summary']['feature_cost_accounting'].__setitem__('fixed_feature_vectors',0))
    result=dict(status='passed',observations=16,proof_rows=row_count,actual_tiles=4*row_count,mutations=mutations,reader_sha256=sha(DOC/'hilbert_expanded_control_reader_001.json'),plan_sha256=sha(OUT/'plan.json'),audit_sha256=sha(OUT/'audit.json'))
    (OUT/'reader-checks.json').write_text(json.dumps(result,indent=2)+'\n');(DOC/'hilbert_expanded_control_reader_checks.json').write_bytes((OUT/'reader-checks.json').read_bytes());print(json.dumps(result))
if __name__=='__main__':main()
