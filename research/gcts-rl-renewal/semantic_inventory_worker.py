"""Fresh semantic-family discovery, learning and isolated cold observations."""
import copy,gzip,hashlib,json,sys,time
from pathlib import Path
from certificate_boundary_search import canonical,digest
from native_receptor_points import Model as Primitive,compile_guards,search as primitive_search
from semantic_inventory_cases import promotion,training
from semantic_lemma_inventory import mine,specialize,used_definitions
from semantic_inventory_oracle import RequestOracle,check_inventory
from semantic_receptor_points import Model
from semantic_inventory_search import search
from semantic_inventory_policy import FEATURES,EPISODES,RATE,reward,update
from semantic_point_smt import solve
from proof_boundary import boundary_words
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NATIVE_STEPS=5*10**9

def oracle_for(job):
    directory=Path(job['directory']);directory.mkdir(parents=True,exist_ok=True)
    micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()))
    old=json.loads((DOC/'proof-boundary-001.json').read_text())
    if digest(micro)!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM:raise ValueError('fixed checker')
    (directory/'code.bin').write_bytes(code_bytes(micro))
    return RequestOracle(micro,old['cases'][0]['initial'],job['executable'],directory/'code.bin',directory)

def verify(oracle,spec,proof,inventory,purpose):
    blocks=used_definitions(inventory,proof) if inventory else []
    rec=oracle.query(dict(**spec,blocks=blocks),proof,True,NATIVE_STEPS)
    rec['purpose']=purpose
    if rec['result']['status']=='rejected':raise ValueError('point certificate rejected by unchanged native checker')
    return rec

def register(spec,library,compiled,oracle):
    return check_inventory(spec,specialize(library,compiled['basis']),oracle,
                           spec.get('inventory_steps',NATIVE_STEPS))

def train(job,oracle):
    began=time.perf_counter();donors=[];library=[];catalog={};registries={};cache={}
    for spec in job['donors']:
        compiled=compile_guards(spec,oracle)
        if compiled['status']!='complete':raise ValueError('incomplete donor compilation')
        model=Primitive(spec,compiled);out=primitive_search(model,attempts=2000,seconds=30)
        if out['proof'] is None:raise ValueError('fresh donor not found')
        rec=verify(oracle,spec,out['proof'],None,'fresh_semantic_donor')
        if rec['result']['status']!='accepted':raise ValueError('unfinished donor cannot enter inventory')
        family=mine(rec['request'],[],dict(case=spec['id'],query=rec['id'],request_sha256=rec['request_sha256']))
        library.append(family);catalog[spec['id']]=compiled;cache[rec['request_sha256']]=rec['id']
        donors.append(dict(case=spec,compiled=compiled,model=model.record(),search=out,
                           verification_query=rec['id'],family=family['id']))
        print('fresh donor',spec['id'],len(out['proof']),'lines',flush=True)
    # A new proof using the lower registered inventory supplies a higher family.
    pspec=promotion();pc=compile_guards(pspec,oracle);pi=register(pspec,library,pc,oracle)
    if pi['status']!='native_accepted':raise ValueError('promotion inventory not checked')
    pm=Model(pspec,pc,pi);po=search(pm,'fixed',attempts=5000,seconds=30)
    if po['proof'] is None:raise ValueError('higher-family discovery remains unresolved')
    pq=verify(oracle,pspec,po['proof'],pi,'higher_semantic_family_donor')
    if pq['result']['status']!='accepted':raise ValueError('higher-family native check incomplete')
    family=mine(pq['request'],pi['definitions'],dict(case=pspec['id'],query=pq['id'],request_sha256=pq['request_sha256']))
    if not family['dependencies']:raise ValueError('higher family did not use earlier lemmas')
    library.append(family);cache[pq['request_sha256']]=pq['id']
    promoted=dict(case=pspec,compiled=pc,inventory=pi,model=pm.record(),search=po,
                  verification_query=pq['id'],family=family['id'])
    specs=training(job['donors'],pspec)
    for spec in specs:
        compiled=catalog.get(spec['id']) or (pc if spec['id']==pspec['id'] else compile_guards(spec,oracle))
        inventory=register(spec,library,compiled,oracle)
        if inventory['status']!='native_accepted':raise ValueError('training registry not checked')
        catalog[spec['id']]=compiled;registries[spec['id']]=inventory
    discovery_seconds=time.perf_counter()-began;stage=time.perf_counter()
    weights=[0.]*len(FEATURES);baseline=0.;episodes=[]
    for index in range(EPISODES):
        spec=specs[index%len(specs)];inventory=registries[spec['id']]
        model=Model(spec,catalog[spec['id']],inventory);before=weights.copy()
        out=search(model,'learned',weights=before,stochastic=True,seed=63000+index,
                   attempts=3000,seconds=30)
        accepted=False;query=None;cached=False;key=None
        if out['proof']:
            request=dict(protocol='gcts-fol-1',theory=spec['theory'],
                         blocks=used_definitions(inventory,out['proof']),proof=out['proof'],target=spec['target'])
            key=digest(request)
            if key in cache:query=cache[key];accepted=True;cached=True
            else:
                rec=verify(oracle,spec,out['proof'],inventory,'training_semantic_feedback')
                query=rec['id'];accepted=rec['result']['status']=='accepted'
                if accepted:cache[key]=query
        value=reward(out,accepted,model.arity)
        weights,baseline,learning=update(weights,out['events'],value,baseline)
        episodes.append(dict(id=index,case=spec['id'],search=out,accepted=accepted,
            verification_query=query,request_sha256=key,cached_native_acceptance=cached,
            weights_before=before,weights_after=weights.copy(),baseline_after=baseline,learning=learning))
        print('episode',index,spec['id'],out['status'],out['metrics'].get('attempts',0),
              'native',accepted,'reward',round(value,6),flush=True)
    return dict(version='semantic-inventory-training-001',donors=donors,promotion=promoted,
        library=library,cases=specs,catalog=catalog,registries=registries,features=FEATURES,
        rate=RATE,episodes=episodes,weights=weights,baseline=baseline,
        discovery_seconds=discovery_seconds,training_seconds=time.perf_counter()-stage,
        scope='Fresh primitive GCTS donors, native-checked ground definitions, a freshly searched dependent lemma, and zero-start REINFORCE. Models and graphs are fresh per rollout. Exact whole-certificate native acceptance may be reused only through the disclosed training cache; no earlier inventory, policy or proof is imported.')

