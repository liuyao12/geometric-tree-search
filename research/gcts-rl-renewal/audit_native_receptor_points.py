"""Independent point universe, entire search trees and native executions.

Does not import the new model, case registry, worker, search or producer.
Rebuilds guards from declared syntax and native tautology results; scans all
placements at every tree node without producer incidence/dependency indexes.
"""
import collections,copy,gzip,itertools,json,math,subprocess,time
from pathlib import Path
from audit_tree_kernel import need,packed
from audit_certificate_boundary import grammar,tree as chronological_tree,initial_for,artifact,sha,pin
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from audit_semantic_proofs import whole_replay
from audit_logical_wang_clusters import checked_chain
from micro_cert import run,write_cuts
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-native-receptor-points-audit-001')
def load(n):return json.loads(gzip.decompress((DOCS/n).read_bytes()))
def encode(j,ch,value):return [((4*j+int(ch=='command'),100+i),v) for i,v in enumerate([*packed(value),256])]
def rebuild(spec,compiled):
    basis,variables,domains=grammar(spec);need((basis,variables)==(compiled['basis'],compiled['variables']),'all subformulas and variables');taut={packed(a) for a in compiled['tautologies']};placements=[];conflicts=[]
    def add(key,cmd,needs):
        j,role,_,_=key;entries=encode(j,'command',cmd)+encode(j,'formula',cmd['formula'])+[e for i,a in needs for e in encode(i,'formula',a)];mark={}
        for p,v in entries:
            if p in mark and mark[p]!=v:conflicts.append(dict(key=key,command=cmd,requirements=needs,reason='internally unequal marking values'));return
            mark[p]=v
        placements.append(dict(key=key,occupancy=[((4*j,role),12)],marks=sorted(mark.items()),slot=j,kind='command' if role==0 else 'guard',command=cmd,requirements=needs))
    for j,rows in enumerate(domains):
        for k,c in enumerate(rows):
            add((j,0,k,0),c,[]);f=c['formula'];r=c['rule']
            if r=='axiom' and spec['theory']['axioms'][c['name']]==f:add((j,1,k,0),c,[])
            if r=='refl' and f[0]=='eq' and f[1]==f[2]:add((j,1,k,0),c,[])
            if r=='tautology' and packed(f) in taut:add((j,1,k,0),c,[])
            if r=='generalize' and f[0]=='all' and f[1]==c['variable']:add((j,1,k,0),c,[(c['source'],f[2])])
            if r=='mp':
                for variant,a in enumerate(basis):
                    if a[0]=='imp' and a[2]==f:add((j,1,k,variant),c,[(c['antecedent'],a[1]),(c['implication'],a)])
    return dict(domains=domains,command_counts=list(map(len,domains)),complete_words=math.prod(map(len,domains)),placements=sorted(placements,key=lambda c:c['key']),conflicts=conflicts,roots=[(4*j,k) for j in range(spec['length']) for k in (0,1)])
def state_pin(s):
    return pin(dict(totals=sorted(s['totals'].items()),marks=sorted(s['marks'].items()),generations=sorted(s['generations'].items()),roots=sorted(s['roots'].items()),selected=sorted(s['selected']),order=s['order'],tile_generations=s['tile_generations'],allowed_points=sorted(s['roots'])))
def initial(spec,model):
    roots={tuple(p):0 for p in model['roots']};return dict(totals={},marks=dict(encode(spec['length']-1,'formula',spec['target'])),generations=roots.copy(),roots=roots,selected=set(),order=[],tile_generations=[])
def legal(c,s):return tuple(c['key']) not in s['selected'] and all(s['totals'].get(tuple(p),0)+v<=12 and tuple(p) in s['roots'] for p,v in c['occupancy']) and all(tuple(p) not in s['marks'] or s['marks'][tuple(p)]==v for p,v in c['marks'])
def advance(c,s):
    out=copy.deepcopy(s);g=1+min(s['generations'][tuple(p)] for p,v in c['occupancy'])
    for p,v in c['occupancy']:p=tuple(p);out['totals'][p]=out['totals'].get(p,0)+v;out['generations'][p]=min(out['generations'][p],g)
    for p,v in c['marks']:out['marks'][tuple(p)]=v
    out['selected'].add(tuple(c['key']));out['order'].append(tuple(c['key']));out['tile_generations'].append(g);return out
