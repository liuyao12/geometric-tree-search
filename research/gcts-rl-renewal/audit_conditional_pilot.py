"""Complete conditional-pilot audit, including independently rerun native I/O."""
import gzip,hashlib,json,subprocess,time
from pathlib import Path
from types import SimpleNamespace
import audit_semantic_inventory as old
from audit_prefix_failure_markings import check_learning as unary_learning,check_overlay as unary_overlay,extended_tree,semantic
from audit_conditional_failure_markings import check_learning,check_overlay,check_combined,plain
from prefix_failure_differential import compare

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/conditional-attachments-20261011';TMP=Path('/private/tmp/gcts-conditional-independent-20261011')


def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def parent(raw):
    full=old.rebuild(raw['case'],raw['compiled'],raw['inventory'])
    return SimpleNamespace(spec=raw['case'],compiled=raw['compiled'],inventory=raw['inventory'],
        arity=full['arity'],mode=full['mode_ids'],record=lambda:full)


def main():
    began=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True)
    plan=json.loads((OUT/'plan.json').read_text())
    overrides=plan.get('audit_source_overrides',{})
    for name,h in plan['source_sha256'].items():
        if name in overrides:
            old.need(sha(HERE/overrides[name]['original_path'])==h,'archived exact pilot audit source '+name)
            old.need(sha(HERE/(name+'.py'))==overrides[name]['sha256'],'corrected independent audit source '+name)
        else:old.need(sha(HERE/(name+'.py'))==h,'exact pilot source '+name)
    previous=load(DOC/'semantic-inventory-001.json.gz')
    for name,h in {**previous['sources'],**previous['reused_sources']}.items():
        old.need(sha(HERE/name)==h,'unchanged previously checked engine/native dependency '+name)
    old.need((previous['program_sha256'],previous['micro_sha256'],previous['literal_table_sha256'])==
             (old.PINNED_PROGRAM,old.PINNED_MICRO,old.PINNED_TABLE),'unchanged native proof authority')
    policy_path=DOC/'semantic-inventory-policy-001.json';policy=json.loads(policy_path.read_text())
    raws=[load(OUT/(name+'-pilot.json.gz')) for name in plan['cases']]
    records=[r for d in raws for r in d['records']]
    old.need([r['id'] for r in records]==list(range(len(records))),'globally dense native query identifiers')
    requests={};cases=[];teacher_nodes=point_nodes=events=hints=0
    for raw in raws:
        name=raw['case']['id'];p=parent(raw)
        old.need(raw['frozen_policy_sha256']==sha(policy_path),'frozen policy bytes')
        if raw['reused_context'] is not None:
            source=raw['reused_context'];path=ROOT/source['path'];old.need(sha(path)==source['sha256'],'prior admission source')
            saved=load(path)
            old.need(saved['case']==raw['case'] and saved['compiled']==raw['compiled']
                     and saved['inventory']==raw['inventory'],'only exact prior admitted context reused')
        else:
            old.catalog(p.spec,p.compiled,records,requests)
            old.registration(p.spec,p.inventory,policy['library'],p.compiled['basis'],records,requests)
        uc=unary_learning(p,raw['unary_learning']);pc=check_learning(p,raw['learning'])
        old.need(uc==raw['unary_certificate'] and pc==raw['certificate'],'actual independent activation certificates')
        teacher_nodes+=uc['nodes']+pc['nodes']
        labels={(x['slot'],old.pin(x['formula'])):x['label'] for x in raw['unary_learning']['probes']}
        genuine=[x['id'] for x in raw['learning']['probes'] if x['label']=='negative'
            and all(labels[j,old.pin(f)]=='positive' for j,f in zip(x['slots'],x['formulas']))]
        old.need(genuine==raw['genuine_conditional_negatives'],'both individual words witnessed but conjunction exhausted')
        models=raw['models'];checks={}
        old.need(old.same(plain(models['original']),plain(p.record())),'identical original point model')
        root=old.initial(p.spec,p.record())
        old.need(old.same(models['original']['initial_marks'],sorted(root['marks'].items())),'original assertion boundary')
        checks['original']=dict(status='original')
        checks['unary']=unary_overlay(p,raw['unary_learning'],uc,models['unary'])
        checks['conditional']=check_overlay(p,raw['learning'],pc,models['conditional'])
        checks['combined']=check_combined(p,models['unary'],models['conditional'],models['combined'])
        old.need(checks==raw['overlay_checks'],'all separately checked overlays')
        rows=[]
        old.need([(r['layer'],r['mode']) for r in raw['results']]==
                 [(l,m) for l in plan['layers'] for m in plan['modes']],'every matched lane exactly once')
        for r in raw['results']:
            model=models[r['layer']];out=r['search'];weights=policy['weights'] if r['mode']=='learned' else None
            check=extended_tree(p.spec,model,out,p.inventory,weights,model['initial_marks'])
            old.need(check==r['tree_check'],'actual complete pre-recorded tree audit')
            point_nodes+=check['nodes'];events+=check['events'];hints+=check['hints']
            q=r['native_query']
            if q is not None:
                request=dict(protocol='gcts-fol-1',theory=p.spec['theory'],blocks=old.closure(p.inventory,out['proof']),
                             proof=out['proof'],target=p.spec['target'])
                rec=records[q]
                old.need(q not in requests and old.same(rec['request'],request) and rec['result']['status']=='accepted'
                    and rec['purpose']=='conditional_pilot_final_'+r['layer']+'_'+r['mode'],
                    'fresh native check of exact searched proof with all failure markings erased')
                requests[q]=request
            else:old.need(out['proof'] is None,'unknown produces no accepted proof')
            rows.append(dict(layer=r['layer'],mode=r['mode'],status=out['status'],metrics=out['metrics'],
                graph_metrics=out['graph_metrics'],seconds=out['seconds'],check=check,native_query=q))
        smt=None
        if raw['smt_control'] is not None:
            out=raw['smt_control'];smt=old.smt_encoding(models['original'],out)
            q=out.get('native_query')
            if q is not None:
                request=dict(protocol='gcts-fol-1',theory=p.spec['theory'],blocks=old.closure(p.inventory,out['proof']),
                             proof=out['proof'],target=p.spec['target'])
                old.need(q not in requests and records[q]['purpose']=='fresh_joint_z3_control'
                    and old.same(records[q]['request'],request) and records[q]['result']['status']=='accepted',
                    'fresh checked original-model SMT proof')
                requests[q]=request
        domains={}
        for layer,model in models.items():
            state=old.initial(p.spec,model);state['marks']={tuple(k):v for k,v in model['initial_marks']}
            literal=old.LiteralDomains({tuple(c['key']):c for c in model['placements']})(state)
            domains[layer]=dict(incidences=sum(map(len,literal.values())),
                forced=sum(len(v)==1 for v in literal.values()),dead=sum(not v for v in literal.values()))
        cases.append(dict(case=name,artifact_sha256=sha(OUT/(name+'-pilot.json.gz')),unary_certificate=uc,
            pair_certificate=pc,genuine_conditional_negatives=genuine,overlay_checks=checks,
            root_domains=domains,observations=rows,smt_check=smt))
        (OUT/'audit-progress.json').write_text(json.dumps(dict(status='running',cases=cases),indent=2)+'\n')
        print(name,'all teachers and 12 search trees independently checked',flush=True)
    # Exhaustive original/conditional/combined census on the unchanged tiny
    # theorem context, using literal point values and independent logical replay.
    training=load(DOC/'semantic-inventory-training-001.json.gz')
    spec=next(s for s in training['cases'] if s['id']=='two-premise')
    # The dedicated tests record both complete censuses. Their exact file and
    # source hashes are reported; larger pilot cases use causal certificates.
    old.need(set(requests)==set(range(len(records))),'every new native query has a bound purpose')
    micro=load(DOC/'proof-boundary-microcode-001.json.gz');old.need(old.pin(micro)==old.PINNED_MICRO,'entire native microcode')
    old.need(hashlib.sha256(gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes())).hexdigest()==old.PINNED_TABLE,
             'unchanged literal Wang palette')
    template=json.loads((DOC/'proof-boundary-001.json').read_text())['cases'][0]['initial']
    old.TMP=TMP;(TMP/'code.bin').write_bytes(old.code_bytes(micro))
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True)
    steps,accepted=old.replay_native(records,requests,micro,template)
    result=dict(version='conditional-pilot-audit-001',status='passed',cases=cases,teacher_nodes=teacher_nodes,
        point_nodes=point_nodes,events=events,hints=hints,native_queries=len(records),micro_steps=steps,
        accepted_distinct_native_requests=len(accepted),seconds=time.perf_counter()-began,
        pilot_sources=plan['source_sha256'],audit_source_overrides=overrides,source_sha256=sha(Path(__file__)),
        scope='Complete original and two-word teacher reconstruction, every causal lift, exact unary/pair/combined marking support, all 36 point-search trees and policy decisions, submitted SMT assertions, and every fresh native computation from the true parser start. Explicit reuse of old context admission/families/frozen policy. One run per lane, no cold speedup or new RL claim.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('AUDIT PASSED',point_nodes,'point nodes',teacher_nodes,'teacher nodes',len(records),'native queries',flush=True)


if __name__=='__main__':main()
