"""Independent expanded-kernel proofs, action interfaces and RL updates.

No proposer, problem generator, serializer or Policy import. The earlier
independent block expander and frozen primitive kernel validate each found
root and every declared block; the new audit recomputes matching and policy
features independently. Unknown proposer results remain unknown.
"""
import copy,hashlib,json,math,resource,struct,time
from pathlib import Path
from audit_serialized_kernel import replay
from audit_tree_kernel import packed,sha,need,PINNED_PROGRAM_SHA256

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def frozen(x):return tuple(frozen(v) for v in x) if type(x) is list else x
def count(t):return 1 if t[0]=='var' else 1+sum(count(a) for a in t[2])
def children(t):
    result={t}
    if t[0]=='fun':
        for a in t[2]:result.update(children(a))
    return result
def delta(a,b):
    if a==b:return 0
    if a[0]=='var' or b[0]=='var' or a[1]!=b[1] or len(a[2])!=len(b[2]):return max(count(a),count(b))
    return sum(delta(a,b) for a,b in zip(a[2],b[2]))
def subterms(t):
    out=[((),t)]
    if t[0]=='fun':
        for j,a in enumerate(t[2]):out.extend(((j,)+p,s) for p,s in subterms(a))
    return out
def match(pattern,t,variables):
    env={};pending=[(pattern,t)]
    while pending:
        p,a=pending.pop()
        if p[0]=='var' and p[1] in variables:
            if p[1] in env and env[p[1]]!=a:return None
            env[p[1]]=a
        elif p[0]=='var':
            if p!=a:return None
        elif a[0]!='fun' or p[1]!=a[1] or len(p[2])!=len(a[2]):return None
        else:pending.extend(zip(p[2],a[2]))
    return env if variables<=env.keys() else None
def instantiate(t,env):return env.get(t[1],t) if t[0]=='var' else ('fun',t[1],tuple(instantiate(a,env) for a in t[2]))
def put(t,path,replacement):
    if not path:return replacement
    args=list(t[2]);args[path[0]]=put(args[path[0]],path[1:],replacement);return ('fun',t[1],tuple(args))
def rules(data,assumptions=()):
    entries=[(n,a,'axiom',1) for n,a in data['theory']['axioms'].items()]
    entries += [(b['name'],b['conclusion'],'block',b['expanded_rules']) for b in data['library']]
    entries += [('premise-'+str(i),a,'assumption',1) for i,a in enumerate(assumptions)]
    out=[]
    for name,a,origin,cost in entries:
        variables=set();body=frozen(a)
        while body[0]=='all':variables.add(body[1]);body=body[2]
        if body[0]=='eq':out.append((name,body,variables,origin,cost))
    return out
def offers(t,rs,limit):
    out=[]
    for path,term in subterms(t):
        for name,eq,variables,origin,cost in rs:
            for direction in (1,-1):
                left,right=eq[1:] if direction==1 else eq[1:][::-1];env=match(left,term,variables)
                if env is None:continue
                after=put(t,path,instantiate(right,env))
                if after!=t and count(after)<=limit:out.append(dict(rule=name,origin=origin,path=path,direction=direction,before=t,after=after,cost=cost))
    return out
def feature(a,target):
    before,after=a['before'],a['after'];ps=children(target)
    return dict(bias=1,finishes=int(after==target),distance_gain=(delta(before,target)-delta(after,target))/8,
        size_gain=(count(before)-count(after))/8,target_overlap=(len(children(after)&ps)-len(children(before)&ps))/8,
        learned_block=int(a['origin']=='block'),expansion_cost=min(1000,a['cost'])/100,context_depth=len(a['path'])/8)
def decision_key(a):return (a['rule'],a['origin'],tuple(a['path']),a['direction'],frozen(a['before']),frozen(a['after']))
def close(a,b,reason):need(abs(a-b)<=1e-9*max(1,abs(a),abs(b)),reason)

