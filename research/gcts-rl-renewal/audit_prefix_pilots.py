"""Audit both archived marking constructions and all paired pilot searches.

No new learner, marking producer, search engine or proof verifier is imported.
The original inventory, literal point domains and native interpreter are the
independently authored Notebook 63 audit authorities. Global query IDs are
retained across the three consumer documents.
"""
import copy,gzip,hashlib,json,subprocess,time
from pathlib import Path
from types import SimpleNamespace
import audit_semantic_inventory as old
from audit_prefix_failure_markings import (check_learning,check_overlay,
    extended_tree,semantic,bound_context)
from prefix_failure_differential import compare

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/certified-prefix-markings-20261011'
TMP=Path('/private/tmp/gcts-prefix-pilot-audit-001')

def load(path):return json.loads(gzip.decompress(path.read_bytes()))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def parent(raw):
    spec=raw['case'];compiled=raw['compiled'];inventory=raw['inventory']
    full=old.rebuild(spec,compiled,inventory)
    return SimpleNamespace(spec=spec,compiled=compiled,inventory=inventory,
        arity=full['arity'],mode=full['mode_ids'],record=lambda:full)

def output_overlay(p,learning,certificate,record):
    """Independent reconstruction of the archived output-command-only layer."""
    full=p.record();expected=copy.deepcopy(full);exterior={};failures=[]
    by_key={tuple(c['key']):c for c in expected['placements']}
    for probe in learning['probes']:
        if probe['label']!='negative':continue
        point=(4*probe['slot']+3,100000+p.compiled['basis'].index(probe['formula']))
        exterior[point]=0
        keys=[tuple(c['key']) for c in full['placements'] if c['kind']=='command'
            and c['slot']==probe['slot'] and c['command']['formula']==probe['formula']]
        old.need(old.same(keys,probe['command_keys']),'complete output-only exclusion support')
        for key in keys:
            c=by_key[key]
            old.need(all(tuple(q)!=point for q,v in c['marks']+c['occupancy']),'private extra point')
            c['marks']=sorted(c['marks']+[(point,1)])
        failures.append(dict(probe=probe['id'],slot=probe['slot'],formula=probe['formula'],
            point=point,exterior_value=0,tile_value=1,command_keys=keys))
    old.need(old.same(semantic(expected),semantic(record)),'every archived output-only placement')
    overlay=record['failure_overlay']
    old.need(overlay['certificate']==certificate and overlay['learning_sha256']==old.pin(learning)
        and overlay['context_sha256']==old.pin(bound_context(p))
        and old.same(overlay['exterior'],sorted(exterior.items()))
        and old.same(overlay['failures'],failures),'exact archived boundary and provenance')
    state=old.initial(p.spec,full);state['marks'].update(exterior)
    old.need(old.same(record['initial_marks'],sorted(state['marks'].items())),'archived zero boundary')
    return dict(status='passed',negative_ports=len(exterior),affected_candidates=
        len({tuple(k) for f in failures for k in f['command_keys']}))

def skeleton(node):
    return {k:(skeleton(v) if k=='tree' else
        [skeleton(c) for c in v] if k=='children' else v)
        for k,v in node.items() if k not in ('census','state_sha256')}