def point_tree(r,model):
    spec=r['case'];result=r['search'];inventory={tuple(c['key']):c for c in model['placements']};root=initial(spec,model);metrics=collections.Counter();found=None;audited=0
    def visit(s,t):
        nonlocal audited,found
        audited+=1;metrics['nodes']+=1;domains={p:sorted(k for k,c in inventory.items() if any(tuple(q)==p for q,v in c['occupancy']) and legal(c,s)) for p in s['roots'] if s['totals'].get(p,0)<12}
        census=[dict(point=p,generation=s['generations'][p],keys=keys) for p,keys in sorted(domains.items())];need(packed(t['census'])==packed(census) and t['state_sha256']==state_pin(s),'complete point/candidate graph and whole state')
        dead=sorted(p for p,d in domains.items() if len(d)==0);forced=sorted(p for p,d in domains.items() if len(d)==1)
        if dead:kind,p='dead',dead[0]
        elif forced:kind,p='forced',forced[0]
        elif not domains:kind,p='empty',None
        else:kind,p='branch',min(domains,key=lambda p:(s['generations'][p],len(domains[p]),p))
        need((t['kind'],t['point'])==(kind,list(p) if p is not None else None),'global dead, forced, earliest generation')
        if kind=='dead':metrics['dead']+=1;need(not t['children'],'dead has no child');return False
        if kind=='empty':found=s;need(not t['children'],'complete target has no child');return True
        metrics[kind]+=1;keys=domains[p]
        for index,child in enumerate(t['children']):
            need(index<len(keys) and tuple(child['key'])==keys[index],'complete original alternative order');metrics['attempts']+=1;okay=visit(advance(inventory[keys[index]],s),child['tree'])
            if okay is not False:need(index+1==len(t['children']),'no choices after success/unknown');return okay
            metrics['backtracks']+=1
        if len(t['children'])<len(keys):
            need(t.get('cutoff')=='before_placement' and (metrics['attempts']>=result['limits']['attempts'] or result['seconds']>=result['limits']['seconds']),'unknown cutoff with complete remaining alternatives');return None
        need('cutoff' not in t,'fully traversed node');return False
    okay=visit(root,result['tree']);status='finite_marked_proof_region' if okay else 'unknown_search_budget' if okay is None else 'exhausted_finite_marked_region';need(result['status']==status and result['metrics']==dict(metrics),'all point tree counters/status');need(result['root_restored'] and result['root_state_sha256']==state_pin(root),'exact root state restored')
    proof=[inventory[k]['command'] for k in sorted(found['order']) if k[1]==0] if found else None;need(proof==result['proof']==r['proof'],'searched commands decoded by line slots');need(packed(result['placements'])==packed(found['order'] if found else []) and result['tile_generations']==(found['tile_generations'] if found else []),'all placement generations');return audited
def equivalence(spec,model):
    if model['complete_words']>5000:return dict(status='outside_exhaustive_bound',words=model['complete_words'])
    commands={tuple(c['key']):c for c in model['placements']};guards=collections.defaultdict(list)
    for c in model['placements']:
        if c['kind']=='guard':guards[c['slot'],c['key'][2]].append(c)
    accepted=0
    for indexes in itertools.product(*[range(len(d)) for d in model['domains']]):
        s=initial(spec,model);proof=[]
        for j,k in enumerate(indexes):c=commands[j,0,k,0];need(legal(c,s),'original command placements');s=advance(c,s);proof.append(c['command'])
        geometric=all(any(legal(g,s) for g in guards[j,k]) for j,k in enumerate(indexes))
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=proof,target=spec['target'])
        try:logical=whole_replay(request)['status']=='accepted'
        except ValueError:logical=False
        need(geometric==logical,'finite original-certificate/marked-region equivalence');accepted+=geometric
    return dict(status='all_words_checked_against_independent_logical_kernel',words=model['complete_words'],accepted=accepted)
