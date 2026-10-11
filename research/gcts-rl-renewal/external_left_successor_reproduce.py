"""Fresh first-order reproduction from downloadable exact source/inventory bytes."""
import argparse,base64,copy,gzip,json,pathlib,subprocess,time
from external_prover_inputs import sha
from external_left_successor_inputs import ROOT,load,dump
import external_left_successor_focus_run as focus
import external_left_successor_run as original
import external_left_successor_audit as auditor
from external_induction_tstp_audit import exact_input

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--e',required=True);a=ap.parse_args()
    began=time.perf_counter();out=pathlib.Path(a.output).resolve()
    if out.exists():raise ValueError('fresh reproduction output must not exist')
    e=pathlib.Path(a.e).resolve();data=json.loads(gzip.decompress((ROOT/'docs/research/gcts-rl-renewal/external_left_successor_control_data.json.gz').read_bytes()))
    for name,entry in data['source_files'].items():
        if sha((ROOT/name).read_bytes())!=entry['sha256']:raise ValueError('reproduction source differs from export '+name)
    out.mkdir(parents=True);private=data['private_files'];prefix='attempt-03/'
    def raw(key):
        entry=private[prefix+key]
        blob=data['blobs'][entry['blob_key']] if 'blob_key' in entry else entry
        b=blob['text'].encode() if 'text' in blob else base64.b64decode(blob['base64'])
        if len(b)!=entry['bytes'] or sha(b)!=entry['sha256']:raise ValueError('byte-preserved input hash '+key)
        return b
    for key in ('inventory.json','snapshot.json'):
        (out/key).write_bytes(raw(key))
    for name in private:
        if name.startswith(prefix+'snapshot/'):
            rel=name[len(prefix):];path=out/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw(rel))
    plan=json.loads(raw('plan.json'));plan=copy.deepcopy(plan);plan.update(status='fresh_reproduction_frozen_before_gates_and_E',prover_binary_sha256=sha(e.read_bytes()),prover_version=subprocess.run([str(e),'--version'],capture_output=True,text=True,check=True).stdout.strip(),original_plan_sha256=sha(raw('plan.json')),original_timing_not_reused=True,inputs=[])
    for kind in ('theory','library'):
        path=out/('left-successor-'+kind+'.p');path.write_bytes(raw(path.name));mp=path.with_suffix('.mapping.json');mp.write_bytes(raw(mp.name));m=load(mp)
        count=exact_input(path.read_text(),m)
        plan['inputs'].append(dict(kind=kind,path=str(path),input_sha256=sha(path.read_bytes()),mapping_sha256=sha(mp.read_bytes()),entries=count))
    dump(out/'plan.json',plan)
    def unchanged():
        for name,h in plan['source_sha256'].items():
            if sha((ROOT/name).read_bytes())!=h:raise ValueError('fresh source changed '+name)
        for entry in plan['inputs']:
            path=pathlib.Path(entry['path'])
            if sha(path.read_bytes())!=entry['input_sha256'] or sha(path.with_suffix('.mapping.json').read_bytes())!=entry['mapping_sha256']:raise ValueError('fresh exact input changed')
        if sha(e.read_bytes())!=plan['prover_binary_sha256']:raise ValueError('fresh binary changed')
        return plan
    focus.OUT=out;focus.unchanged=unchanged
    original.OUT=out;original.unchanged=unchanged;original.E=e;original.op=focus.operation
    auditor.OUT=out;auditor.unchanged=unchanged;auditor.op=focus.operation
    focus.fixtures()
    original.setup()
    auditor.before()
    original.run()
    auditor.after()
    audit=load(out/'audit.json')
    if audit['successful_checked_derivations']!=4:raise ValueError('reproduction target certificates remain unknown')
    result=dict(status='passed_fresh_first_order_reproduction',seconds=time.perf_counter()-began,plan_sha256=sha((out/'plan.json').read_bytes()),summary_sha256=sha((out/'summary.json').read_bytes()),audit_sha256=sha((out/'audit.json').read_bytes()),complete_interfaces=24,full_proofs=4,scope='Fresh complete source/input/interface and36 native-binding gates, all fixtures, balanced E searches and full returned-certificate replays. Native admission/audit records are authoritative reused evidence; no native tape replay is re-executed. Different binary creates a separately identified run.')
    dump(out/'reproduction.json',result);print('FRESH REPRODUCTION PASSED',result['seconds'],flush=True)

if __name__=='__main__':main()
