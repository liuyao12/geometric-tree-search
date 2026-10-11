"""Repeat exact finite-theory/library searches in a NEW output directory.

Uses byte-preserved public evidence and the pinned checker source closure. A
different E binary is clearly recorded as a new experiment. Native acceptance
audits are historical provenance; this script independently rechecks the FOL
interfaces and returned E proofs, and does not claim a native Wang replay.
"""
import argparse,gzip,json,pathlib,re,subprocess,time
from external_prover_inputs import sha,canonical
from external_induction_tstp_audit import exact_input
import external_induction_tstp_run as runner

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--e',required=True);ap.add_argument('--data',default='docs/research/gcts-rl-renewal/external_induction_tstp_control_data.json.gz');a=ap.parse_args();began=time.perf_counter()
    data_path=pathlib.Path(a.data);data=json.loads(gzip.decompress(data_path.read_bytes()));files=data['frozen_records']
    for name,item in data['source_files'].items():
        raw=item['text'].encode()
        if sha(raw)!=item['sha256'] or len(raw)!=item['bytes'] or sha((runner.ROOT/name).read_bytes())!=item['sha256']:raise ValueError('exact checker/driver source closure mismatch '+name)
    def record(name):
        item=files[name];raw=item['text'].encode()
        if sha(raw)!=item['sha256'] or len(raw)!=item['bytes']:raise ValueError('saved artifact byte binding '+name)
        return item['text']
    plan=json.loads(record('plan.json'));audit=json.loads(record('audit.json'));bundle=json.loads(record('bundle.json'))
    if audit['status']!='passed' or audit['plan_sha256']!=sha(record('plan.json')) or audit['exact_native_queries_bound']!=92 or audit['preserved_unknown_derivations']!=4:raise ValueError('completed source audit binding')
    schema={s['id']:s['formula'] for s in bundle['schemas']};axioms=bundle['plan']['assertion']['theory']['axioms']
    out=pathlib.Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False);runner.OUT=out;e=pathlib.Path(a.e).resolve()
    actual_binary=sha(e.read_bytes());version=subprocess.run([str(e),'--version'],capture_output=True,text=True,check=True).stdout.strip()
    input_paths={};mappings={}
    for kind,count in [('theory',4),('library',70)]:
        text=record('arithmetic-'+kind+'.p');mapping=json.loads(record('arithmetic-'+kind+'.mapping.json'))
        if exact_input(text,mapping)!=count:raise ValueError('complete declared input inventory')
        path=out/('arithmetic-'+kind+'.p');path.write_text(text);runner.dump(path.with_suffix('.mapping.json'),mapping);input_paths[kind]=path;mappings[kind]=mapping
    freeze=dict(status='frozen_before_interface_checks_and_E_runs',source_evidence_sha256=sha(data_path.read_bytes()),original_plan_sha256=audit['plan_sha256'],binary_sha256=actual_binary,original_binary_sha256=plan['prover_binary_sha256'],version=version,classification='same pinned binary, fresh experiment' if actual_binary==plan['prover_binary_sha256'] else 'different binary: new experiment, original timing not reproduced',options=plan['options'],order=plan['order'],inputs={k:dict(path=str(p),sha256=sha(p.read_bytes()),entries=len(mappings[k]['entries'])) for k,p in input_paths.items()},theory_scope=plan['theory_scope'],setup_scope='all66 interfaces from exact contextual axiom/finite-schema dependencies',native_scope='passed92 native prior computations disclosed as reused historical source audit; no native computation rerun',preparation_seconds=time.perf_counter()-began)
    runner.dump(out/'plan.json',freeze);setup=[];setup_began=time.perf_counter()
    for interface in bundle['interfaces']:
        parents=[axioms[n] for n in interface['axiom_dependencies']]+[schema[n] for n in interface['induction_dependencies']]
        request=dict(operation='interface',parents=parents,child=interface['formula'],mapping=mappings['library'])
        checked=runner.operation(request,interface['id']+'-setup',30)
        if checked['status']!='complete':raise ValueError('fresh setup unknown '+interface['id'])
        replayed=runner.operation(dict(request,operation='interface-replay',saved=checked['result']),interface['id']+'-replay',30)
        if replayed['status']!='complete':raise ValueError('fresh setup replay unknown '+interface['id'])
        setup.append(dict(id=interface['id'],check=checked,replay=replayed))
    runner.dump(out/'setup.json',dict(status='complete',interfaces=setup,seconds=time.perf_counter()-setup_began));observations=[];target_began=time.perf_counter()
    for item in plan['order']:
        kind=item['kind'];path=input_paths[kind];stem='arithmetic-'+kind+'-r'+str(item['repetition']);measured=runner.execute([str(e),*plan['options'],str(path)],plan['prover_wall_cutoff_seconds']);text=measured['stdout'];(out/(stem+'.tstp')).write_text(text);runner.dump(out/(stem+'.process.json'),measured)
        request=dict(operation='proof',output=text,mapping=mappings[kind],input_path=str(path));checked=runner.operation(request,stem+'-check',300)
        replayed=runner.operation(dict(request,operation='proof-replay',saved=checked['result']),stem+'-replay',300) if checked['status']=='complete' else None
        status=re.search(r'SZS status (\w+)',text);o=dict(kind=kind,repetition=item['repetition'],szs_status=status.group(1) if status else 'missing',e_measurement=measured,check=checked,replay=replayed,certificate_status='checked_complete_derivation' if checked['status']=='complete' and replayed['status']=='complete' else 'unknown');observations.append(o)
        runner.dump(out/'summary.json',dict(status='complete' if len(observations)==4 else 'running',observations=observations,target_seconds=time.perf_counter()-target_began,setup_seconds=time.perf_counter()-setup_began-(time.perf_counter()-target_began),preparation_seconds=freeze['preparation_seconds']))
        print(kind,item['repetition'],o['certificate_status'],flush=True)
    print('Fresh reproduction complete. Outputs:',out,flush=True)

if __name__=='__main__':main()