def evaluate(job,oracle):
    raw=Path(job['policy']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=job['policy_sha256']:raise ValueError('frozen policy binding')
    policy=json.loads(raw);spec=job['case'];compiled=compile_guards(spec,oracle)
    result=dict(case=spec,compiled=compiled,mode=job['mode'],policy_sha256=job['policy_sha256'],
                repetition=job['repetition'],method_order=job['method_order'],model=None,search=None,proof=None)
    if compiled['status']!='complete':return dict(result,status=compiled['status'])
    inventory=register(spec,policy['library'],compiled,oracle);result['inventory']=inventory
    if inventory['status']!='native_accepted':return dict(result,status=inventory['status'])
    model=Model(spec,compiled,inventory);result['model']=model.record()
    if job['mode']=='z3':
        out=solve(model,seconds=30,disabled=not spec.get('search_enabled',True))
    else:
        out=search(model,job['mode'],weights=policy['weights'],stochastic=False,seed=job['seed'],
                   attempts=spec.get('attempts',5000),seconds=30)
    result.update(search=out,proof=out['proof'],status=out['status'])
    if out['proof']:
        rec=verify(oracle,spec,out['proof'],inventory,'frozen_semantic_evaluation')
        result['verification_query']=rec['id']
        result['status']='native_proof_discovered' if rec['result']['status']=='accepted' else 'unknown_native_verification'
    return result

def main():
    began=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text());oracle=oracle_for(job)
    try:
        result=train(job,oracle) if job['kind']=='training' else evaluate(job,oracle)
        for rec in oracle.records:
            fixed,free=boundary_words(rec['request']);rec['boundary_words']=dict(fixed=fixed,free=free)
        result['records']=oracle.records;result['queries']=len(oracle.records)
    finally:oracle.close()
    result['cold_seconds']=time.perf_counter()-began
    Path(sys.argv[2]).write_text(json.dumps(result,separators=(',',':'))+'\n')
    print('worker complete',job['kind'],result['queries'],round(result['cold_seconds'],3),flush=True)

if __name__=='__main__':main()
