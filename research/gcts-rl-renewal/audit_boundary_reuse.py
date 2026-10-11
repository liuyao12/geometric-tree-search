"""Independent source, transfer, literal-domain and new native proof audit.

Imports no boundary-reuse producer, direct state, worker, constraint constructor
or search. Direct trees are checked via the exact literal point equivalence;
their actual unaugmented state hashes are checked before projection.
"""
import collections,copy,gzip,hashlib,json,subprocess,time
from pathlib import Path
from types import SimpleNamespace
import audit_semantic_inventory as old
from audit_conditional_failure_markings import check_learning,check_overlay,plain
from audit_prefix_failure_markings import extended_tree,bound_context

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/boundary-reuse-20261011';TMP=Path('/private/tmp/gcts-boundary-reuse-audit-20261011')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(gzip.decompress(path.read_bytes()))


def parent(spec,compiled,inventory):
    full=old.rebuild(spec,compiled,inventory)
    return SimpleNamespace(spec=spec,compiled=compiled,inventory=inventory,arity=full['arity'],
        mode=full['mode_ids'],record=lambda:full)


def admit(raw,spec,packet,source):
    p=parent(spec,raw['compiled'],raw['inventory'])
    certificate=check_learning(p,raw['learning'])
    old.need(certificate==raw['certificate'],'all old teacher transcripts rechecked in target boundary')
    expected=dict(version='boundary-reuse-constraints-001',source=source,
        learning_sha256=old.pin(raw['learning']),context=bound_context(p),
        context_sha256=old.pin(bound_context(p)),counts=raw['learning']['counts'],
        pair_certificate=certificate,
        negatives=[dict(id=x['id'],slots=x['slots'],formulas=x['formulas'])
                   for x in raw['learning']['probes'] if x['label']=='negative'])
    old.need(old.same(packet,expected),'every and only certified negative reused; exact source/theory/word scope')
    return dict(version='boundary-transfer-admission-001',status='passed',
        packet_sha256=old.pin(packet),target_spec_sha256=old.pin(spec),
        target_model_sha256=old.pin(p.record()),source_learning_sha256=old.pin(raw['learning']),
        source_length=raw['case']['length'],target_length=spec['length'],
        pairs=certificate['pairs'],teacher_nodes=certificate['nodes'],
        scope='Independent full target reconstruction, whole source pair catalog, every teacher tree and complete causal prefix lift. No new labels or proof sequence supplied; no unbounded completeness claim.')


def direct_record(original,point,record):
    old.need(old.same(plain(original),{k:v for k,v in plain(record).items() if k!='direct_constraints'}),
             'direct control retains every original candidate and t/m value')
    fields=record['direct_constraints'];expected=[];tokens=[];membership=collections.defaultdict(lambda:[0,0,0])
    for f in point['conditional_overlay']['failures']:
        expected.append({k:v for k,v in f.items() if k!='assignments'})
        keys=set()
        for i,name in enumerate(('left_keys','right_keys','joint_keys')):
            for key in f[name]:
                key=tuple(key);membership[key][i]|=1<<f['probe'];keys.add(key)
        tokens.append(dict(token=('failure',f['probe']),keys=sorted(keys)))
    wanted=dict(failures=expected,dependency_tokens=tokens,
                membership=[dict(key=k,left=a,right=b,joint=c) for k,(a,b,c) in sorted(membership.items())])
    old.need(old.same(wanted,fields),'all direct clause incidences, distant consumers and shared writers')
    old.need(old.same(original['initial_marks'],record['initial_marks']),'no added direct point boundary')
    return dict(status='passed',clauses=len(expected),membership_candidates=len(membership))