def policy_audit(data):
    weights={};baseline=0.;updates=0;decisions=0;reward_checks=0
    for episode in data['training']['episodes']:
        for record in episode['result'].get('records',[]):
            goal=frozen(record['goal']);rs=rules(data,record['assumptions']);enumerated=0
            for trace in record['rollouts']:
                current=goal[1];visited={current};features_seen=[];cost=0;gradients=[]
                need(len(trace['actions'])==len(trace['gradients']),'one gradient per proposal choice')
                for chosen,saved in zip(trace['actions'],trace['gradients']):
                    full=offers(current,rs,record['term_limit']);enumerated+=len(full);valid=[a for a in full if a['after'] not in visited]
                    keys=[decision_key(a) for a in valid];key=decision_key(chosen);need(key in keys,'chosen move is not in complete matching domain')
                    j=keys.index(key);fs=[feature(a,goal[2]) for a in valid];scores=[sum(weights.get(k,0)*v for k,v in f.items()) for f in fs]
                    top=max(scores);ps=[math.exp(v-top) for v in scores];denom=sum(ps);ps=[v/denom for v in ps]
                    expected={k:sum(p*f.get(k,0) for p,f in zip(ps,fs)) for k in fs[j]}
                    gradient={k:fs[j][k]-expected[k] for k in expected}
                    need(set(saved)==set(gradient),'gradient fields')
                    for k in gradient:close(saved[k],gradient[k],'gradient '+k)
                    action=valid[j];current=action['after'];visited.add(current);cost+=action['cost'];gradients.append(gradient);decisions+=1
                # When a rollout stops because all neighbors are visited, its
                # last full domain was enumerated but produced no decision.
                success=current==goal[2]
                if not success and len(trace['actions'])<10:enumerated+=len(offers(current,rs,record['term_limit']))
                need(success==trace['success'],'rollout endpoint')
                reward=(1. if success else -.5)-min(.5,(enumerated+cost)/10000);close(reward,trace['reward'],'charged proposal reward')
                advantage=reward-baseline;baseline=.9*baseline+.1*reward
                for g in gradients:
                    for k,v in g.items():weights[k]=weights.get(k,0)+.03*advantage*v/max(1,len(gradients))
                # Feature lookup in the zero-start Policy materializes zeros.
                for a in offers(goal[1],rs,record['term_limit']):
                    for k in feature(a,goal[2]):weights.setdefault(k,0.)
                updates+=1;reward_checks+=1
        need(updates==episode['updates'],'episode update count')
        for k in weights.keys()|episode['weights'].keys():close(weights.get(k,0),episode['weights'].get(k,0),'episode weight '+k)
        close(baseline,episode['baseline'],'episode baseline')
    need(updates==data['training']['updates'],'final updates')
    return dict(episodes=len(data['training']['episodes']),updates=updates,decisions=decisions,rewards=reward_checks,method='independent complete matching domains, softmax gradients, charged rewards and REINFORCE updates; sampled RNG stream not independently reconstructed')

def audit_proposals(data):
    results=[];expanded=0;requests=0
    def check_one(item,problem):
        nonlocal expanded,requests
        if item['status']!='accepted_proposal':return
        request=item['request'];need(request['theory']==data['theory'] and request['target']==problem['target'],'external theory/target binding')
        pin=sha({k:request[k] for k in ('protocol','theory','target')});result=replay(packed(request),pin);need(result['status']=='accepted','independent full expansion')
        expanded+=result['expanded_lines'];requests+=1
        for record in item['records']:
            path=record.get('path')
            if path is None:continue
            goal=frozen(record['goal']);current=goal[1];rs=rules(data,record['assumptions'])
            for a in path:
                rule=a['rule'];selected=dict(a,rule=rule['name'],origin=rule['origin']);key=decision_key(selected)
                need(any(decision_key(o)==key for o in offers(current,rs,record['term_limit'])),'saved searched move invalid');current=frozen(a['after'])
            need(current==goal[2],'searched path endpoint')
        results.append(dict(problem=problem['id'],expanded_lines=result['expanded_lines'],blocks=result['blocks']))
    for row in data['discovery']:check_one(row['result'],row['problem'])
    by_id={p['id']:p for p in data['evaluation']['problems']}
    for row in data['evaluation']['runs']:check_one(row['result'],by_id[row['problem']])
    need(data['tree_program_sha256']==PINNED_PROGRAM_SHA256,'fixed semantic program pin')
    for r in data['tree_program_checks']:need(r['result']['status']=='accepted' and r['result']['program_sha256']==PINNED_PROGRAM_SHA256,'complete tree acceptance binding')
    return dict(requests=requests,expanded_primitive_lines=expanded,results=results)

