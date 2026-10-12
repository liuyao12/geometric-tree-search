"""ROOT-owned metadata-only handoff after actual fresh preparation/static PASS.

No placeholder actual pins; this writes one immutable search plan only after
all supplied resource-credited artifacts and complete census are bound. It does
not activate/import a graph, register a pool, run search/checkers or train.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def read(path):return json.loads(Path(path).read_text())
def pin(path):
    path=Path(path);h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(65536),b''):h.update(b)
    return {'path':str(path.relative_to(ROOT)),'sha256':h.hexdigest(),'bytes':path.stat().st_size}

def main():
    parser=argparse.ArgumentParser()
    for role in ['static_plan','static_result','static_lifetime','static_root_terminal','preparation_root_terminal']:
        parser.add_argument('--'+role.replace('_','-'),required=True)
    args=parser.parse_args();paths={k:Path(v).resolve() for k,v in vars(args).items()}
    protocol=read(HERE/'search-protocol-v1.json');prep=read(HERE/'preparation-plan-v1.json')
    for p in prep['sources']+prep['inputs']+prep['preserved_files']:
        if pin(ROOT/p['path'])!={k:p[k] for k in ('path','sha256','bytes')}:raise ValueError('source/input changed before gate handoff')
    outcome=read(HERE/'preparation-outcome-v1.json');lifetime=read(HERE/'preparation-lifetime-v1.json')
    if outcome['status']!='completed_fresh_context_preparation_pending_independent_gate' or lifetime['status']!='passed_full_fresh_context_preparation_lifetime' or lifetime['worker_reaped_confirmed'] is not True:
        raise ValueError('actual complete preparation and owned lifetime PASS required')
    if outcome['plan']!=pin(HERE/'preparation-plan-v1.json') or lifetime['plan']!=outcome['plan']:
        raise ValueError('same exact owned preparation plan')
    result=read(paths['static_result']);life=read(paths['static_lifetime'])
    compiled=pin(HERE/'compiled-context-v1.json.gz');evidence=pin(HERE/'preparation-evidence-v1.json.gz')
    if outcome['compiled_context']!=compiled or outcome['preparation_evidence']!=evidence:
        raise ValueError('actual preparation output pins')
    gate={k:pin(paths['static_'+k]) for k in ['plan','result','lifetime']};gate['root_terminal']=pin(paths['static_root_terminal'])
    if result['status']!='passed_independent_fresh_context_family_pool_audit' or life['status']!='passed_owned_independent_fresh_context_family_pool_audit' or life['child_exit']!=0 or life['child_reaped'] is not True:
        raise ValueError('actual independent fresh static gate required')
    if result['plan']!=gate['plan'] or life['plan']!=gate['plan'] or life['result']!=gate['result'] or result['compiled_context_pin']!=compiled or result['preparation_evidence_pin']!=evidence:
        raise ValueError('same exact compiled/new prepared pool and audit/lifetime bindings')
    for field,value in {'primitive_license_count':229,'non_assumption_witness_count':226,'source_body_count':171,'single_types':171,'pair_types':29241}.items():
        if type(result[field]) is not int or result[field]!=value:raise ValueError('complete fresh gate census')
    if result['model_epoch']!=outcome['model_epoch'] or result['group_authority_epoch']!=outcome['group_authority_epoch'] or result['original_body_authority_epoch']!=outcome['original_body_authority_epoch']:
        raise ValueError('same new whole graph/body/pool relation')
    if len(result['groups_checked'])!=outcome['complete_pool_group_count']:raise ValueError('entire new pool, no subset')
    terminals={k:read(paths[k]) for k in ['static_root_terminal','preparation_root_terminal']}
    for name,t in terminals.items():
        if t.get('owner_process_terminal_reaped') is not True or t.get('worker_reaped') is not True or t.get('owner_exit_code')!=0:
            raise ValueError('ROOT terminal receipt must record same-owner successful exit and worker reaping: '+name)
    if terminals['static_root_terminal']['lifetime']!=gate['lifetime'] or terminals['preparation_root_terminal']['lifetime']!=pin(HERE/'preparation-lifetime-v1.json'):
        raise ValueError('ROOT exact owned lifetime terminal pins')
    plan=copy.deepcopy(protocol['search_plan_template']);plan['status']='source_frozen_search_plan_pending_ROOT_source_review_and_activation'
    plan['model_epoch']=result['model_epoch'];plan['complete_saved_pool_count']=len(result['groups_checked']);plan['fresh_static_gate_pins']=gate
    plan['sources']=prep['sources'];plan['inputs']=copy.deepcopy(prep['inputs']);plan['preserved_files']=copy.deepcopy(prep['preserved_files'])
    newroles={
        'compiled_context':HERE/'compiled-context-v1.json.gz','fresh_preparation_evidence':HERE/'preparation-evidence-v1.json.gz',
        'fresh_preparation_outcome':HERE/'preparation-outcome-v1.json','fresh_preparation_lifetime':HERE/'preparation-lifetime-v1.json',
        'fresh_static_plan':paths['static_plan'],'fresh_static_result':paths['static_result'],'fresh_static_lifetime':paths['static_lifetime'],
        'fresh_static_root_terminal':paths['static_root_terminal'],'fresh_preparation_root_terminal':paths['preparation_root_terminal'],
        'source_frozen_preparation_plan':HERE/'preparation-plan-v1.json','prospective_search_protocol':HERE/'search-protocol-v1.json'}
    for role,path in newroles.items():plan['inputs'].append({'role':role,**pin(path)})
    output=HERE/'search-plan-v1.json'
    with output.open('x') as stream:json.dump(plan,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'status':plan['status'],'plan':pin(output),'scientific_execution':False,'ROOT_activation_created':False}))
if __name__=='__main__':main()
