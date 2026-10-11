"""Independent exact input/native provenance and complete certificate replay."""
import argparse,copy,gzip,hashlib,json,subprocess,sys,time
from pathlib import Path
from audit_first_order import free,subst
from audit_semantic_inventory import packed
from external_induction_tstp_audit import exact_input
from external_prover_check import native_formula
from external_left_successor_focus import check_output
from audit_certificate_boundary import initial_for
from audit_proof_boundary import input_bytes

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';OUT=ROOT/'.gcts-active/external-commutativity-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes())) if p.suffix=='.gz' else json.loads(p.read_text())
def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def digest(v):return sha(packed(v))
def need(t,message):
    if not t:raise ValueError(message)
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def instance(template,x):
    need(template[0]=='eq' and x in free(template),'nonvacuous equational induction only')
    f=['imp',['and',subst(template,x,['fun','zero',[]]),['all',x,['imp',template,subst(template,x,['fun','succ',[['var',x]]])]]],['all',x,template]]
    for y in reversed(sorted(free(template)-{x})):f=['all',y,f]
    return f
def alternatives(target):
    xs=[];body=target
    while body[0]=='all':xs.append(body[1]);body=body[2]
    need(len(xs)==len(set(xs)) and body[0]=='eq' and free(body)==set(xs),'complete declared bound variables')
    return [instance(body,x) for x in xs]
def binding():
    began=time.perf_counter();plan=load(OUT/'plan.json');bundle=load(OUT/'inventory.json');comm=load(DOC/'commutativity_plan.json')
    for n,h in plan['source_sha256'].items():need(sha((ROOT/n).read_bytes())==h,'source '+n)
    for n,e in plan['data_dependencies'].items():need(sha((ROOT/n).read_bytes())==e['sha256'],'input '+n)
    for e in plan['preserved_exports']:need(sha((ROOT/e['path']).read_bytes())==e['sha256'],'immutable prior export '+e['path'])
    need(sha((OUT/'inventory.json').read_bytes())==plan['inventory_sha256'] and bundle['spec']==comm['case'],'exact original assertion/theory binding')
    need(load(DOC/'commutativity_audit.json')['status']=='passed_complete_bounded_feasibility_audit','complete bounded grammar gate')
    expected={digest(f):f for f in alternatives(comm['case']['target'])}
    target_variables=[]
    for lane in comm['lanes']:
        c=load(DOC/('commutativity_'+lane['id'].replace('-','_')+'_full_core.json.gz'))
        need(c['spec']==comm['case'],'entire exact lane grammar')
        iv=[r['description']['variable'] for r in c['rules'] if r['description']['operation']=='induction']
        need(sorted(iv)==['x','y'],'both variable alternatives, not a chosen path')
        target_variables.append(dict(lane=lane['id'],variables=iv))
        for d in c['definitions']:
            for q in d['proof']:
                if q['rule']=='induction':
                    f=instance(q['template'],q['variable']);need(f==q['formula'],'native command formula/parameter closure');expected[digest(f)]=f
    earlier=load(ROOT/'.gcts-active/external-left-successor-20261011/inventory.json')
    for f in alternatives(earlier['spec']['target']):expected[digest(f)]=f
    need(earlier['spec']['theory']==bundle['spec']['theory'],'prior theorem theory equality')
    native_bindings=[];micro=load(DOC/'proof-boundary-microcode-001.json.gz');base=load(DOC/'proof-boundary-001.json')['cases'][0]['initial']
    for i,e in enumerate(bundle['lemmas']):
        q=load(ROOT/e['native_source_path'])[1];r=q['request']
        need(r==e['native_request'] and q==e['native_record'] and r['theory']==bundle['spec']['theory'] and not r['blocks'] and r['target']==e['formula'] and q['result']['status']=='accepted','exact accepted primitive certificate')
        need(q['request_sha256']==digest(r)==comm['lemma_sources'][i]['request_sha256'],'native assertion/certificate request hash')
        for command in r['proof']:
            if command['rule']=='induction':
                f=instance(command['template'],command['variable']);need(command['formula']==f,'accepted certificate finite schema export');expected[digest(f)]=f
        boot=initial_for(micro,base,r)
        if i==0:
            audit=load(ROOT/'.gcts-active/induction-receptors-20261011/compaction-audit.json');a=audit['variants'][1]
            need(audit['status']=='passed' and a['native_status']=='accepted' and a['native_micro_steps']==q['result']['micro_steps'] and a['whole_input_output_sha256_matched'],'accepted zero-left full native replay authority')
            need(q['boundary_words']==dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1]),'zero-left complete boundary words')
        else:
            audit=load(ROOT/'.gcts-active/left-successor-20261011/workspace-native/audit.json');a=audit['observations'][1]
            need(audit['status']=='passed_complete_larger_workspace_native_replay' and a['status']=='accepted' and a['request_sha256']==digest(r) and a['all_input_output_matched'] and not a['out_of_frame_bands'],'left-successor full native replay authority')
            for k in ('micro_steps','physical_steps','micro_fnv64'):need(str(a[k])==str(q['result'][k]),'left-successor execution fingerprint')
            boot['capacities'][26]=a['heap_capacity']
        need(sha(input_bytes(boot))==q['input_sha256'],'complete primitive certificate input/physical boundary hash')
        native_bindings.append(dict(request_sha256=digest(r),input_sha256=q['input_sha256'],output_sha256=q['output_sha256'],micro_steps=q['result']['micro_steps'],native_production_seconds=q['seconds'],native_audit_seconds=a['native_replay_seconds'] if i==0 else a['seconds'],native_authority_sha256=sha(packed(audit))))
    actual={digest(s['formula']):s['formula'] for s in bundle['schemas']}
    need(len(expected)==len(actual)==5 and expected==actual,'complete independently regenerated five-instance union')
    for e in plan['inputs']:
        path=OUT/e['name'];mapping=load(path.with_suffix('.mapping.json'));text=path.read_text()
        need(sha(path.read_bytes())==e['input_sha256'] and sha(path.with_suffix('.mapping.json').read_bytes())==e['mapping_sha256'],'exact exported input/mapping')
        need(exact_input(text,mapping)==e['entries'],'whole AST/role/signature export')
        need(mapping['entries'][-1]['role']=='conjecture','sole final conjecture')
        schemas={digest(x['formula']) for x in mapping['entries'] if x['name'].startswith('ind')}
        if not e['kind'].startswith('setup-'):
            need(schemas==set(actual) and mapping['entries'][-1]['formula']==bundle['spec']['target'],'same complete instance union and unchanged universal target')
            ls=[x for x in mapping['entries'] if x['role']=='lemma'];n={'theory':0,'zero-left':1,'both':2}[e['kind']]
            need(len(ls)==n and [x['formula'] for x in ls]==[x['formula'] for x in bundle['lemmas'][:n]],'all and only declared theorem transfers; no unadmitted block')
        else:
            lemma=bundle['lemmas'][int(e['kind'].split('-')[1])]
            need(schemas==set(lemma['induction_dependencies']) and mapping['entries'][-1]['formula']==lemma['formula'] and not any(x['role']=='lemma' for x in mapping['entries']),'no circular lemma setup')
    return dict(status='passed_exact_instance_union_inputs_native_provenance',seconds=time.perf_counter()-began,plan_sha256=sha((OUT/'plan.json').read_bytes()),native_bindings=native_bindings,target_variable_inventory=target_variables,instances=5,unadmitted_interface_inputs=0)