def direct_tree(spec,original,point,result,inventory):
    old.need(result['mode']=='base' and not result['events'] and not result['hints'],
             'representation control has matched unlearned base ordering')
    point_lookup={tuple(c['key']):c for c in point['placements']}
    original_lookup={tuple(c['key']):c for c in original['placements']}
    source=old.initial(spec,original);source['marks']={tuple(p):v for p,v in original['initial_marks']}
    target=old.initial(spec,point);target['marks']={tuple(p):v for p,v in point['initial_marks']}
    old.need(result['root_state_sha256']==old.state_pin(source),'actual direct root state')
    translated=copy.deepcopy(result)
    def walk(s,m,t):
        old.need(t['state_sha256']==old.state_pin(s),'actual direct unaugmented state at every node')
        t['state_sha256']=old.state_pin(m)
        for child in t['children']:
            key=tuple(child['key'])
            old.need(key in original_lookup and old.legal(original_lookup[key],s),
                     'direct selected base placement and ordinary original markings')
            walk(old.advance(original_lookup[key],s),old.advance(point_lookup[key],m),child['tree'])
    walk(source,target,translated['tree']);translated['root_state_sha256']=old.state_pin(target)
    checked=extended_tree(spec,point,translated,inventory,None,point['initial_marks'])
    return dict(**checked,projection='Independent exact point comparison; original direct state hashes separately checked')


def semantic_tree(result):
    tree=copy.deepcopy(result['tree'])
    def strip(t):
        t.pop('state_sha256')
        for child in t['children']:strip(child['tree'])
    strip(tree)
    return old.pin(dict(tree=tree,proof=result['proof'],placements=result['placements'],
        tile_generations=result['tile_generations'],metrics=result['metrics'],events=result['events'],hints=result['hints']))


