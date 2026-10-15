"""Metadata-only current Source5 plan preparation; no scientific functions."""
import ast
import hashlib
import json
from pathlib import Path
import sys

BASE=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
ROOT=BASE/'.gcts-active/atomic-family-donor-ROOT-20261015'
AUTHOR=BASE/'.gcts-active/atomic-family-donor-training-source-20261015'

def pin(path):
    path=Path(path).resolve();h=hashlib.sha256();n=0
    with path.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b);n+=len(b)
    return {'path':str(path),'sha256':h.hexdigest(),'bytes':n}

def save(name,value):
    p=ROOT/name
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    return pin(p)

def main(argv):
    if len(argv)!=1:raise ValueError('sole genuine peer review path')
    source=pin(AUTHOR/'atomic_donor_training_intake_v2.py')
    if (source['sha256'],source['bytes'])!=('065051bc9bb8df8ae95d2d737ddc11bdd051bf0788920c9b23e5788c6524ad67',62865):raise ValueError('exact whole reviewed worker')
    constants={}
    for node in ast.parse(Path(source['path']).read_bytes()).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:constants[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    sources=dict(constants['FIXED_SOURCES'],intake=source)
    contract=pin(AUTHOR/'Source-contract-v1.json')
    if (contract['sha256'],contract['bytes'])!=('70f2ea39ba4352dd79320ae7175cf03d92a883df8cbd5a0437528f05de32beca',16673):raise ValueError('current whole Source contract')
    for record in [*sources.values(),*constants['FIXED_INPUTS'].values(),constants['PROTOCOL'],constants['RUNTIME'],constants['FAMILY_CONTRACT'],constants['FAMILY_PEER']]:
        if pin(record['path'])!=record:raise ValueError('current whole raw metadata/input/Source/runtime')
    peerpin=pin(argv[0]);peer=json.loads(Path(argv[0]).read_bytes())
    if not(peer['scope']==constants['REVIEW_SCOPE'] and peer['source']==source and peer['source_contract']==contract
       and peer['sources']==sources and peer['source_only'] is True and peer['source_review_passed'] is True
       and peer['scientific_calls']==0 and peer['scientific_acceptance'] is False
       and peer['author_identity']==constants['AUTHOR'] and peer['reviewer_identity'] not in ('/root',constants['AUTHOR'])):raise ValueError('genuine whole current Source5 peer')
    review=save('ROOT-Source-review-v1.json',{'schema':'ROOT-atomic-family-donor-Source-review-v1',
        'author_identity':constants['AUTHOR'],'reviewer_identity':'/root','scope':constants['REVIEW_SCOPE'],
        'source_only':True,'source_review_passed':True,'scientific_calls':0,'scientific_acceptance':False,
        'source':source,'source_contract':contract,'sources':sources,
        'checks':['Whole selected756-line worker read; current sole-plan/Source5/input8 ABI and historical links inspected.',
        'Prior actual Root admission authenticates searched-origin provenance; small buffers bind full same donor/context/ordered references and exact old word certificate. No large Q paths followed.',
        'Existing e499 family/b32 adapter/1717 closed-target endpoint and4645 CodeSeal/projection/parser/writer scopes retained; no new inference or graph code.',
        'All Source modules loaded before guard capture; owned immediate callbacks/exceptional returns guarded; same global D projected without reset.',
        'Corrupt-origin and undeclared-axiom controls derive from actual donor; only exact specific ValueError messages count, guard/time failures remain UNKNOWN.',
        'Complete fresh closed-target donor check precedes miner all-root census; no expected eligible count or positive family supplied.',
        'Single fixed worker contains no descendant launch; captured native exit after full write. True terminal T and strict launch-postprobe20 plus512/60/90+1 remain external actual gates.',
        'Both math/recipient/library/native/point/RL/advantage flags remain false except completed donor recheck/mining at their narrow scope. Forward selected-fact receptor limitation and training costs disclosed.'],
        'limitations':'Fixed reviewed synchronous Sources/pinned Darwin ABI. Source-only readiness, not runtime, mining result, library soundness or hostile VM/OS protection.'})
    invocation='atomic-family-donor-training-20261015-v1'
    grant=save('ROOT-authorization-v1.json',{'schema':'ROOT-atomic-family-donor-training-authorization-v1',
        'author_identity':'/root','actual_execution_authorized':True,'invocation_id':invocation,'purpose':'admitted-donor-training',
        'source_bindings':sources,'inputs':constants['FIXED_INPUTS'],'resource_rule':'single-owned-process-native-terminal-v1',
        'protocol_choice':constants['PROTOCOL'],'limits':constants['LIMITS'],
        'scope':'One admitted searched word as training/debug data; fresh same original1717 closed-target check then donor/root census only. No recipient, activation, transfer or speed claim.'})
    plan=save('ROOT-plan-v1.json',{'schema':'ROOT-atomic-family-donor-training-plan-v1','invocation_id':invocation,
        'purpose':'admitted-donor-training','output_directory':str(ROOT/'training-owned-v1'),
        'resource_rule':'single-owned-process-native-terminal-v1','runtime':constants['RUNTIME'],'limits':constants['LIMITS'],
        'source_contract':contract,'sources':sources,'inputs':constants['FIXED_INPUTS'],'reviews':{'ROOT':review,'peer':peerpin},
        'protocol_choice':constants['PROTOCOL'],'family_contract':constants['FAMILY_CONTRACT'],
        'family_peer':constants['FAMILY_PEER'],'ROOT_authorization':grant})
    external=pin(BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py')
    meter=pin(BASE/'.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py')
    if external['sha256']!='9ded650bc257a7c5bb02388098f92803743d42f40629908b98f864a562289ef0' or meter['sha256']!='0129830110b8f46a1cfd376ced0cd147aa2f224665b4a0cce36ae82f2106d67e':raise ValueError('unchanged generic instruments')
    closure={'schema':'ROOT-atomic-family-donor-current-metadata-closure-v1','plan':plan,'external_driver':external,
        'native_meter':meter,'external_directory':str(ROOT/'training-external-v1'),'actual_started':False,
        'Source_functions_executed':0,'Q_decodes':0,
        'external_schema_note':'Byte-identical generic9ded measurement-only driver retains ordinary schema prefixes. Actual plan/purpose/Source5 and explicit single-process protocol define this donor-only experiment; no ordinary/point proof wire is counterfeited.'}
    save('ROOT-closure-v1.json',closure);print(json.dumps(closure,sort_keys=True))

if __name__=='__main__':main(sys.argv[1:])
