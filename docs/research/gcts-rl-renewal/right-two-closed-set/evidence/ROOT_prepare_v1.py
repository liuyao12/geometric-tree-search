"""Metadata-only exact current Source5 closure/grant/plan; no scientific imports."""
import hashlib
import json
from pathlib import Path
import sys

BASE=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
ROOT=Path(__file__).resolve().parent
AUTHOR=BASE/'.gcts-active/right-two-closed-set-intake-source-20261015'
def pin(path):
    p=Path(path).resolve();h=hashlib.sha256();n=0
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b);n+=len(b)
    return {'path':str(p),'sha256':h.hexdigest(),'bytes':n}
def save(name,value):
    p=ROOT/name
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
def main(peer_path):
    handoff=json.loads((AUTHOR/'handoff-v1.json').read_bytes())
    source,contract=handoff['source'],handoff['source_contract']
    if (source['sha256'],source['bytes'])!=('96e27192243fd6ce51fbe93461feeafdde2055be34f0623f8d4f47c6b20342dd',40960):raise ValueError('selected complete intakeV2')
    if (contract['sha256'],contract['bytes'])!=('9a9c72798dfb9d14a58ff537383908c6ef5709b5a4978bae03987a1f723fce27',11732):raise ValueError('selected current whole Source contract')
    capsule=json.loads(Path(contract['path']).read_bytes());sources,inputs=handoff['sources'],handoff['inputs']
    for ref in [source,contract,*sources.values(),*inputs.values(),*handoff['producer_sources'].values(),capsule['Root_protocol'],capsule['runtime'],capsule['module_contract'],capsule['module_peer'],capsule['author_static']]:
        if pin(ref['path'])!=ref:raise ValueError('whole current pin '+ref['path'])
    peer_ref=pin(peer_path);peer=json.loads(Path(peer_path).read_bytes())
    if not(peer['scope']==capsule['review_scope'] and peer['source']==source and peer['source_contract']==contract
        and peer['sources']==sources and peer['author_identity']=='/root' and peer['reviewer_identity']!='/root'
        and peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0
        and peer['scientific_acceptance'] is False):raise ValueError('genuine exact current whole Source5 peer')
    review=save('ROOT-Source-review-v1.json',{'schema':'right-two-finite-Horn-closed-set-intake-Source-review-v1',
        'scope':capsule['review_scope'],'source':source,'source_contract':contract,'sources':sources,
        'author_identity':'/root','reviewer_identity':'/root','source_only':True,'source_review_passed':True,
        'scientific_calls':0,'scientific_acceptance':False,'author_review_only':True,
        'checks':['Whole new generic checker and saturation modules read; closure soundness follows induction over original Horn recipes, with no expected target set or theorem route.',
            'Whole original cold intake/main pattern read;14 nonmain definitions AST exact. Parser whole raw auth/EOF and unconditional raw/text release preserved.',
            'Current Root independent catalogue admission, exact audit plan/result, original producerSource6 and declaration raw/value identities all bind this full preparation.',
            'Original private checker-owned view contains only tuples/strings/integers and is retained through producer call. No mutable catalogue/authority reaches generator; bounded candidate is isolated before original checker call.',
            'Full Source/caller boundaries bracket delegates; internal module tick is captured native resource guidance. Actual mutation controls check exact error categories, invoking caller in finally and a full boundary outside the catch.',
            'Whole3 outputs and2LF completion plus finalstdout/postoutput Source/native guards; one owned process/no children B=T, unchanged native20/512/55/60/90+1 and external instruments.',
            'All point/full24/trajectory/native Wang/positive theorem/arithmetic nonprovability/GCTS marking/RL/advantage remain outside this finite negative certificate scope.'],
        'limitations':'Fixed reviewed synchronous Sources/Darwin, not hostile VM/OS. Author plus genuine distinct Source review; no current actual result/resource fit or semantic replay from this metadata review.'})
    invocation='right-two-finite-Horn-closed-set-20261015-v1'
    grant=save('ROOT-authorization-v1.json',{'schema':'ROOT-right-two-finite-Horn-closed-set-authorization-v1',
        'author_identity':'/root','actual_execution_authorized':True,'invocation_id':invocation,'purpose':'right-two-finite-Horn-closed-set-certificate',
        'sources':sources,'inputs':inputs,'producer_sources':handoff['producer_sources'],'limits':capsule['limits'],'ROOT_protocol':capsule['Root_protocol']})
    plan=save('ROOT-plan-v1.json',{'schema':'ROOT-right-two-finite-Horn-closed-set-plan-v1','invocation_id':invocation,
        'purpose':'right-two-finite-Horn-closed-set-certificate','output_directory':str(ROOT/'closed-set-owned-v1'),
        'sources':sources,'inputs':inputs,'source_contract':contract,'reviews':{'ROOT':review,'peer':peer_ref},
        'ROOT_authorization':grant,'runtime':capsule['runtime'],'limits':capsule['limits'],
        'resource_rule':'single-owned-process-native-terminal-v1','producer_sources':handoff['producer_sources']})
    external=pin(BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py')
    meter=pin(BASE/'.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py')
    if external['sha256']!='9ded650bc257a7c5bb02388098f92803743d42f40629908b98f864a562289ef0' or meter['sha256']!='0129830110b8f46a1cfd376ced0cd147aa2f224665b4a0cce36ae82f2106d67e':raise ValueError('unchanged native instruments')
    closure={'schema':'ROOT-right-two-finite-Horn-closed-set-metadata-closure-v1','plan':plan,'external_driver':external,'native_meter':meter,
        'external_directory':str(ROOT/'closed-set-external-v1'),'actual_started':False,'scientific_calls':0,'Q_decodes':0,
        'scope':'Only generic current whole-graph closed-set generation/check/controls; no theorem route, no old negative promotion, no model or clock reset.'}
    save('ROOT-closure-v1.json',closure);print(json.dumps(closure,sort_keys=True))
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('sole genuine current whole-intake peer path')
    main(sys.argv[1])
