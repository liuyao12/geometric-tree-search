"""Raw Source assembly and AST/compile only. No scientific functions execute."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
def pin(path):
    raw = path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,value):
    path = HERE/name
    with path.open('x') as f:
        json.dump(value,f,sort_keys=True,indent=2)
        f.write('\n')
    return pin(path)
parent = BASE/'shared-bounded-point-board-cold-source-20261015/verify_saved_word_point_board_v1.py'
assert pin(parent)['sha256'] == 'dd7a1a13829c63d41935038327c063a7089b2c3e28d28c20f4743ebcd6ec7be2'
parent_raw = parent.read_text()
ptree = ast.parse(parent_raw)
assigns = {n.targets[0].id:ast.literal_eval(n.value) for n in ptree.body
    if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)
    and n.targets[0].id in ('FIXED','FIXED_INPUTS','LIMITS')}
proposer = json.loads((BASE/'unit-row-implicit-degree-source-20261015/handoff-v2.json').read_bytes())
checker = json.loads((BASE/'unit-row-degree-checker-source-20261015/handoff-v1.json').read_bytes())
controls = json.loads((BASE/'unit-row-degree-controls-source-20261015/handoff-v1.json').read_bytes())
fixed = {k:assigns['FIXED'][k] for k in ('clean_support','kernel','membership')}
fixed.update(proposer=proposer['source'],degree_checker=checker['source'],controls=controls['source'])
inputs = {k:assigns['FIXED_INPUTS'][k] for k in ('declaration','profile')}
for ref in [*fixed.values(),*inputs.values()]:
    assert pin(Path(ref['path'])) == ref
helpers = ['need','canonical','raw_pin','unique','reject_constant','finite_float','decode','read_pinned',
           'load_module','write_new','anchor','same','invoke','cancel','all_function_anchors']
defs = {n.name:n for n in ptree.body if isinstance(n,ast.FunctionDef)}
header = '''"""Cold local-degree controls only. Reuses existing native measurement/helpers.
No proof word, donor or library is an input. Not a GCTS search engine.
"""
import time
CLOCK=time.clock_gettime_ns
CLOCK_ID=time.CLOCK_MONOTONIC
EARLY_G=CLOCK(CLOCK_ID)
import copy
import hashlib
import itertools
import json
import json.decoder
import json.encoder
import json.scanner
import math
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import types
EXIT=os._exit
VERSION='unit-row-degree-controls-cold-v1'
SCOPE='unit-row-degree-controls-cold-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
'''
source = header+'FIXED='+repr(fixed)+'\nFIXED_INPUTS='+repr(inputs)+'\nLIMITS='+repr(assigns['LIMITS'])+'\n\n'
source += '\n\n'.join(ast.get_source_segment(parent_raw,defs[k]) for k in helpers)+'\n\n'
source += (HERE/'worker_main_v1.py.in').read_text()
source_path = HERE/'unit_row_degree_controls_cold_v1.py'
with source_path.open('x') as f:
    f.write(source)
tree = ast.parse(source)
compile(tree,str(source_path),'exec')
current_defs = {n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
for k in helpers:
    assert ast.dump(current_defs[k],include_attributes=False) == ast.dump(defs[k],include_attributes=False)
sources = dict(intake=pin(source_path),**fixed)
contract = {'schema':'unit-row-degree-controls-cold-Source-contract-v1',
    'scope':'unit-row-degree-controls-cold-Source','author_identity':'/root','source_only':True,
    'scientific_calls':0,'scientific_acceptance':False,'sources':sources,'inputs':inputs,
    'limits':assigns['LIMITS'],'resource_rule':'single-owned-process-native-terminal-v1',
    'endpoint':'Complete local-degree control evidence only; no proof discovery/point search/graph/scheduler/rollback/marking/RL benefit.',
    'fresh_authority':'Each proposer/checker call receives a separate freshly constructed original membership object after reauthentication of whole original declaration/profile. Full Source binding remains unchanged. Native tick retained even for injected callback controls.',
    'scope_limits':['Fixed reviewed synchronous Darwin Sources, not hostile Python/OS/VM assurance.',
        'Complete root target24 and current six-rule unit-row inventory only.',
        'Caller-supplied branch exclusions are fixtures, not justified search failures.',
        'Primitive membership shares the reviewed original kernel; this is distinct local geometric/census checking, not another1717 whole-proof acceptance.',
        'Any unfinished callback/check/runtime work prevents successful completion; no false zero/singleton.'],
    'provenance':{'parent_intake':pin(parent),'copied15_helpers':helpers,
        'new_source_scope':'New local-control main/adapters, original early native gates and two-line wire. No new external measurement or custody framework.',
        'proposer_handoff':pin(BASE/'unit-row-implicit-degree-source-20261015/handoff-v2.json'),
        'checker_handoff':pin(BASE/'unit-row-degree-checker-source-20261015/handoff-v1.json'),
        'controls_handoff':pin(BASE/'unit-row-degree-controls-source-20261015/handoff-v1.json')},
    'Review_ABI':{'schema':'unit-row-degree-controls-cold-typed-Source-review-v1',
        'scope':'unit-row-degree-controls-cold-Source','author_identity':'/root',
        'source':sources['intake'],'sources':sources,'source_only':True,
        'scientific_calls':0,'scientific_acceptance':False,
        'source_contract':'Exact current complete raw contract capsule; no self hash.',
        'reviewer_identity':'Actual reviewer decides; Root author check disclosed separately.',
        'source_review_passed':'Actual reviewer decides.'}}
contract_ref = write('Source-contract-v1.json',contract)
static = write('author-static-evidence-v1.json',{'schema':'unit-row-degree-controls-cold-author-static-v1',
    'source':sources['intake'],'AST_compile_only':True,'unchanged_helpers':helpers,
    'sources':sources,'inputs':inputs,'scientific_calls':0,'scientific_acceptance':False,
    'Root_is_caller_author':True,'independent_caller_review_pending':True})
handoff = write('handoff-v1.json',{'schema':'unit-row-degree-controls-cold-handoff-v1',
    'source':sources['intake'],'sources':sources,'inputs':inputs,'source_contract':contract_ref,
    'static_evidence':static,'status':'FROZEN_SOURCE_ONLY_DISTINCT_REVIEW_PENDING'})
print(json.dumps({'handoff':handoff,'source':sources['intake'],'source_contract':contract_ref},sort_keys=True))