def native_bindings(data):
    """Independent syntax heap construction binds every native input to its proof.

    Complete event digests are compared with the completed original runs;
    independent instruction semantics are separately exercised by native tests.
    This audit does not claim to reconstruct the executable toolchain.
    """
    native=data['native_tree_replay']
    for file,pin in native['sources'].items():need(hashlib.sha256((HERE/file).read_bytes()).hexdigest()==pin,'native source '+file)
    code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program'];need(sha(code)==PINNED_PROGRAM_SHA256,'independent code pin')
    requests={r['problem']['id']:r['result']['request'] for r in data['discovery']}
    requests.update({r['problem']+'/'+r['lane']:r['result']['request'] for r in data['evaluation']['runs'] if r['result']['status']=='accepted_proposal'})
    old={r['id']:r['result']['result'] for r in data['tree_program_checks']}
    need(len(native['cases'])==len(old)==66 and {r['id'] for r in native['cases']}==set(old),'native case coverage')
    for row in native['cases']:
        r=row['result'];need(r['program_sha256']==PINNED_PROGRAM_SHA256,'native code binding')
        for key in ('status','steps','event_sha256','peak_frames','heap_nodes','profile','value'):need(r[key]==old[row['id']][key],'native full trace binding '+key)
        nodes=[tuple(n) for n in code['nodes']];index={v:257+j for j,v in enumerate(nodes)}
        def pair(a,b):
            k=(a,b)
            if k not in index:index[k]=257+len(nodes);nodes.append(k)
            return index[k]
        def word(xs):
            out=256
            for v in reversed(xs):out=pair(v,out)
            return out
        def text(s):return word(list(s.encode('utf-8','surrogatepass')))
        def value(x):
            if type(x) is dict:
                keys=list(x);vs=[value(x[k]) for k in keys]
                return pair(0,word([pair(text(k),v) for k,v in zip(keys,vs)]))
            if type(x) is list:return pair(1,word([value(a) for a in x]))
            if type(x) is str:return pair(2,text(x))
            if type(x) is bool:return pair(5,int(x))
            if type(x) is int:
                n=256
                for _ in range(abs(x)):n=pair(1,n)
                return pair(3 if x>=0 else 4,n)
            need(x is None,'independent exact syntax value');return pair(6,256)
        request=json.loads(packed(requests[row['id']]));root=value(request);flat=[0x47544931,root,len(nodes)]
        for a,b in nodes:flat.extend((a,b))
        raw=struct.pack('<'+'I'*len(flat),*flat)
        need(hashlib.sha256(raw).hexdigest()==r['input_sha256'],'native request input binding')
    return dict(cases=len(old),input_heaps='independently reconstructed from pinned code and exact request syntax',trace_scope='all full digests, counts, profiles, heaps and results match completed original runs; independent generic execution controls in test_tree_native.py')

def main():
    began=time.perf_counter();path=DOCS/'learned-proof-blocks-001.json';data=json.loads(path.read_text())
    for file,pin in data['sources'].items():need(hashlib.sha256((HERE/file).read_bytes()).hexdigest()==pin,'source pin '+file)
    block_definitions=[]
    for i,b in enumerate(data['library']):
        source=next(r for r in data['discovery'] if r['promoted']==b['name'])['result']['request']
        need(b['proof']==source['proof'] and b['conclusion']==source['target'] and b['premises']==[],'block discovery provenance')
        definitions=[{k:x[k] for k in ('name','premises','conclusion','proof')} for x in data['library'][:i+1]]
        probe=dict(protocol='gcts-fol-1',theory=data['theory'],target=b['conclusion'],blocks=definitions,proof=[dict(rule='block',formula=b['conclusion'],name=b['name'],inputs=[])])
        result=replay(packed(probe));need(result['status']=='accepted' and result['expanded_lines']==b['expanded_rules'],'derived block expansion cost')
        block_definitions.append(dict(name=b['name'],expanded_lines=result['expanded_lines']))
    proof=audit_proposals(data);proof['block_definitions']=block_definitions;policy=policy_audit(data);native=native_bindings(data)
    need(not ({sha(p['target']) for p in data['training']['problems']} & {sha(p['target']) for p in data['evaluation']['problems']}),'statement leakage')
    need(data['training']['initial_weights']=={},'zero-start model')
    altered=copy.deepcopy(data['discovery'][-1]['result']['request']);pin=sha({k:altered[k] for k in ('protocol','theory','target')});mutations=[]
    for name,mutate in [('target',lambda d:d.update(target=['bot'])),('theory',lambda d:d['theory']['axioms'].update(invented=d['target'])),('block-body',lambda d:d['blocks'][0]['proof'][-1].update(formula=['bot'])),('block-order',lambda d:d['blocks'][0]['proof'].append(dict(rule='block',formula=d['blocks'][0]['conclusion'],name=d['blocks'][0]['name'],inputs=[])))]:
        wrong=copy.deepcopy(altered);mutate(wrong);need(replay(packed(wrong),pin)['status']=='rejected','mutation '+name);mutations.append(name)
    audit=dict(proof=proof,policy=policy,native=native,mutations_rejected=mutations,seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='finite searched proposal proofs and exact learned interfaces; unknown runs unrefuted; native toolchain and logical soundness formalization remain trusted/open')
    data['independent_audit']=audit;path.write_text(json.dumps(data,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in audit.items() if k not in ('proof',)},indent=2),flush=True)
if __name__=='__main__':main()
