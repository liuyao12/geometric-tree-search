"""Metadata-only preparation; no scientific Source functions or Q decoding."""
import ast
import hashlib
import json
from pathlib import Path
import sys

BASE=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
ROOT=BASE/'.gcts-active/arithmetic-Q-compact-point-ROOT-20261015'
SOURCES=BASE/'.gcts-active/arithmetic-Q-compact-point-cold-source-20261015'


def pin(path):
    path=Path(path).resolve();h=hashlib.sha256();size=0
    with path.open('rb') as stream:
        while True:
            block=stream.read(65536)
            if not block:break
            h.update(block);size+=len(block)
    return {'path':str(path),'sha256':h.hexdigest(),'bytes':size}


def save(name,value):
    path=ROOT/name
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')
    return pin(path)


def main(argv):
    if len(argv)!=2 or argv[0] not in ('controls','primary'):raise ValueError('purpose and genuine peer review path')
    purpose,peerpath=argv
    intake=SOURCES/'Q_point_compact_cold_intake_v1.py'
    actual=pin(intake)
    if (actual['sha256'],actual['bytes'])!=('30bef873644dda63102fb08d32b23d42a3082d3744ce1608535fa18e11171c79',42845):
        raise ValueError('exact reviewed immutable intake')
    constants={}
    for node in ast.parse(intake.read_bytes()).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:constants[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    old=json.loads((BASE/'.gcts-active/arithmetic-Q-census-batch64-cold-progress-20261015/ROOT-plan-v1.json').read_bytes())
    sources={'intake':actual,
        'producer_bootstrap':pin(SOURCES/'Q_point_compact_producer_bootstrap_v1.py'),
        'point_producer':pin(BASE/'.gcts-active/arithmetic-Q-compact-point-producer-source-20261015/Q_untrusted_compact_candidate_search_v4.py'),
        'codec':pin(BASE/'.gcts-active/arithmetic-Q-untrusted-preparation-codec-source-20261014/Q_untrusted_lossless_preparation_codec_v1.py'),
        'point_graph':pin(BASE/'.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py'),
        'verifier':pin(BASE/'.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py'),
        'independent_checker':pin(BASE/'.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py'),
        'control_leaf':pin(BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-cold-source-20261015/Q_ordinary_control_leaf_v1.py')}
    for role,expected in constants['SOURCE_PINS'].items():
        if {k:sources[role][k] for k in ('sha256','bytes')}!=expected:raise ValueError('complete Source '+role)
    for role,record in old['inputs'].items():
        if pin(record['path'])!=record or {k:record[k] for k in ('sha256','bytes')}!=constants['RAW_INPUT_BINDINGS'][role]:raise ValueError('original input '+role)
    for role,record in old['original_sources'].items():
        if pin(record['path'])!=record:raise ValueError('original Source '+role)
    if old['original_sources']!=constants['ORIGINAL_SOURCES'] or pin(old['runtime']['path'])!=constants['RUNTIME']:raise ValueError('original runtime/provenance')
    peer=json.loads(Path(peerpath).read_bytes())
    if not (peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0
            and peer['reviewer_identity'] not in ('/root','/root/arithmetic_induction') and peer['sources']==sources):raise ValueError('genuine current Source8 peer review')
    reviewpath=ROOT/'ROOT-Source-review-v1.json'
    if purpose=='controls':
        save(reviewpath.name,{'schema':'ROOT-point-compact-Q-Source-review-v1','source_only':True,
            'source_review_passed':True,'scientific_calls':0,'author_identity':'/root/arithmetic_induction',
            'reviewer_identity':'/root','scope':'Q-point-compact-cold-intake-Source','sources':sources,
            'checks':['Whole current point parent changes/bootstrap read;21 inherited parent helper ASTs exact to reviewed57e2.',
                'Whole compact3 producer read; exact4 successor adds only telemetry/version/schema, not graph/search/fingerprint rules.',
                'Full unchanged8d22 point graph and selected unchanged verifier4 MAIN/1717 word endpoint read.',
                'Original24 rows/complete catalogue/epochs,128attempts/2000events/max1 canonical unadvised fallback retained.',
                'Global dead precedes complete target ancestry, canonical candidate order and exact producer rollback fingerprints retained.',
                'Typed complete fingerprint covers all semantic state/domain/trail data; only producer claim, no independent trajectory promotion.',
                'Source8 runtime ledger distinct from verifier authority5; correct Source4 bootstrap imports/registration and CLI10 channels.',
                'Falseword complete WORD_REJECTED and corrupt-authority exact native exit2/stderr/emptywire are distinct controls.',
                'Same native serial true-wait4/no-future-spawn cut/parent-only exit tail; max(SELF_cut+max leaf peaks,T), no subtraction.',
                'Native launch-to-postprobe<=20, original20/55/60/512/90+1 and full output closure remain final actual gates.',
                'No ordinary successful word/prefix/backcone/library/rank/RL reaches point BASE; old UNKNOWNs unchanged.'],
            'limitations':'Fixed reviewed pinned Sources and Darwin ABI; Source-only readiness, not runtime, proof or GCTS advantage.'})
    else:
        controls=json.loads((ROOT/'ROOT-controls-disposition-v1.json').read_bytes())
        if controls.get('controls_accepted') is not True:raise ValueError('genuine actual controls required')
        if json.loads(reviewpath.read_bytes())['sources']!=sources:raise ValueError('same reviewed Source8 for primary')
    invocation='point-compact-Q-'+purpose+'-20261015-v1'
    grant=save('ROOT-'+purpose+'-authorization-v1.json',{'schema':'ROOT-point-compact-Q-cold-authorization-v1',
        'author_identity':'/root','actual_execution_authorized':True,'purpose':purpose,'invocation_id':invocation,
        'limits':constants['LIMITS'],'binding':constants['BINDING'],
        'source_bindings':{r:{k:p[k] for k in ('sha256','bytes')} for r,p in sources.items()},
        'resource_rule':'point-sequential-cutoff-max-v1','point_BASE_receives_ordinary_output':False,
        'scope':'Once only unchanged full-model canonical point baseline. Producer origins/fingerprints untrusted; fresh1717 word check only mathematical endpoint.'})
    plan=save('ROOT-'+purpose+'-plan-v1.json',{'schema':'ROOT-point-compact-Q-cold-plan-v1','purpose':purpose,
        'invocation_id':invocation,'output_directory':str(ROOT/(purpose+'-owned-v1')),'sources':sources,
        'inputs':old['inputs'],'original_sources':old['original_sources'],'runtime':constants['RUNTIME'],
        'limits':constants['LIMITS'],'authorization':grant,'source_reviews':{'ROOT':pin(reviewpath),'peer':pin(peerpath)},
        'protocol_choice':pin(ROOT/'ROOT-protocol-choice-v1.json')})
    external=pin(BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py')
    if (external['sha256'],external['bytes'])!=('9ded650bc257a7c5bb02388098f92803743d42f40629908b98f864a562289ef0',4357):raise ValueError('same generic external instrument')
    closure={'schema':'ROOT-point-compact-Q-actual-metadata-closure-v1','purpose':purpose,'plan':plan,
        'external_driver':external,'native_meter':pin(BASE/'.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py'),
        'external_directory':str(ROOT/(purpose+'-external-v1')),'Source_functions_executed':0,'Q_decodes':0,
        'external_schema_note':'Byte-identical generic9ded driver retains inherited ordinary measurement-only schema; point purpose/plan/Source8 and Root protocol control this new experiment.',
        'actual_started':False}
    save('ROOT-'+purpose+'-closure-v1.json',closure);print(json.dumps(closure,sort_keys=True))


if __name__=='__main__':main(sys.argv[1:])
