"""ROOT metadata-only stage freezing; no project imports or scientific calls."""
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'.gcts-active/guard-native-bridge-source-20261012'
PYTHON='/Library/Developer/CommandLineTools/usr/bin/python3'

def need(v,label):
    if not v: raise ValueError(label)

def read(path): return json.loads(Path(path).read_bytes())

def pin(path):
    p=Path(path); p=p if p.is_absolute() else ROOT/p
    h=hashlib.sha256(); size=0
    with p.open('rb') as stream:
        for b in iter(lambda:stream.read(65536),b''): h.update(b); size+=len(b)
    try: name=str(p.relative_to(ROOT))
    except ValueError: name=str(p)
    return dict(path=name,sha256=h.hexdigest(),bytes=size)

def main():
    need(len(sys.argv)==2 and sys.argv[1] in ('preparation','native','replay'),'one stage')
    mode=sys.argv[1]; review_path=HERE/'ROOT-source-review-v1.json'; review=read(review_path)
    need(review['source_review_passed'] is True and review['scientific_calls']==0,'source review completed')
    contract=read(SOURCE/'preparation-input-contract-v1.json')
    closure={a['path']:a for a in contract['closure']}
    def add(path):
        a=pin(path)
        need(a['path'] not in closure or closure[a['path']]==a,'unchanged source closure')
        closure[a['path']]=a
        return a
    for path in (SOURCE/'preparation-input-contract-v1.json',HERE/'run_owned_bridge_v1.py',
                 HERE/'native_bridge_worker_v1.py',HERE/'freeze_stage_plan_v1.py',review_path,
                 ROOT/'research/gcts-rl-renewal/boundary_oracle.cpp',
                 ROOT/'research/gcts-rl-renewal/audit_boundary_micro.cpp','/bin/ps',PYTHON,
                 '/usr/bin/clang++'):
        add(path)
    for a in review['source_records']+review['independent_reviews']:
        need(pin(a['path'])==a,'exact prior reviewed source/metadata bytes')
        closure[a['path']]=a
    request_path=HERE/'translation-v1/native-request-v1.json'; translation_path=HERE/'translation-v1/translation-receipt-v1.json'
    plan=dict(schema='ROOT-guard-native-owned-plan-v1',stage=mode,
        worker=str((SOURCE/'prepare_native_input_v1.py' if mode=='preparation' else HERE/'native_bridge_worker_v1.py').relative_to(ROOT)),
        runtime_binary=pin(PYTHON),output_directory=str((HERE/(mode+'-v1')).relative_to(ROOT)),
        worker_receipt=str((HERE/(mode+'-v1')/('preparation-result-v1.json' if mode=='preparation' else 'worker-result-v1.json')).relative_to(ROOT)),
        limits=dict(whole_seconds=60 if mode=='preparation' else 900,caller_seconds=90 if mode=='preparation' else 930,
                    peak_bytes=805306368),
        source_review=pin(review_path),target_searches=0,new_RL_training=False,
        all_five_qualification=False,universal_compiler_theorem=False,finite_Wang_rectangle_accepted=False)
    if mode=='preparation':
        plan['argv']=[PYTHON,'-B',str(SOURCE/'prepare_native_input_v1.py'),'ROOT-prepare-only',
            str(request_path),str(translation_path),str(HERE/'preparation-v1')]
    else:
        prep=HERE/'preparation-v1/preparation-result-v1.json'
        admission=HERE/'preparation-ROOT-final-decision-v1.json'
        result=read(prep); decision=read(admission)
        need(decision['ROOT_final_accepted'] is True and decision['native_queries']==0,'actual preparation admitted')
        need(result['stage_completed'] is True and result['all_input_and_microcode_bytes_equal'] is True,'whole byte preparation')
        a=result['artifacts']
        for record in [pin(prep),pin(admission),*[a[k]['file'] for k in ('frame','input','microcode')]]:
            need(pin(record['path'])==record,'exact prepared immutable bytes')
            closure[record['path']]=record
        plan.update(preparation_receipt=str(prep.relative_to(ROOT)),preparation_ROOT_decision=str(admission.relative_to(ROOT)),
            frame=a['frame']['file']['path'],input=a['input']['file']['path'],code=a['microcode']['file']['path'],
            microcode=contract['microcode_json']['path'],
            request_sha256=read(translation_path)['native_request_sha256'],
            input_bytes_sha256=a['input']['raw_sha256'],micro_code_bytes_sha256=a['microcode']['raw_sha256'],
            program_sha256='877c47879b027b08f02d3923d1e6dd9ccaf9a12e354567109f1aaa640a8fb673',
            micro_sha256='2f9e430b0b7034ed615d81c3e9b3978dc47ba4136686227a9b86df5779b203ac',
            parser_start=88986,compiler='/usr/bin/clang++',
            interpreter_source='research/gcts-rl-renewal/'+('boundary_oracle.cpp' if mode=='native' else 'audit_boundary_micro.cpp'))
        plan['limits']['micro_steps']=80000000000
        plan['argv']=[PYTHON,'-B',str(HERE/'native_bridge_worker_v1.py'),str(HERE/(mode+'-plan-v1.json'))]
        if mode=='replay':
            producer=HERE/'native-v1/worker-result-v1.json'; native_admission=HERE/'native-ROOT-final-decision-v1.json'
            native=read(producer); admitted=read(native_admission)
            need(admitted['ROOT_final_accepted'] is True and native['stage_completed'] is True,'whole native stage admitted')
            output=ROOT/native['output_file']['path']
            for p in (producer,native_admission,output): add(p)
            plan.update(producer_receipt=str(producer.relative_to(ROOT)),producer_ROOT_decision=str(native_admission.relative_to(ROOT)),
                        producer_output=str(output.relative_to(ROOT)))
    plan['closure']=list(closure.values())
    for a in plan['closure']: need(pin(a['path'])==a,'all prospective closure verified')
    path=HERE/(mode+'-plan-v1.json')
    need(not path.exists() and not (ROOT/plan['output_directory']).exists(),'one fresh frozen plan/worker attempt')
    with path.open('x') as stream: json.dump(plan,stream,indent=2); stream.write('\n')
    print(json.dumps(dict(plan=pin(path),stage=mode,closure=len(plan['closure']),limits=plan['limits'],scientific_calls=0)),flush=True)

if __name__=='__main__': main()