def point_binding(r):
    compiled=r['compiled'];basis,variables,domains=grammar(r['case']);need((compiled['basis'],compiled['variables'])==(basis,variables),'compiler syntax basis');tauts=[]
    for index,qid in enumerate(compiled['queries']):
        rec=r['records'][qid];expected=dict(protocol='gcts-fol-1',theory=r['case']['theory'],blocks=[],proof=[dict(rule='tautology',formula=basis[index])],target=basis[index]);need(rec['purpose']=='tautology_instance' and rec['basis_index']==index and rec['request']==expected,'native tautology guard instance')
        if rec['result']['status']=='accepted':tauts.append(basis[index])
    need(tauts==compiled['tautologies'],'native guard acceptance catalog')
    if compiled['status']!='complete':
        need(r['model'] is None and r['search'] is None and r['proof'] is None,'unfinished compiler cannot prune or search')
        need(compiled['status']==r['status'] and compiled['status'] in ('unknown_compile_budget','unknown_native_compilation'),'unknown compiler outcome')
        if compiled['status']=='unknown_native_compilation':need(compiled['queries'] and r['records'][compiled['queries'][-1]]['result']['status'] not in ('accepted','rejected'),'unfinished native query never prunes')
        else:need(len(compiled['queries'])>=r['case'].get('compile_queries',64),'compiler query budget')
        return None,0
    need(len(compiled['queries'])==len(basis) and all(r['records'][i]['result']['status'] in ('accepted','rejected') for i in compiled['queries']),'complete native guard compilation');m=rebuild(r['case'],compiled)
    for k in ('domains','command_counts','complete_words','placements','conflicts','roots'):need(packed(m[k])==packed(r['model'][k]),'full independently rebuilt inventory '+k)
    nodes=point_tree(r,m)
    if r['proof']:
        q=r['verification_query'];rec=r['records'][q];need(q==len(compiled['queries']) and len(r['records'])==q+1,'only native final verification follows point search');need(rec['request']['proof']==r['proof'] and rec['request']['target']==r['case']['target'] and rec['purpose']=='searched_certificate_without_point_markings','marking-erased whole certificate')
        need(rec['result']['status']=='accepted' and r['status']=='native_proof_discovered','native final acceptance')
    else:need(len(r['records'])==len(compiled['queries']) and r['status']==r['search']['status'],'no native proof claimed')
    return m,nodes
