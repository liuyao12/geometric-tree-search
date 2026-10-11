"""Independent union-input reconstruction, setup replay and returned-proof audit."""
import argparse,copy,gzip,json,pathlib,time
from external_prover_check import alpha,closed,free,native_formula
from external_prover_inputs import canonical,sha
from external_induction_tstp_audit import exact_input
from external_left_successor_inputs import OUT,ROOT,LANES,dump,load
from external_left_successor_tests import independent_schema
from external_left_successor_run import unchanged,op

def before():
    began=time.perf_counter();plan=unchanged();bundle=load(OUT/'inventory.json');snap=OUT/'snapshot';spec=load(snap/'plan.json')['case']
    if spec!=bundle['spec'] or sha((OUT/'inventory.json').read_bytes())!=plan['inventory_sha256'] or sha((OUT/'snapshot.json').read_bytes())!=plan['snapshot_manifest_sha256']:raise ValueError('exact source-derived union inventory binding')
    for e in load(OUT/'snapshot.json')['files']:
        if sha((snap/e['name']).read_bytes())!=e['sha256']:raise ValueError('immutable source artifact changed')
    m=load(OUT/'left-successor-library.mapping.json');expected={};occurrences=[]
    def collect(command,where):
        f=independent_schema(command['template'],command['variable'],m)
        if alpha(native_formula(command['formula'],m))!=alpha(f):raise ValueError('independent explicit induction formula closure')
        expected[canonical(alpha(f))]=f;occurrences.append(where)
    for lane in LANES:
        c=load(snap/(lane+'-core.json.gz'))
        for d in c['definitions']:
            for p in d['proof']:
                if p['rule']=='induction':collect(p,dict(lane=lane,name=d['name']))
        inds=[];count=0
        for word in gzip.open(snap/(lane+'-primitive.jsonl.gz'),'rb'):
            count+=1;p=json.loads(word)
            if p['rule']=='induction':collect(p,dict(lane=lane,primitive_line=count-1));inds.append(p['variable'])
        if inds!=['x','y']:raise ValueError('both target induction alternatives retained')
    if len(expected)!=3 or set(expected)!=set(canonical(alpha(native_formula(s['formula'],m))) for s in bundle['schemas']):raise ValueError('complete three-instance union not selected from proof path')
    # Same exact complete union theory, with only the optional24 lemma entries.
    counts=[]
    for kind in ('theory','library'):
        path=OUT/('left-successor-'+kind+'.p');mapping=load(path.with_suffix('.mapping.json'));counts.append(exact_input(path.read_text(),mapping))
        ids=[e['name'] for e in mapping['entries']]
        if ids!=['a0','a1','ind0','ind1','ind2']+(['l'+str(i) for i in range(24)] if kind=='library' else [])+['goal']:raise ValueError('complete fixed entry order')
        observed=[e for e in mapping['entries'] if e['role']=='axiom']
        if [e['formula'] for e in observed]!=[f for n,f in sorted(spec['theory']['axioms'].items())]+[s['formula'] for s in bundle['schemas']]:raise ValueError('same union axioms in both lanes')
        if mapping['entries'][-1]['formula']!=spec['target']:raise ValueError('unchanged universal target')
    if counts!=[6,30]:raise ValueError('entire six/thirty input census')
    core=load(snap/'with-searched-zero-left-reachable-core.json.gz');registry=load(snap/'with-searched-zero-left-admission.json');defs=core['definitions'];records={e['name']:e for e in registry['definitions']};schemas={s['id']:s['formula'] for s in bundle['schemas']};schema_ids={canonical(alpha(native_formula(s['formula'],m))):s['id'] for s in bundle['schemas']};setup=load(OUT/'setup.json')
    if setup['status']!='complete' or len(setup['interfaces'])!=24 or len(defs)!=24:raise ValueError('all-interface setup gate incomplete')
    pilot=load(snap/'pilot-native.json.gz');fresh=load(snap/'admission-native.json.gz');pa=load(snap/'pilot-audit.json');aa=load(snap/'admission-audit.json')
    for ledger,audits,count in [(pilot,pa['queries'],16),(fresh,aa['fresh_queries'],20)]:
        if len(ledger)!=count or len(audits)!=count:raise ValueError('every reused native computation accounted')
        for q,a in zip(ledger,audits):
            if q['id']!=a['query'] or q['result']['status']!=a['status'] or q['result']['micro_steps']!=a['micro_steps'] or not a.get('whole_input_output_matched',a.get('complete_input_output_sha256_matched')) or sha(canonical(q['request']))!=q['request_sha256']:raise ValueError('independent entire native ledger/audit binding')
    replays=[]
    for i,(e,d,r) in enumerate(zip(bundle['interfaces'],defs,setup['interfaces'])):
        f=native_formula(d['conclusion'],m)
        for p in reversed(d['premises']):f=('imp',native_formula(p,m),f)
        closure=sorted(free(f))
        for v in reversed(closure):f=('forall',v,f)
        deps=sorted({p['name'] for p in d['proof'] if p['rule']=='axiom'});ind=sorted({schema_ids[canonical(alpha(native_formula(p['formula'],m)))] for p in d['proof'] if p['rule']=='induction'})
        if e['id']!='l'+str(i) or e['definition']!=d or e['universal_closure_variables']!=closure or alpha(native_formula(e['formula'],m))!=alpha(f) or e['axiom_dependencies']!=deps or e['induction_dependencies']!=ind or e['native_admission']!=records[d['name']] or registry['complete_definition_sha256'][d['name']]!=sha(canonical(d)):raise ValueError('every actual admitted interface independently reconstructed')
        admission=records[d['name']];ledger=pilot if admission['source']=='pilot-exact-request' else fresh;q=ledger[admission['query']];taut=['imp',['bot'],['bot']]
        if q['request']!=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut) or q['result']['status']!='accepted' or q['request_sha256']!=admission['request_sha256']:raise ValueError('independent exact native local definition request')
        parents=[spec['theory']['axioms'][n] for n in deps]+[schemas[n] for n in ind]
        if r['id']!=e['id'] or r['request']['parents']!=parents or r['request']['child']!=e['formula'] or r['native_binding']!=e or r['measurement']['status']!='complete':raise ValueError('exact contextual setup dependency/result binding')
        reply=op(dict(r['request'],operation='interface-replay',saved=r['measurement']['result']),'audit-'+e['id']+'-pre-run-replay',30)
        if reply['status']!='complete':raise ValueError('fresh independent interface replay remains unknown')
        replays.append(dict(id=e['id'],measurement=reply))
    result=dict(status='passed_exact_source_input_inventory_setup_and_full_replay_gate',plan_sha256=sha((OUT/'plan.json').read_bytes()),setup_sha256=sha((OUT/'setup.json').read_bytes()),inventory_sha256=sha((OUT/'inventory.json').read_bytes()),input_entries=counts,declared_union_instances=len(expected),induction_occurrence_count=len(occurrences),complete_interfaces=24,reused_native_computations_bound=bundle['native_queries_bound'],interface_replays=replays,seconds=time.perf_counter()-began,target_prover_runs_before_gate=0,scope='All original grammar induction alternatives and every transferred predicate included in both lanes; each admitted contextual interface/dependency/closure independently reconstructed and complete certificates freshly replayed before E. This union is a wider instance language than native without-transfer, not a winning-variable choice or RL effect.')
    dump(OUT/'pre-run-audit.json',result);print('COMPLETE PRE-RUN SOURCE/INPUT/SETUP GATE PASSED',result['seconds'],flush=True)

