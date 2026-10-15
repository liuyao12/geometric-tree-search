"""UNEXECUTED Root metadata-only constructor proposal. No project imports/calls.

Root alone may invoke this after genuine distinct integration Source review.
The resulting request12 targets unchanged worker5/launcher5 Sources. This helper
never creates the controls-output-v1 directory and does not activate a worker.
Original Q payloads are streamed/hash-only, never JSON-decoded.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
VERSION='Q-full52-Root-metadata-author-builder-Source-v1'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
INTEGRATION_SCOPE='Q-full52-metadata-native-meter-integration-Source'
WORKER = {'bytes': 75494,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/Q_split_neutral_cold_worker_global_clock_v5.py',
 'sha256': '7c0ae6343cec47c28af8f452c5d56839dbf9a627e2d1a4b4933c7cb7ae61e957'}
LAUNCHER = {'bytes': 9204,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/Q_neutral_controls_early_launcher_global_clock_v5.py',
 'sha256': '3ddfadf1120dbc9ca03b0f718a4956d0cf93d10dabca5dd981122a3761d2bcf3'}
COMMON_CONTRACT = {'bytes': 25425,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/worker-launcher-Source-contract-v2.json',
 'sha256': 'e5e315f18c2a8356f3cd8004b2be0d1d9c46642f86bc03f9edf151c3862b2f05'}
SOURCES = {'census_leaf': {'bytes': 20215,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/Q_neutral_full_model_census_leaf_v2.py',
                 'sha256': 'bb30787adbeee4d479bbcad254eedcd02ed354135199524bd96103501f40aca6'},
 'codec': {'bytes': 5806,
           'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-untrusted-preparation-codec-source-20261014/Q_untrusted_lossless_preparation_codec_v1.py',
           'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df'},
 'coordinator': {'bytes': 54630,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-coordinator-source-20261015/Q_split_owned_coordinator_v6.py',
                 'sha256': 'dafc392dc1463cac98d36dcb8e74d164cc2aa91cb04e64ac7b9f7f304c001fab'},
 'disposable_leaf': {'bytes': 2985,
                     'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-controls-source-20261014/Q_neutral_calibration_leaf_v1.py',
                     'sha256': '8c88dabb29c1e5e5b7af0bceddc37173ac03fd6de86e89604cf10a406bb5e190'},
 'independent_checker': {'bytes': 46514,
                         'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py',
                         'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'},
 'owned_adapter': {'bytes': 26071,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/Q_owned_neutral_controls_adapter_v4.py',
                   'sha256': '768e6ef7c9386b92bc7330f6ca96766ccdaaa560c1c38b809efa7be3308f1ca1'},
 'point_adapter': {'bytes': 22217,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/Q_neutral_point_scheduler_adapter_v2.py',
                   'sha256': '0e38a1ee5e3b2a55beaf2fbae5c461e3b5f6bc2530d2bb375cd22573ee9379bb'},
 'point_graph': {'bytes': 28531,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py',
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'producer': {'bytes': 20219,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-untrusted-candidate-producer-source-20261014/Q_untrusted_candidate_search_v2.py',
              'sha256': '994b1ff8f3edf2621826f64fe7d974dee9041fa211e1990d76362268eb607f36'},
 'profile_leaf': {'bytes': 6704,
                  'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/Q_control_verifier_profile_leaf_v2.py',
                  'sha256': '6ba72fc11295e8972b356fd433f5990bc39723eb166001f374c795933cffbdd9'},
 'protocol_adapter': {'bytes': 76516,
                      'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-C-source-20261015/Q_clean_verifier_protocol_controls_adapter_global_clock_v5.py',
                      'sha256': '77c48f0ffac17faf40ec5cbbb7f5011a00cd6cac3d7236c42546e851415b4cc1'},
 'runner': {'bytes': 38113,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_split_neutral_controls_runner_global_clock_v3.py',
            'sha256': 'b64e50d800e74c4c0622f78c153a7a7d058c9036d351af1dfa030e4075d65590'},
 'verifier': {'bytes': 48584,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py',
              'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}}
INPUTS = {'architecture_choice': {'bytes': 6808,
                         'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-search-verifier-architecture-design-source-20261014/ROOT-architecture-choice-v1.json',
                         'sha256': '62b0d66686f890c9f604192058bdba48a4b171e233f25767b1e1de88fffbd82f'},
 'declaration': {'bytes': 2683,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/Q-declaration-v1.json',
                 'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc'},
 'finite_ROOT_admission': {'bytes': 8563,
                           'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-audit-shared-wire-progress-20261014/ROOT-actual-independent-Q-shared-wire-audit-reconciled-disposition-v2.json',
                           'sha256': '80dee8b9ec1bca398c24d61c10a026a82f73c8886cdeeb0ed9bf9ea5cf9c1ff1'},
 'finite_certificate': {'bytes': 5789,
                        'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-audit-shared-wire-progress-20261014/worker-output-v1/Q-independent-audit-certificate-provisional-v1.json',
                        'sha256': '3c3aefa4ff9d918a43a8b73d94fd6cebf0741e6203e0d47f3a44fbd716c7bc87'},
 'fixtures': {'bytes': 62584,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-search-verifier-controls-design-source-20261014/complete-fixtures-design-v2.json',
              'sha256': '1420cd2c0a56d09e629ca65fe4b7f690570ccb283b1998762c10de1190180575'},
 'initial_oracle': {'bytes': 8295473,
                    'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-initial-oracle-domains-v2.json',
                    'sha256': '03c42ca0083d5e40363d5237d69af56df4ebe3b3ae7d88fa3720fae3390d6969'},
 'initial_state': {'bytes': 8296118,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-initial-state-witness-v2.json',
                   'sha256': 'c7e8cfd099b1b80ae170b6c35591d68d56f37aecb38f1bcf7b567d2e019acbb9'},
 'preparation': {'bytes': 38376960,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-preparation-provisional-v1.json',
                 'sha256': '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a'},
 'word_controls_ROOT': {'bytes': 6796,
                        'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-word-controls-progress-20261014/ROOT-actual-unrelated-word-controls-reconciled-disposition-v1.json',
                        'sha256': 'f254219dc8e7324a7d15f9ff50661de627d207eca08660bca354e73978d39fd1'}}
ORIGINAL_SOURCES = {'catalogue': {'bytes': 10187,
               'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_catalog_v1.py',
               'sha256': '2db11af0d7206afd4e1c10b53b97c16f98064c14fd1e57a9a2ca34c0a602348a'},
 'controls': {'bytes': 19742,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_v3.py',
              'sha256': '4e28fadd9c76ba6664e485fa2c5aa97beaa08639986b6d56aae50395b006e638'},
 'kernel': {'bytes': 10323,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py',
            'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'},
 'master': {'bytes': 21657,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md',
            'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'},
 'payload': {'bytes': 5435,
             'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/q_preparation_owned_graph_v3.py',
             'sha256': 'ee2088bf60709f6c0c5a78297841bd0684674369fa9d3c08119b96a59caa88ad'},
 'point_graph': {'bytes': 28531,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py',
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'worker': {'bytes': 37266,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_worker_v7.py',
            'sha256': '75d5d80701a0815d78e182a5cb7eb99412bff5b48a5b936a8850b625743de48d'}}
CONTRACTS = {'coordinator': {'bytes': 13518,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-coordinator-source-20261015/Source-contract-v6.json',
                 'sha256': '8d37f633a14a0a23f00ea3888c832137f291896d5ee00e079ffd1ac481861a5b'},
 'owned_adapter': {'bytes': 13058,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/profile-O8-Source-contract-v1.json',
                   'sha256': 'b569e8d1c5aca24b2db5e9a711871b1e7f88294ddff39335eb273a695601077c'},
 'point_adapter': {'bytes': 5927,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-source-20261015/M8-census-Source-contract-v1.json',
                   'sha256': '99e15e3bb34786e86496da815924954431bfa93f0aa9df5db49759cf92aec7c2'},
 'protocol_adapter': {'bytes': 7885,
                      'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-C-source-20261015/P15-Source-contract-v1.json',
                      'sha256': '01a00f3e2ccdfb46c6f4cc76b93a50d0ff7dbfed467a707b73e9bb13854f6abb'},
 'runner': {'bytes': 15495,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/runner-Source-contract-v1.json',
            'sha256': '01bf2a0b45a476b27442f5e87e015d50d4838cc5c8625fe3ba02cd3e68935bf0'}}
REVIEWS = {'coordinator': {'bytes': 2196,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-coordinator-controls-review-source-20261015/typed-Source-review-v1.json',
                 'sha256': '016e2d78db0e42ac1d86ef7e2234fe0f26b0a3d296caa3ad789cf1d6764a14a4'},
 'launcher': {'bytes': 10864,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-worker-independent-source-20261015/launcher-typed-Source-review-v2.json',
              'sha256': 'd059ad6d003911a9154735c72e89454e125b87d739f5d167ca31b06fb326b276'},
 'owned_adapter': {'bytes': 6327,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-profile-owned-independent-source-20261015/O8-typed-Source-review-v1.json',
                   'sha256': 'c818eeb4247053d151b6b14cb52aeb901377103eed3a2cfc67a9683639f474d8'},
 'point_adapter': {'bytes': 3037,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-B-ROOT-independent-source-20261015/point-adapter-typed-Source-review-v1.json',
                   'sha256': 'd166ab09e6af0d3a59a8348e674419ca96166e7e363efbbfb94166dd0472471a'},
 'protocol_adapter': {'bytes': 4338,
                      'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-protocol-ROOT-independent-source-20261015/typed-Source-review-v2.json',
                      'sha256': '5a7a7db6b4394d1eb623d5fee91e26ec521b56899d8d997e06b55a5dc35ab49c'},
 'runner': {'bytes': 3519,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-diagnosis-review-source-20261015/runner-typed-Source-review-v1.json',
            'sha256': 'cfb384d20404039f4b0e5cd3f7ee60fce8967a72ce5a751ad1c4924d73dc7c34'},
 'worker': {'bytes': 10855,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-worker-independent-source-20261015/worker-typed-Source-review-v2.json',
            'sha256': '7e6bda8f516e867336aad6cc9732978554856377de96bf310d20e295d3af0eb9'}}
SCOPES = {'coordinator': 'Q-split-owned-coordinator-Source',
 'launcher': 'Q-neutral-controls-early-clock-launcher-Source',
 'owned_adapter': 'Q-split-neutral-owned-model-role-deadline-adapter-Source',
 'point_adapter': 'Q-split-neutral-NONLOGICAL-point-scheduler-adapter-Source',
 'protocol_adapter': 'Q-split-neutral-hard-target-protocol-adapter-Source',
 'runner': 'Q-split-neutral-controls-callable-Source',
 'worker': 'Q-split-neutral-owned-controls-worker-Source'}
RUNTIME = {'bytes': 102352,
 'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',
 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'}
LIMITS = {'aggregate_owned_bytes': 536870912,
 'caller_finish_reserve_seconds': 1,
 'caller_seconds': 90,
 'failure_only_seconds': 55,
 'joint_seconds': 20,
 'owned_seconds': 60}
CLOCK_POLICY = {'bytes': 4443,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-runtime-clock-ABI-qualification-20261015/ROOT-global-clock-repair-choice-v1.json',
 'sha256': '2e526972409799e8874d10afdf0cb094ac4f6dc634b2fc0ffdaa2be789d172b4'}
OUTPUT_DIRECTORY = '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-neutral-controls-progress-20261014/controls-output-v1'
METER_SOURCE = {'bytes': 6734,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py',
 'sha256': '0129830110b8f46a1cfd376ced0cd147aa2f224665b4a0cce36ae82f2106d67e'}
EXTERNAL_JS = {'bytes': 7182,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-full52-integration-source-20261015/observe_actual_full52_launcher_v1.js',
 'sha256': '61da0d7361b37040a5599ede8a542d76130b90b5ec1a845a848bc83eef771a6e'}


def need(ok,message):
    if not ok:raise ValueError(message)


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def capsule(path):
    path=Path(path);need(path.is_absolute() and path==path.resolve() and not path.is_symlink(),'canonical exact raw path')
    with path.open('rb') as f:
        before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode),'whole regular metadata/raw file')
        h=hashlib.sha256();size=0
        while True:
            block=f.read(65536)
            if not block:break
            h.update(block);size+=len(block)
        after=os.fstat(f.fileno())
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns) and size==before.st_size,'whole stable EOF')
    return {'path':str(path),'sha256':h.hexdigest(),'bytes':size}


def verify(record):
    need(type(record) is dict and set(record)=={'path','sha256','bytes'} and type(record['bytes']) is int,'complete strict raw record')
    need(capsule(record['path'])==record,'exact whole raw pin')
    return record


def unique(pairs):
    out={}
    for k,v in pairs:
        need(k not in out,'duplicate metadata key');out[k]=v
    return out


def no_float(token):
    raise ValueError('no float/nonfinite metadata tokens')


def small(record):
    verify(record);need(record['bytes']<=1048576,'only named small metadata decoded')
    return json.loads(Path(record['path']).read_bytes().decode('utf8','strict'),object_pairs_hook=unique,
        parse_float=no_float,parse_constant=no_float)


def write(path,value):
    raw=canonical(value)+b'\n';fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
    try:
        offset=0
        while offset<len(raw):
            n=os.write(fd,raw[offset:]);need(n>0,'whole metadata write');offset+=n
    finally:os.close(fd)
    return capsule(path)


def main(argv):
    need(len(argv)==1,'one Root metadata-author request path, never a runtime plan argument')
    spec_pin=capsule(argv[0]);spec=small(spec_pin)
    need(type(spec) is dict and set(spec)=={'schema','author_identity','invocation_id','integration_review','prior_isolated_qualification'}
         and spec['schema']=='ROOT-Q-full52-metadata-authoring-request-v1' and spec['author_identity']=='/root','genuine Root-authored metadata request5')
    nonce=spec['invocation_id'];need(type(nonce) is str and 1<=len(nonce)<=128 and nonce.isascii(),'Root opaque bounded invocation')
    own=capsule(Path(__file__).resolve());integration_review=small(spec['integration_review'])
    need(integration_review.get('source')==own and integration_review.get('scope')==INTEGRATION_SCOPE
         and integration_review.get('source_only') is True and integration_review.get('source_review_passed') is True
         and integration_review.get('all_checks_passed') is True and type(integration_review.get('scientific_calls')) is int
         and integration_review['scientific_calls']==0 and integration_review['author_identity']=='/root/hilbert_advice_controls'
         and integration_review['reviewer_identity']!=integration_review['author_identity'],'exact genuine distinct current integration Source review')
    integration_contract_pin=integration_review['source_contract'];integration_contract=small(integration_contract_pin)
    need(integration_contract['builder_source']==own and integration_contract['worker_source']==WORKER
         and integration_contract['launcher_source']==LAUNCHER and integration_contract['meter_source']==METER_SOURCE
         and integration_contract['external_accounting_source']==EXTERNAL_JS,'current exact selected integration contract')
    need(len(SOURCES)==13 and len(INPUTS)==9 and len(ORIGINAL_SOURCES)==7 and len(CONTRACTS)==5 and len(REVIEWS)==7,'whole declared existing consumer census')
    for role,record in REVIEWS.items():
        value=small(record);source=WORKER if role=='worker' else LAUNCHER if role=='launcher' else SOURCES[role]
        contract=COMMON_CONTRACT if role in ('worker','launcher') else CONTRACTS[role]
        need(value.get('source')==source and value.get('source_contract')==contract and value.get('scope')==SCOPES[role]
             and value.get('source_only') is True and value.get('source_review_passed') is True and value.get('all_checks_passed') is True
             and type(value.get('scientific_calls')) is int and value['scientific_calls']==0
             and value['author_identity']!=value['reviewer_identity'],'genuine current review '+role)
    # A prior Root isolated qualification is provenance only, never a full52 grant.
    verify(spec['prior_isolated_qualification'])
    stage=Path(OUTPUT_DIRECTORY).parent;run=Path(OUTPUT_DIRECTORY)
    need(not stage.exists() and not run.exists() and stage.parent==stage.parent.resolve(),'fresh metadata parent and absent hardliteral worker output')
    prereg={'schema':'ROOT-Q-split-neutral-owned-controls-preregistration-v1','invocation_id':nonce,'sources':SOURCES,
        'inputs':INPUTS,'limits':LIMITS,'case_counts':{'kernel':20,'protocol':16,'point':8,'owned':8},
        'W16':'not_exercised_separate_expected_UNKNOWN','scope':'controls_only_no_original_target_positive_route',
        'author_identity':'/root','prior_isolated_qualification':spec['prior_isolated_qualification'],
        'metadata_only_builder':own,'no_worker_activation':True}
    records=list(SOURCES.values())+list(INPUTS.values())+list(ORIGINAL_SOURCES.values())+list(CONTRACTS.values())+list(REVIEWS.values())
    records += [WORKER,LAUNCHER,COMMON_CONTRACT,RUNTIME,CLOCK_POLICY,METER_SOURCE,EXTERNAL_JS,own,
        spec_pin,spec['integration_review'],integration_contract_pin,spec['prior_isolated_qualification']]
    bypath={}
    for record in records:
        verify(record);old=bypath.get(record['path']);need(old is None or old==record,'no lexical source/data alias disagreement');bypath[record['path']]=record
    # Only now emit Root-authorized metadata. Never mkdir the runtime child.
    stage.mkdir(mode=0o700)
    prereg_pin=write(stage/'ROOT-full52-preregistration-v1.json',prereg);bypath[prereg_pin['path']]=prereg_pin
    raw_closure=[bypath[k] for k in sorted(bypath)];need(len(raw_closure)<=512,'unchanged complete lexical closure cap')
    request={'schema':'ROOT-Q-split-neutral-owned-controls-request-v1','invocation_id':nonce,'sources':SOURCES,'inputs':INPUTS,
        'original_sources':ORIGINAL_SOURCES,'runtime':RUNTIME,'reviews':REVIEWS,'output_directory':OUTPUT_DIRECTORY,
        'preregistration':prereg_pin,'worker_source':WORKER,'launcher_source':LAUNCHER,'raw_closure':raw_closure}
    need(len(request)==12,'exact existing request12')
    request_pin=write(stage/'ROOT-full52-request-v1.json',request)
    construction={'schema':'ROOT-Q-full52-metadata-construction-v1','author_identity':'/root','constructor_source':own,
        'request':request_pin,'preregistration':prereg_pin,'source13':SOURCES,'inputs9':INPUTS,'original7':ORIGINAL_SOURCES,
        'contracts5':CONTRACTS,'reviews7':REVIEWS,'complete_raw_closure_count':len(raw_closure),'raw_closure':raw_closure,
        'external_meter':METER_SOURCE,'external_JS':EXTERNAL_JS,'external_metrics_path':str(stage/'native-terminal-meter-v1.json'),
        'native_command_shape':'pinnedPython -I -S -B meter2 freshMetrics pinnedPython -I -S -B launcher5 requestPath',
        'runtime_output_absent':not run.exists(),'all52_declared':True,'dispatch51_W16_deferred':True,
        'metadata_only':True,'scientific_calls':0,'actual_controls':0,'ROOT_resource_accepted':False,'full_architecture_qualified':False}
    need(not run.exists(),'builder never creates runtime controls output')
    construction_pin=write(stage/'ROOT-full52-construction-v1.json',construction)
    print(canonical({'request':request_pin,'construction':construction_pin,'metadata_only':True,'actual_controls':0}).decode())
    return 0


if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