def main():
    began=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True)
    plan=json.loads((OUT/'plan.json').read_text())
    for path,h in plan['source_sha256'].items():old.need(sha(ROOT/path)==h,'pinned source '+path)
    for path,h in plan['prior_source_closure'].items():old.need(sha(ROOT/path)==h,'unchanged source authority '+path)
    prior=load(DOC/'conditional-audit-001.json.gz');old.need(prior['status']=='passed','published prior audit')
    old.need(sha(DOC/'conditional-audit-001.json.gz')==plan['prior_audit_sha256'],'exact prior audit authority')
    policy_path=DOC/'semantic-inventory-policy-001.json';policy=json.loads(policy_path.read_text())
    old.need(sha(policy_path)==plan['policy_sha256'],'frozen policy bytes')
    summaries=[];requests={};records=load(OUT/'native-records.json.gz');nodes=events=hints=0
    old.need([q['id'] for q in records]==list(range(len(records))),'dense new native query ids')
    used_queries=set();observations=0
    for config in plan['configs']:
        raw=load(OUT/(config['id']+'.json.gz'));source=raw['source'];path=ROOT/source['path']
        old.need(sha(path)==source['sha256'],'exact reused source artifact')
        saved=load(path);saved_case=next(c for c in prior['cases'] if c['case']==saved['case']['id'])
        old.need(saved_case['artifact_sha256']==source['sha256'],'source native authority bound by prior audit')
        spec=copy.deepcopy(saved['case']);spec.update(id=config['id'],length=config['length'],
            scope='Same symbolic assertion and syntax inventory; declared finite boundary comparison.')
        old.need(raw['case']==spec and raw['compiled']==saved['compiled'] and raw['inventory']==saved['inventory'],
                 'boundary-only change with same admitted grammar and inventory')
        certificate=admit(saved,spec,raw['constraints'],source)
        old.need(certificate==raw['transfer_certificate'],'actual independent pre-search transfer certificate')
        p=parent(spec,raw['compiled'],raw['inventory']);models=raw['models']
        old.need(old.same(plain(p.record()),plain(models['original'])),'original full candidate universe')
        root=old.initial(spec,p.record());old.need(old.same(models['original']['initial_marks'],sorted(root['marks'].items())),
                                                'original boundary word')
        overlay=check_overlay(p,saved['learning'],saved['certificate'],models['point'])
        direct=direct_record(models['original'],models['point'],models['direct'])
        schedule=plan['schedules'][config['id']]
        old.need([(x['repetition'],x['layer'],x['mode']) for x in raw['results']]==
                 [(s['repetition'],s['layer'],s['mode']) for s in schedule],'every predeclared lane and process order')
        rows=[];equivalence=[]
        for observation in raw['results']:
            out=observation['search'];layer=observation['layer'];mode=observation['mode']
            old.need(out['limits']==plan['search_limits'] and out['mode']==mode and out['seed']==66000
                     and not out['stochastic'],'predeclared equal search budget and deterministic policy')
            if layer=='direct':checked=direct_tree(spec,models['original'],models['point'],out,p.inventory)
            else:checked=extended_tree(spec,models[layer],out,p.inventory,
                        policy['weights'] if mode=='learned' else None,models[layer]['initial_marks'])
            old.need(checked==observation['tree_check'],'recorded complete immediate audit')
            nodes+=checked['nodes'];events+=checked['events'];hints+=checked['hints'];observations+=1
            q=observation['native_query']
            if out['proof'] is None:
                old.need(q is None and not observation['cached_native_acceptance'],'unfinished search has no acceptance')
            else:
                request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=old.closure(p.inventory,out['proof']),
                             proof=out['proof'],target=spec['target'])
                old.need(q is not None and old.same(records[q]['request'],request)
                         and records[q]['result']['status']=='accepted','exact whole native proof with failure layer erased')
                if observation['cached_native_acceptance']:old.need(q in used_queries,'only earlier exact acceptance reused')
                else:old.need(q not in used_queries and records[q]['purpose']=='boundary_reuse_final','first new acceptance')
                used_queries.add(q);requests[q]=request
            old.need(observation['peak_rss_bytes']>0 and observation['worker_wall_seconds']>=out['seconds']
                     and observation['setup_seconds']>=0 and observation['representation_seconds']>=0,
                     'whole-worker memory and measured timing scopes')
            rows.append(dict(layer=layer,mode=mode,repetition=observation['repetition'],status=out['status'],
                metrics=out['metrics'],graph_metrics=out['graph_metrics'],seconds=out['seconds'],
                worker_wall_seconds=observation['worker_wall_seconds'],setup_seconds=observation['setup_seconds'],
                representation_seconds=observation['representation_seconds'],peak_rss_bytes=observation['peak_rss_bytes'],
                native_query=q,cached_native_acceptance=observation['cached_native_acceptance'],check=checked))
        for repetition in plan['repetitions']:
            a=next(x['search'] for x in raw['results'] if x['layer']=='point' and x['mode']=='base' and x['repetition']==repetition)
            b=next(x['search'] for x in raw['results'] if x['layer']=='direct' and x['repetition']==repetition)
            old.need(semantic_tree(a)==semantic_tree(b),'identical point/direct full censuses, scheduler, alternatives, outcomes and proof')
            equivalence.append(dict(repetition=repetition,nodes=a['metrics']['nodes'],sha256=semantic_tree(a)))
        summaries.append(dict(case=config['id'],artifact_sha256=sha(OUT/(config['id']+'.json.gz')),
            transfer_certificate=certificate,overlay=overlay,direct=direct,equivalence=equivalence,
            transfer_seconds=raw['transfer_seconds'],source_collection_seconds=raw['source_collection_seconds'],observations=rows))
        (OUT/'audit-progress.json').write_text(json.dumps(dict(status='running',cases=summaries),indent=2)+'\n')
        print(config['id'],'all transfer data and',len(rows),'search trees checked',flush=True)
    old.need(used_queries==set(range(len(records))),'every new computation tied to an actual searched proof')
    micro=load(DOC/'proof-boundary-microcode-001.json.gz');old.need(old.pin(micro)==old.PINNED_MICRO,'unchanged whole native microcode')
    old.need(hashlib.sha256(gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes())).hexdigest()==old.PINNED_TABLE,
             'unchanged primitive Wang table')
    template=json.loads((DOC/'proof-boundary-001.json').read_text())['cases'][0]['initial'];old.TMP=TMP
    (TMP/'code.bin').write_bytes(old.code_bytes(micro))
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True)
    steps,accepted=old.replay_native(records,requests,micro,template)
    result=dict(version='boundary-reuse-audit-001',status='passed',cases=summaries,observations=observations,
        point_nodes=nodes,events=events,hints=hints,native_queries=len(records),micro_steps=steps,
        accepted_distinct_native_requests=len(accepted),seconds=time.perf_counter()-began,
        source_sha256=plan['source_sha256'],prior_source_closure=plan['prior_source_closure'],
        scope='Boundary-only transfers, every reused teacher and full causal lift, all compact constraints and writer incidences, every search tree and frozen policy decision, exact point/direct base equivalence, and all fresh distinct native computations from the true parser start. Prior 65 admissions and 63 policy explicitly reused; no new labels or RL training.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('BOUNDARY AUDIT PASSED',nodes,'nodes',len(records),'native requests',flush=True)


if __name__=='__main__':main()