def after():
    began=time.perf_counter();plan=unchanged();summary=load(OUT/'summary.json');gate=load(OUT/'pre-run-audit.json')
    if summary['status']!='complete' or len(summary['observations'])!=4 or summary['plan_sha256']!=sha((OUT/'plan.json').read_bytes()) or summary['pre_run_gate_sha256']!=sha((OUT/'pre-run-audit.json').read_bytes()):raise ValueError('complete unchanged result batch and pre-run gate')
    observations=[]
    for o,ordered in zip(summary['observations'],plan['order']):
        if o['kind']!=ordered['kind'] or o['repetition']!=ordered['repetition']:raise ValueError('balanced fresh process order')
        stem='left-successor-'+o['kind']+'-r'+str(o['repetition']);path=OUT/('left-successor-'+o['kind']+'.p');m=load(path.with_suffix('.mapping.json'));text=(OUT/(stem+'.tstp')).read_text()
        if sha(text)!=o['output_sha256'] or text!=o['e_measurement']['stdout'] or load(OUT/(stem+'.process.json'))!=o['e_measurement']:raise ValueError('exact E output/process binding')
        for suffix,measurement in [('check',o['proof_check'])]+([('replay',o['proof_replay'])] if o['proof_replay'] else []):
            req=load(OUT/(stem+'-'+suffix+'.request.json'))
            if sha((OUT/(stem+'-'+suffix+'.request.json')).read_bytes())!=measurement['request_sha256'] or req['output']!=text or req['mapping']!=m or req['input_path']!=str(path) or load(OUT/(stem+'-'+suffix+'.result.json'))!=measurement:raise ValueError('all target bounded check/replay request/results bound')
        if o['certificate_status']=='checked_complete_derivation':
            request=dict(operation='proof-replay',output=text,mapping=m,input_path=str(path),saved=o['proof_check']['result']);replay=op(request,'audit-'+stem+'-full-replay',300)
            if replay['status']!='complete':raise ValueError('complete returned derivation replay remains unknown')
            observations.append(dict(kind=o['kind'],repetition=o['repetition'],status='checked_complete_derivation',replay=replay))
        else:observations.append(dict(kind=o['kind'],repetition=o['repetition'],status='preserved_unknown_not_a_proof',error=o['proof_check']['result'].get('error'),original_result_sha256=sha((OUT/(stem+'-check.result.json')).read_bytes())))
    result=dict(status='passed_exact_saved_outcomes_audit',observations=observations,successful_checked_derivations=sum(o['status']=='checked_complete_derivation' for o in observations),unknown_checks=sum(o['status']!='checked_complete_derivation' for o in observations),pre_run_complete_interfaces=gate['complete_interfaces'],native_queries_bound=gate['reused_native_computations_bound'],summary_sha256=sha((OUT/'summary.json').read_bytes()),plan_sha256=sha((OUT/'plan.json').read_bytes()),seconds=time.perf_counter()-began,scope='Exact source/input/actual outcomes audited; every successful proof fully replayed, unknown checks remain unknown regardless of E theorem status. No target native acceptance or RL advantage is inferred.')
    dump(OUT/'audit.json',result);print('SAVED OUTCOMES AUDITED',result['successful_checked_derivations'],result['unknown_checks'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['before','after']);a=ap.parse_args();{'before':before,'after':after}[a.phase]()