def main():
    began=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True)
    policy=json.loads((DOC/'semantic-inventory-policy-001.json').read_text())
    manifest=load(DOC/'semantic-inventory-001.json.gz')
    frozen={**manifest['sources'],**manifest['reused_sources']}
    for name,digest in frozen.items():old.need(sha(HERE/name)==digest,'unchanged source '+name)
    for name,digest in json.loads((OUT/'consumer-pilot-source-pins.json').read_text()).items():
        old.need(sha(HERE/name)==digest,'consumer source at run '+name)
    old.need((manifest['program_sha256'],manifest['micro_sha256'],manifest['literal_table_sha256'])==
        (old.PINNED_PROGRAM,old.PINNED_MICRO,old.PINNED_TABLE),'unchanged native authority')
    micro=load(DOC/'proof-boundary-microcode-001.json.gz')
    old.need(old.pin(micro)==old.PINNED_MICRO,'complete microcode pin')
    old.need(hashlib.sha256(gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes())).hexdigest()==old.PINNED_TABLE,'literal palette pin')
    template=json.loads((DOC/'proof-boundary-001.json').read_text())['cases'][0]['initial']
    old.TMP=TMP;(TMP/'code.bin').write_bytes(old.code_bytes(micro))
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True)
    cases=[];records=[];requests={};teacher_nodes=point_nodes=events=hints=0;differential=None
    for name in ('two-premise','pa-universal-equality','renamed-five'):
        original_path=OUT/'pilot-output-only'/(name+'-pilot.json.gz')
        consumer_path=OUT/(name+'-consumer-pilot.json.gz')
        raw=load(original_path);consumer=load(consumer_path);p=parent(raw)
        old.need(consumer['original_pilot_sha256']==sha(original_path),'paired label origin')
        old.need(consumer['case']==raw['case'] and consumer['compiled']==raw['compiled']
            and consumer['inventory']==raw['inventory'] and consumer['learning']==raw['learning'],
            'same original model and current-turn labels across propagation constructions')
        certificate=check_learning(p,raw['learning'])
        old.need(certificate==raw['certificate']==consumer['certificate'],'actual prior activation audit')
        teacher_nodes+=certificate['nodes'];observations=[]
        for variant,data in (('output-only',raw),('all-writers',consumer)):
            for r in data['results']:
                marked=r.get('marked',True);model=r['model'];result=r['search']
                weights=policy['weights'] if r['mode']=='learned' else None
                if marked:
                    overlay=(output_overlay(p,raw['learning'],certificate,model) if variant=='output-only'
                        else check_overlay(p,raw['learning'],certificate,model))
                    initial_marks=model['initial_marks']
                else:
                    old.need(old.same(semantic(p.record()),semantic(model)),'unchanged original model')
                    overlay=None;initial_marks=sorted(old.initial(p.spec,model)['marks'].items())
                check=extended_tree(p.spec,model,result,p.inventory,weights,initial_marks)
                if 'tree_check' in r:old.need(check==r['tree_check'],'pre-recorded full consumer tree audit')
                point_nodes+=check['nodes'];events+=check['events'];hints+=check['hints']
                obs=dict(variant=variant,mode=r['mode'],marked=marked,status=result['status'],
                    metrics=result['metrics'],graph_metrics=result['graph_metrics'],seconds=result['seconds'],
                    check=check,overlay=overlay,native_query=r.get('native_query'))
                if variant=='all-writers':
                    reference=next(x for x in raw['results'] if x['mode']==r['mode'] and not x['marked'])['search']
                    obs['same_placements']=reference['placements']==result['placements']
                    obs['same_metrics']=reference['metrics']==result['metrics']
                    obs['same_choice_events']=old.same(reference['events'],result['events'])
                    q=r.get('native_query')
                    if q is not None:
                        rec=next(rec for rec in consumer['records'] if rec['id']==q)
                        request=dict(protocol='gcts-fol-1',theory=p.spec['theory'],
                            blocks=old.closure(p.inventory,result['proof']),proof=result['proof'],target=p.spec['target'])
                        old.need(old.same(rec['request'],request) and rec['purpose']=='consumer_failure_marking_pilot'
                            and rec['result']['status']=='accepted','fresh whole native check for exactly the searched proof')
                        requests[q]=request
                    else:old.need(result['proof'] is None,'unknown search invents no accepted proof')
                observations.append(obs)
                print(name,variant,r['mode'],marked,'tree audited',check['nodes'],flush=True)
        records.extend(consumer['records'])
        if name=='two-premise':
            original=next(r['model'] for r in raw['results'] if not r['marked'])
            differential=compare(p.spec,original,consumer['results'][0]['model'],p.inventory)
        cases.append(dict(case=name,certificate=certificate,observations=observations,
            original_sha256=sha(original_path),consumer_sha256=sha(consumer_path)))
        (OUT/'audit-progress.json').write_text(json.dumps(dict(status='running',cases=cases),indent=2)+'\n')
        del raw,consumer
    old.need([r['id'] for r in records]==list(range(7)) and set(requests)==set(range(7)),
        'all seven globally numbered queries accounted for')
    steps,accepted=old.replay_native(records,requests,micro,template)
    old.need(len(accepted)>=3,'three distinct assertions independently native checked')
    result=dict(version='prefix-pilot-audit-001',status='passed',cases=cases,
        teacher_nodes=teacher_nodes,point_nodes=point_nodes,events=events,hints=hints,
        native_queries=len(records),micro_steps=steps,finite_equivalence=differential,
        frozen_source_sha256=frozen,source_sha256=sha(Path(__file__)),seconds=time.perf_counter()-began,
        scope='Every prefix teacher, exact causal lift and both redundant marking constructions; all 27 recorded point-search trees, all bounded policy choices and rollback; every fresh native query independently rerun from the true parser start with exact input/output hashes. Cached Notebook 63 admission, families and weights are reused, with no cold benchmark or speedup claim. Full native certificate DAGs are those in Notebook 63; this increment replays the seven whole computations, not new line-DAG materialization.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('AUDIT PASSED',point_nodes,'search nodes,',teacher_nodes,'teacher nodes,',len(records),'native queries',flush=True)

if __name__=='__main__':main()
