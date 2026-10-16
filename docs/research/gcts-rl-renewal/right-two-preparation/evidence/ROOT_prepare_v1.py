"""Prepare one exact current metadata plan. No scientific Source imports."""
import hashlib
import json
from pathlib import Path
import sys

BASE=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
ROOT=Path(__file__).resolve().parent
AUTHOR=BASE/'.gcts-active/arithmetic-right-two-preparation-source-20261015'


def pin(path):
    p=Path(path).resolve();raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def save(name,data):
    p=ROOT/name
    with p.open('x') as f:json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    return pin(p)


def main(peer_path):
    handoff=json.loads((AUTHOR/'handoff-v1.json').read_bytes())
    source,contract=handoff['source'],handoff['source_contract']
    if (source['sha256'],source['bytes'])!=('c344d1f59b2b3b30f31b3899581889ba7e4e5268c308bc399320b6ba579fecdc',41739):raise ValueError('whole selected reviewed worker')
    if (contract['sha256'],contract['bytes'])!=('b60a18d370a6adc8df8c27d898cf4662bef032126a42ab3460b36fed82797527',15161):raise ValueError('whole selected Source contract')
    capsule=json.loads(Path(contract['path']).read_bytes())
    sources,inputs=handoff['sources'],handoff['inputs']
    protocol=pin(ROOT/'ROOT-protocol-choice-v1.json')
    if protocol['sha256']!='67b7f355eafdbe725b0013ce25f304130efc5b081eb796c975344655051cae64':raise ValueError('prospective Root protocol')
    for ref in [source,contract,*sources.values(),*inputs.values(),capsule['runtime'],handoff['Root_prospective_protocol']]:
        if pin(ref['path'])!=ref:raise ValueError('full current raw pin '+ref['path'])
    if capsule['sources']!=sources or capsule['inputs']!=inputs or sources['intake']!=source:raise ValueError('whole Source6/input2 map')
    peer_ref=pin(peer_path);peer=json.loads(Path(peer_path).read_bytes())
    if not(peer['scope']==capsule['Source_review_ABI']['scope'] and peer['source']==source
        and peer['source_contract']==contract and peer['sources']==sources and peer['source_only'] is True
        and peer['source_review_passed'] is True and peer['scientific_calls']==0
        and peer['scientific_acceptance'] is False and peer['author_identity']==handoff['author_identity']
        and peer['reviewer_identity'] not in ('/root',handoff['author_identity'])):raise ValueError('genuine distinct current whole Source peer')
    review=save('ROOT-Source-review-v1.json',{'schema':'Q-right-two-complete-preparation-Source-review-v1',
        'scope':peer['scope'],'source':source,'source_contract':contract,'sources':sources,
        'author_identity':handoff['author_identity'],'reviewer_identity':'/root','source_only':True,
        'source_review_passed':True,'scientific_calls':0,'scientific_acceptance':False,
        'checks':['Whole567line current worker read; sole canonical plan12/Source6/input2/currentgrant and distinctreview ABI inspected.',
            'Same source buffers authenticated whole and compiled into registered private modules; existing CodeSeal and full immediate pre/post delegate guards reused.',
            'Unchanged kernel/compiler/all24 point model and literal domain streams, no proof/lemma/route/backcone/search supplied. Honest new Source6 in authority/model.',
            'One original native G/D, existing conservative local guidance only; no children. B=T and strict full launch-through-postprobe20 external gates remain mandatory.',
            'All initial state/oracle/catalogue data streamed full with original ceilings/EOF pins; no trimming/count constants. Fresh model epoch and separate smallsummary.',
            'Original catalogue text(result) allocation and fixed-term grammar gap retained and disclosed. Producer comparisons are not independent mathematical admission.',
            'Current whole profile audit successor required before newmodel qualification; old1717 remains originaltargetonly. No proof/fullboard/nativeWang/RL claim.'],
        'limitations':'Fixed reviewed synchronous Source and pinned Darwin ABI; no fit or runtime acceptance from review and no hostile OS/VM guarantee.'})
    invocation='Q-right-two-complete-preparation-20261015-v1'
    grant=save('ROOT-authorization-v1.json',{'schema':'ROOT-Q-right-two-preparation-authorization-v1',
        'author_identity':'/root','actual_execution_authorized':True,'invocation_id':invocation,
        'purpose':'complete-right-two-preparation','sources':sources,'inputs':inputs,
        'limits':capsule['limits'],'resource_rule':capsule['resource_rule'],'ROOT_protocol':protocol})
    plan=save('ROOT-plan-v1.json',{'schema':'ROOT-Q-right-two-preparation-plan-v1','invocation_id':invocation,
        'purpose':'complete-right-two-preparation','output_directory':str(ROOT/'preparation-owned-v1'),
        'sources':sources,'inputs':inputs,'source_contract':contract,'reviews':{'ROOT':review,'peer':peer_ref},
        'ROOT_authorization':grant,'runtime':capsule['runtime'],'limits':capsule['limits'],'resource_rule':capsule['resource_rule']})
    external=pin(BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py')
    meter=pin(BASE/'.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py')
    if external['sha256']!='9ded650bc257a7c5bb02388098f92803743d42f40629908b98f864a562289ef0' or meter['sha256']!='0129830110b8f46a1cfd376ced0cd147aa2f224665b4a0cce36ae82f2106d67e':raise ValueError('unchanged native measurement instruments')
    closure={'schema':'ROOT-current-right-two-preparation-metadata-closure-v1','plan':plan,'external_driver':external,
        'native_meter':meter,'external_directory':str(ROOT/'preparation-external-v1'),'actual_started':False,
        'scientific_calls':0,'Q_decodes':0,'measurement_schema_note':'Byte-identical external9ded retains ordinary prefixes; exact new plan/purpose/Source6 defines preparation stage, no proof response counterfeited.'}
    save('ROOT-closure-v1.json',closure)
    print(json.dumps(closure,sort_keys=True))


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('sole genuine current peer Source review path')
    main(sys.argv[1])
