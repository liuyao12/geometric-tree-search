"""Mechanically promote the audited, actually searched incidence proof.

This phase admits exactly the concrete identity binding of its two-input
interface under I.2 alone. It does not enumerate or search a receptor family.
No target derivation is supplied apart from the unchanged recorded search.
"""
import copy,gzip,hashlib,json,subprocess,time
from pathlib import Path
from certificate_boundary_search import digest
from proof_boundary import boundary_words
from semantic_inventory_worker import oracle_for

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-receptors-20261011'
TMP=Path('/private/tmp/gcts-hilbert-receptors-promotion-20261011')

def build(source):
    request=source['request'];names=source['hypothesis_axioms']
    retained=source['retained_axioms'];theory=copy.deepcopy(request['theory'])
    theory['axioms']={n:copy.deepcopy(request['theory']['axioms'][n]) for n in retained}
    premises=[copy.deepcopy(request['theory']['axioms'][n]) for n in names]
    proof=[]
    for command in request['proof']:
        if command['rule']=='axiom' and command['name'] in names:
            i=names.index(command['name'])
            if command['formula']!=premises[i]:raise ValueError('source assumption binding')
            proof.append(dict(rule='assumption',index=i,formula=copy.deepcopy(command['formula'])))
        else:proof.append(copy.deepcopy(command))
    body=dict(premises=premises,conclusion=copy.deepcopy(request['target']),proof=proof)
    definition=dict(name='hilbert-promoted-'+digest(body),**body)
    taut=['imp',['bot'],['bot']]
    admitted=dict(protocol=request['protocol'],theory=theory,
                  blocks=copy.deepcopy(request['blocks'])+[definition],
                  proof=[dict(rule='tautology',formula=taut)],target=taut)
    return admitted,dict(level=2,family='searched-incidence-transport',definition=definition,
                         dependencies=[d['name'] for d in request['blocks']],
                         source_native_query=source['native_query'],
                         source_request_sha256=source['request_sha256'],
                         parameter_domain='Concrete identity binding only; no family specialization has yet been admitted.')

def main():
    began=time.perf_counter();plan=json.loads((OUT/'promotion-admission-plan.json').read_text())
    for file,sha in plan['sources'].items():
        if hashlib.sha256((ROOT/file).read_bytes()).hexdigest()!=sha:raise ValueError('frozen source changed '+file)
    for file,item in plan['data_dependencies'].items():
        p=ROOT/file
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256'] or p.stat().st_size!=item['bytes']:raise ValueError('frozen data changed '+file)
    source=json.loads((OUT/'ground-accepted-request.json').read_text())
    if source['result']['status']!='accepted' or json.loads((OUT/'audit.json').read_text())['status']!='passed':raise ValueError('source whole certificate not audited')
    stage=time.perf_counter();request,interface=build(source);construction=time.perf_counter()-stage
    TMP.mkdir(parents=True,exist_ok=True)
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'production'),executable=str(TMP/'oracle')))
    try:
        record=oracle.request(request,plan['native_steps'],'hilbert_searched_level_two_admission')
        fixed,free=boundary_words(request);record['boundary_words']=dict(fixed=fixed,free=free)
        (OUT/'promotion-admission-native.json.gz').write_bytes(gzip.compress(json.dumps([record],separators=(',',':')).encode(),mtime=0))
        result=dict(status=record['result']['status'],interface=interface,construction_seconds=construction,
                    native_seconds=record['seconds'],total_seconds=time.perf_counter()-began,
                    micro_steps=record['result']['micro_steps'],source_native_query=source['native_query'],
                    native_steps_limit=plan['native_steps'],
                    scope='Concrete mechanically promoted receptor admission only. No transfer search or family benefit measured. Independent replay pending.')
        (OUT/'promotion-admission-result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='interface'}),flush=True)
    finally:oracle.close()

if __name__=='__main__':main()
