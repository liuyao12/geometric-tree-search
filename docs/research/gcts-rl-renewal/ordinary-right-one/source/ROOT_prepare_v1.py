"""Metadata-only frozen-plan preparation. Never executes project Source."""
import ast
import hashlib
import json
from pathlib import Path
import sys

BASE = Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
ROOT = BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015'
LEAVES = BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-cold-source-20261015'


def pin(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    count = 0
    with path.open('rb') as stream:
        while True:
            block = stream.read(65536)
            if not block:
                break
            h.update(block)
            count += len(block)
    return {'path':str(path),'sha256':h.hexdigest(),'bytes':count}


def save(name, value):
    path = ROOT/name
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False)
        stream.write('\n')
    return pin(path)


def main(argv):
    if len(argv) != 2 or argv[0] not in ('controls','primary'):
        raise ValueError('purpose and genuine peer review path')
    purpose, peer_path = argv
    intake = LEAVES/'Q_ordinary_cold_intake_v1.py'
    own = pin(intake)
    if (own['sha256'],own['bytes']) != ('57e2c28233996e4eafc0d19ea0fe9af7eac79c6356174b04f37cf979615c2a47',39108):
        raise ValueError('exact reviewed frozen intake')
    constants = {}
    for node in ast.parse(intake.read_bytes()).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError,TypeError):
                pass
    old = json.loads((BASE/'.gcts-active/arithmetic-Q-census-batch64-cold-progress-20261015/ROOT-plan-v1.json').read_bytes())
    sources = {
        'intake':own,
        'producer_bootstrap':pin(LEAVES/'Q_ordinary_producer_bootstrap_v1.py'),
        'clean_checker':pin(LEAVES/'Q_ordinary_clean_checker_v2.py'),
        'control_leaf':pin(LEAVES/'Q_ordinary_control_leaf_v1.py'),
        'codec':pin(BASE/'.gcts-active/arithmetic-Q-untrusted-preparation-codec-source-20261014/Q_untrusted_lossless_preparation_codec_v1.py'),
        'ordinary_producer':pin(BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-control-source-20261015/Q_ordinary_first_ready_saturation_v1.py'),
        'ordinary_adapter':pin(BASE/'.gcts-active/arithmetic-Q-ordinary-first-ready-control-source-20261015/Q_ordinary_first_ready_word_adapter_v1.py'),
        'independent_checker':pin(BASE/'.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py'),
        'checker_support':pin(BASE/'.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py')}
    for role, expected in constants['SOURCE_PINS'].items():
        if {k:sources[role][k] for k in ('sha256','bytes')} != expected:
            raise ValueError('unchanged Source '+role)
    for role,record in old['inputs'].items():
        if pin(record['path']) != record or {k:record[k] for k in ('sha256','bytes')} != constants['RAW_INPUT_BINDINGS'][role]:
            raise ValueError('whole original input '+role)
    for role,record in old['original_sources'].items():
        if pin(record['path']) != record:
            raise ValueError('whole original Source '+role)
    if old['original_sources'] != constants['ORIGINAL_SOURCES'] or pin(old['runtime']['path']) != constants['RUNTIME']:
        raise ValueError('unchanged original provenance/runtime')
    peer = json.loads(Path(peer_path).read_bytes())
    if not (peer['source_only'] is True and peer['source_review_passed'] is True and peer['scientific_calls']==0
            and peer['reviewer_identity'] not in ('/root','/root/arithmetic_induction') and peer['sources']==sources):
        raise ValueError('genuine current peer review')
    root_review_path = ROOT/'ROOT-Source-review-v1.json'
    if purpose == 'controls':
        root_review = {'schema':'ROOT-ordinary-Q-Source-review-v1','source_only':True,
            'source_review_passed':True,'scientific_calls':0,'author_identity':'/root/arithmetic_induction',
            'reviewer_identity':'/root','scope':'Q-ordinary-first-ready-cold-intake-Source','sources':sources,
            'checks':[
                'Whole new parent and all new leaves read; selected exact support FD/JSON/CodeSeal/writer helpers read.',
                'Unchanged860 full first-ready saturation and e65 adapter read, with1717 whole word semantics and codec.',
                'Root path-bearing pin rejection fixed before freeze, exact configured path plus same-buffer digest retained.',
                'Complete original catalogue retained; no supplied proof/prefix/backcone/lemma/rank/RL; point BASE never receives result.',
                'Fresh checker process uses unchanged1717 exact original closed target/emptyGamma, ordered MP and unary generalization.',
                'Producer then checker lifetimes close by exact native wait4, no concurrent leaves or observer children.',
                'SELF cut only after all reaped; seal blocks actual launch; no-spawn tail writes and captured native os._exit.',
                'Prospective resource bound max(SELF_cut+max(serial leaf peaks),external true terminal T), no subtraction.',
                'Finite diagnostic floats preserved only in response metadata; semantic inputs strict integer data.',
                'Negative word/authority, real reaping, valid-args sealed launch denial and resident parent-tail controls precede target.',
                'Same20/55/60/512MiB/90+1 limits, including external native launch-to-postprobe<=20s.',
                'Source review is not actual conformance, logical acceptance, resource acceptance or a promotion of old UNKNOWNs.'],
            'scope_assumptions':'Pinned Darwin25.5.0/Python3.9.6, fixed reviewed nonhostile leaf Sources; no arbitrary OS/VM integrity claim.'}
        save(root_review_path.name,root_review)
    else:
        controls = json.loads((ROOT/'ROOT-controls-disposition-v1.json').read_bytes())
        if controls.get('controls_accepted') is not True:
            raise ValueError('genuine previous actual controls must be admitted')
        if json.loads(root_review_path.read_bytes())['sources'] != sources:
            raise ValueError('same reviewed Source for primary')
    invocation = 'ordinary-Q-'+purpose+'-20261015-v1'
    grant = {'schema':'ROOT-ordinary-Q-cold-authorization-v1','author_identity':'/root',
        'actual_execution_authorized':True,'purpose':purpose,'invocation_id':invocation,
        'limits':constants['LIMITS'],'source_bindings':{r:{k:p[k] for k in ('sha256','bytes')} for r,p in sources.items()},
        'binding':constants['BINDING'],'resource_rule':'ordinary-sequential-cutoff-max-v1',
        'point_BASE_receives_ordinary_output':False,
        'scope':'Once-only original ordinary control; no mathematical authority in producer and no point trajectory/full24/RL claim.'}
    grantpin = save('ROOT-'+purpose+'-authorization-v1.json',grant)
    plan = {'schema':'ROOT-ordinary-Q-cold-plan-v1','purpose':purpose,'invocation_id':invocation,
        'output_directory':str(ROOT/(purpose+'-owned-v1')),'sources':sources,'inputs':old['inputs'],
        'original_sources':old['original_sources'],'runtime':constants['RUNTIME'],'limits':constants['LIMITS'],
        'authorization':grantpin,'source_reviews':{'ROOT':pin(root_review_path),'peer':pin(peer_path)},
        'protocol_choice':pin(ROOT/'ROOT-protocol-choice-v1.json')}
    planpin = save('ROOT-'+purpose+'-plan-v1.json',plan)
    closure = {'schema':'ROOT-ordinary-Q-actual-metadata-closure-v1','purpose':purpose,'plan':planpin,
        'external_driver':pin(ROOT/'ROOT_external_once_v1.py'),
        'native_meter':pin(BASE/'.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py'),
        'external_directory':str(ROOT/(purpose+'-external-v1')),'source_functions_executed':0,
        'Q_decodes':0,'actual_started':False}
    save('ROOT-'+purpose+'-closure-v1.json',closure)
    print(json.dumps(closure,sort_keys=True))


if __name__=='__main__':
    main(sys.argv[1:])