def corruptions(r):
    tests=[]
    def change(name,edit):
        b=copy.deepcopy(r);edit(b)
        try:point_binding(b)
        except (ValueError,KeyError,IndexError,TypeError):tests.append(name)
        else:raise ValueError('corruption accepted '+name)
    change('removed-original-command',lambda b:b['model']['domains'][0].pop())
    change('lost-remote-mark',lambda b:b['model']['placements'][-1]['marks'].pop())
    change('changed-point-census',lambda b:b['search']['tree']['census'][0]['keys'].pop())
    change('changed-generation',lambda b:b['search']['tree']['census'][0].update(generation=4))
    change('false-root-rollback',lambda b:b['search'].update(root_restored=False))
    change('skipped-first-choice',lambda b:b['search']['tree']['children'].pop(0))
    change('false-status',lambda b:b['search'].update(status='exhausted_finite_marked_region'))
    change('changed-erased-command',lambda b:b['records'][-1]['request']['proof'][0].update(rule='tautology'))
    change('invented-tautology-guard',lambda b:b['compiled']['tautologies'].append(b['case']['target']))
    change('changed-searched-proof',lambda b:b['proof'][0].update(rule='tautology'))
    return tests
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True,parents=True);data=load('native-receptor-points-001.json.gz');need((data['program_sha256'],data['micro_sha256'],data['literal_table_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'fixed native authority')
    for field,root in (('sources',HERE),('reused_sources',HERE),('reused_inputs',DOCS)):
        for n,p in data[field].items():need(sha(root/n)==p,'frozen source/input '+n)
    micro=load('proof-boundary-microcode-001.json.gz');template=json.loads((DOCS/'proof-boundary-001.json').read_text())['cases'][0]['initial'];(TMP/'code.bin').write_bytes(code_bytes(micro))
    need(len(data['observations'])==2*len(data['cases']) and {(o['case'],o['mode']) for o in data['observations']}=={(c['id'],m) for c in data['cases'] for m in ('points','prefix')},'every declared cold case and control')
    for source,name in (('audit_tape_micro.cpp','native'),('micro_line_check.cpp','checker')):subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    observations=[];queries=steps=nodes=0;all_requests={};first=None;finite=[]
    for obs in data['observations']:
        r=json.loads(artifact(obs['artifact']));need(r['case']==next(c for c in data['cases'] if c['id']==obs['case']) and r['mode']==obs['mode'],'external assertion binding')
        for k in ('status','queries','cold_seconds'):need(r[k]==obs[k],'cold summary '+k)
        if r['mode']=='points':
            model,n=point_binding(r);nodes+=n
            if model is not None:finite.append(dict(case=obs['case'],**equivalence(r['case'],model)))
            requests=[]
            for rec in r['records']:
                if rec['purpose']=='tautology_instance':f=r['compiled']['basis'][rec['basis_index']];proof=[dict(rule='tautology',formula=f)];target=f
                else:proof=[model['domains'][j][next(i for i,c in enumerate(model['domains'][j]) if c==cmd)] for j,cmd in enumerate(r['proof'])];target=r['case']['target']
                requests.append(dict(protocol='gcts-fol-1',theory=r['case']['theory'],blocks=[],proof=proof,target=target))
            if first is None and r['proof']:first=r
        else:
            control=copy.deepcopy(r['chronological']);control.update(case=r['case'],records=r['records']);requests=chronological_tree(control)
        need(len(requests)==r['queries']==len(r['records']),'all native queries')
        for request,rec in zip(requests,r['records']):
            need(rec['request']==request and rec['request_sha256']==pin(request),'entire native request and external theory')
            initial_value=initial_for(micro,template,request);expected_words=dict(fixed=initial_value['words'][micro['boundary']['problem']][:-1],free=initial_value['words'][micro['boundary']['certificate']][:-1]);need(rec['boundary_words']==expected_words,'independent byte-exact wire encoding');(TMP/'input.bin').write_bytes(input_bytes(initial_value));need(sha(TMP/'input.bin')==rec['input_sha256'],'native initial binding');native=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',r['case'].get('micro_steps',10**9)))
            for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(native[k])==str(rec['result'][k]),'independent all-query native replay '+k)
            need(rec['result']['start']==micro['start'] and sha(TMP/'output.bin')==rec['output_sha256'],'true start and full output');queries+=1;steps+=native['micro_steps']
            if native['status'] in ('accepted','rejected'):
                try:logical=whole_replay(request)['status']
                except ValueError:logical='rejected'
                need(logical==native['status'],'logical cross-check, audit only')
            if rec['id']==r.get('verification_query') and native['status']=='accepted':all_requests[pin(request)]=request
        observations.append(dict(case=obs['case'],mode=obs['mode'],status=r['status'],queries=r['queries']));print(obs['case'],obs['mode'],'all queries and point nodes checked',flush=True)
    certificates=[]
    for row in data['certificates']:
        request=all_requests[row['request_sha256']];need(row['request']==request,'certificate really discovered');initial_value=initial_for(micro,template,request);need(initial_value==row['initial'],'whole certificate boot frame');(TMP/'input.bin').write_bytes(input_bytes(initial_value));(TMP/'grammar.bin').write_bytes(artifact(row['grammar']));events=[json.loads(v) for v in artifact(row['events']).splitlines()];write_cuts([e['node'] for e in events if e['kind']=='fragment'],TMP/'observed.bin');checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**9,1500000000,TMP/'root.json',TMP/'observed.bin'))
        need(checked['status']=='checked_response' and checked['result']=='accepted' and sha(TMP/'output.bin')==row['output_sha256'],'whole native response derivation');root=json.loads((TMP/'root.json').read_text());need(root==json.loads(artifact(row['responses'])),'all whole response interfaces');chain=checked_chain(row,micro,events,root);need(chain['final']==row['output'],'decoded real native contexts');certificates.append(dict(name=row['name'],request_sha256=row['request_sha256'],lines=chain['lines'],contexts=chain['contexts'],fragments=chain['fragments'],checked=checked));print(row['name'],'entire native certificate derived',len(chain['lines']),flush=True)
    result=dict(version='native-receptor-points-audit-001',status='passed',producer_sha256=sha(DOCS/'native-receptor-points-001.json.gz'),source_sha256=sha(HERE/'audit_native_receptor_points.py'),queries=queries,micro_steps=steps,point_nodes=nodes,finite_equivalence=finite,observations=observations,certificates=certificates,mutations_rejected=corruptions(first),seconds=time.perf_counter()-began,scope='Independent point-domain construction and all visited graph nodes; every recorded native query rerun; small complete-word differential checks against a separate logical kernel; all accepted native response DAGs checked again. General compiler soundness and universality proofs remain open.')
    (DOCS/'native-receptor-points-audit-001.json.gz').write_bytes(gzip.compress(packed(result),mtime=0));print('audit passed',queries,nodes,round(result['seconds'],3),flush=True)
if __name__=='__main__':main()
