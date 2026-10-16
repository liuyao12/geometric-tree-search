"""Metadata-only fresh current whole-audit grant/plan; no Source execution."""
import hashlib
import json
from pathlib import Path
import sys

BASE=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
ROOT=Path(__file__).resolve().parent
AUTHOR=BASE/'.gcts-active/right-two-independent-audit-intake-source-20261015'

def pin(path):
    p=Path(path).resolve();h=hashlib.sha256();n=0
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b);n+=len(b)
    return {'path':str(p),'sha256':h.hexdigest(),'bytes':n}

def save(name,data):
    p=ROOT/name
    with p.open('x') as f:json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)

def main(peer_path):
    handoff=json.loads((AUTHOR/'handoff-v3.json').read_bytes());source=handoff['source'];contract=handoff['source_contract']
    if (source['sha256'],source['bytes'])!=('741d88d0d54b90aeadc6ad193d8906daa8a02eaa5ca5d63255997a358bb6683f',26854):raise ValueError('selected whole V3 intake')
    if (contract['sha256'],contract['bytes'])!=('1e0f89e92bfb7f3ae48fb83253d3a0722fac7114323777092df49cf0ee963a7a',8907):raise ValueError('selected current V3 contract')
    capsule=json.loads(Path(contract['path']).read_bytes());sources,inputs=handoff['sources'],handoff['inputs']
    for ref in [source,contract,*sources.values(),*inputs.values(),*handoff['producer_sources'].values(),capsule['Root_protocol'],capsule['runtime'],capsule['core_peer']]:
        if pin(ref['path'])!=ref:raise ValueError('whole current pin '+ref['path'])
    peer_ref=pin(peer_path);peer=json.loads(Path(peer_path).read_bytes())
    if not(peer['scope']==capsule['review_scope'] and peer['source']==source and peer['source_contract']==contract
        and peer['sources']==sources and peer['author_identity']=='/root' and peer['reviewer_identity']!='/root'
        and peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0
        and peer['scientific_acceptance'] is False):raise ValueError('genuine current V3 whole Source4 peer')
    review=save('ROOT-Source-review-v1.json',{'schema':'right-two-independent-audit-intake-Source-review-v1',
        'scope':capsule['review_scope'],'source':source,'source_contract':contract,'sources':sources,
        'author_identity':'/root','reviewer_identity':'/root','source_only':True,'source_review_passed':True,
        'scientific_calls':0,'scientific_acceptance':False,'author_review_only':True,
        'checks':['Whole original intake and all V2/V3 live-caller/storage modifications read; current source includes preserved original anchor/same/invoke helpers.',
            'Global ParseBudget methods are CodeSeal-covered; nested boundary/guard/tick and immediate delegated callers/final poststdout edge have original pre/post code/default/closure checks.',
            'One complete current raw prep auth before unchanged generic shared parser; raw buffer and decoded text explicitly dropped in proper main control flow. Old fixed codec decode never called.',
            'Fixed cf7c independent math core/declaration/current Source6, exact producer admission/output chain and whole24 state/oracle file comparisons. No producer mathematical module executes.',
            'One native original G/D and exact same-process deadline guidance; one owned process/B=T and full launch-to-postprobe20/512/60/90+1 external gates.',
            'Full independent result plus whole2LF response and actual terminal required; no proof/library/recipient/RL/native Wang claims. Unexecuted negative V1/V2 remain historical.'],
        'limitations':'Root author review plus distinct peer, fixed synchronous Sources and pinned ABI. No independent semantic replay or actual result from this Source review; not a hostile OS/VM claim.'})
    invocation='right-two-complete-independent-audit-20261015-v1'
    grant=save('ROOT-authorization-v1.json',{'schema':'ROOT-right-two-independent-audit-authorization-v1',
        'author_identity':'/root','actual_execution_authorized':True,'invocation_id':invocation,
        'purpose':'complete-right-two-independent-audit','sources':sources,'inputs':inputs,
        'producer_sources':handoff['producer_sources'],'limits':capsule['limits'],'ROOT_protocol':capsule['Root_protocol']})
    plan=save('ROOT-plan-v1.json',{'schema':'ROOT-right-two-independent-audit-plan-v1','invocation_id':invocation,
        'purpose':'complete-right-two-independent-audit','output_directory':str(ROOT/'audit-owned-v1'),
        'sources':sources,'inputs':inputs,'source_contract':contract,'reviews':{'ROOT':review,'peer':peer_ref},
        'ROOT_authorization':grant,'runtime':capsule['runtime'],'limits':capsule['limits'],
        'resource_rule':'single-owned-process-native-terminal-v1','producer_sources':handoff['producer_sources']})
    external=pin(BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py')
    meter=pin(BASE/'.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py')
    if external['sha256']!='9ded650bc257a7c5bb02388098f92803743d42f40629908b98f864a562289ef0' or meter['sha256']!='0129830110b8f46a1cfd376ced0cd147aa2f224665b4a0cce36ae82f2106d67e':raise ValueError('unchanged native instruments')
    closure={'schema':'ROOT-right-two-independent-audit-metadata-closure-v1','plan':plan,'external_driver':external,
        'native_meter':meter,'external_directory':str(ROOT/'audit-external-v1'),'actual_started':False,
        'scientific_calls':0,'Q_decodes':0,'scope':'Only current whole audit, no search, no old preparation/admission/clock reset.'}
    save('ROOT-closure-v1.json',closure);print(json.dumps(closure,sort_keys=True))

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('sole genuine current V3 whole-intake peer review path')
    main(sys.argv[1])