def replay(obs):
    path=OUT/('commutativity-'+obs['kind']+'.p');mapping=load(path.with_suffix('.mapping.json'));text=(OUT/(obs['stem']+'.tstp')).read_text()
    need(sha(text)==obs['output_sha256'] and text==obs['e_measurement']['stdout'],'complete prover output binding')
    need(obs['proof_check']['status']=='complete' and obs['proof_replay']['status']=='complete','whole check and independent saved replay required')
    again=check_output(text,mapping,str(path),saved=obs['proof_check']['result'])
    need(again['status']=='checked_complete_derivation' and again['steps']==obs['proof_steps'],'all preprocessing/consequences/context registries replayed')
    return dict(kind=obs['kind'],stem=obs['stem'],steps=again['steps'],used_lemma_inputs=again.get('used_lemma_inputs',[]),output_sha256=sha(text))
def before():
    began=time.perf_counter();gate=binding();summary=load(OUT/'summary.json')
    need(len(summary['setup'])==2 and not summary['observations'] and summary['fixtures']['status']=='passed','all setup/fixture gates before target')
    replays=[replay(o) for o in summary['setup']]
    gate.update(status='passed_complete_independent_pre_run_gate',setup_sha256=sha(packed(summary['setup'])),setup_replays=replays,seconds=time.perf_counter()-began,target_runs=0)
    dump(OUT/'pre-run-audit.json',gate);print('EXACT UNION/SETUP/FULL REPLAY GATE PASSED',gate['seconds'],flush=True)
def after():
    began=time.perf_counter();gate=binding();summary=load(OUT/'summary.json');replays=[];unknowns=[]
    for o in summary['setup']+summary['observations']:
        if o['certificate_status']=='checked_complete_derivation':replays.append(replay(o))
        else:
            text=(OUT/(o['stem']+'.tstp')).read_text();need(sha(text)==o['output_sha256'] and text==o['e_measurement']['stdout'],'all unknown output bytes preserved')
            unknowns.append(dict(kind=o['kind'],stem=o['stem'],status='unknown',error=o['proof_check']['result'].get('error')))
    schedule=load(OUT/'plan.json')['target_order']
    need(len(summary['observations'])+len(summary['unexecuted'])==6,'all scheduled target outcomes accounted')
    need([dict(kind=o['kind'],repetition=o['repetition']) for o in summary['observations']]==schedule[:len(summary['observations'])],'predeclared balanced order')
    need(summary['seconds']<=180.5,'aggregate cap accounted')
    result=dict(status='passed_complete_result_source_input_replay_audit',binding=gate,producer_status=summary['status'],completed_setup=len(summary['setup']),completed_targets=len(summary['observations']),checked_replays=replays,unknowns=unknowns,unexecuted=summary['unexecuted'],seconds=time.perf_counter()-began,scope='Independent full serialized certificate replay under unchanged external checkers; no new native Wang acceptance. Unknowns remain unknown and unexecuted schedules do not count as searches.')
    dump(OUT/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('binding','checked_replays')}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['before','after']);a=p.parse_args();{'before':before,'after':after}[a.phase]()
