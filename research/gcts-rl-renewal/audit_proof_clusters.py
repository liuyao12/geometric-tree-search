"""Independent cluster compilation, scheduler, full-tree and hierarchy replay.

No proposer, miner, point graph, catalog generator or producer imports.
Literal bounded base inventories and proofs use the notebook 29 independent
auditor; cluster indexes are reconstructed here by separate term matching.
"""
import copy,hashlib,itertools,json,time
from pathlib import Path
import logic as L
import audit_semantic_proofs as A
from audit_proof_compaction import native_binding
from audit_serialized_kernel import freeze

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(x):return hashlib.sha256(A.packed(x)).hexdigest()
def match(p,t,variables,env):
    if p[0]=='var' and p[1] in variables:
        if p[1] in env:return env[p[1]]==t
        env[p[1]]=t;return True
    if p[0]=='var':return p==t
    return t[0]=='fun' and p[1]==t[1] and len(p[2])==len(t[2]) and all(match(a,b,variables,env) for a,b in zip(p[2],t[2]))
def goal_path(c,placements,n):
    by={k[0]:k for k in placements};out=[];slot=n-1
    while True:
        key=by[slot];A.need(key not in out,'acyclic equation chain');out.append(key)
        if not key[2]:break
        A.need(len(key[2])==1 and key[2][0]<slot,'single earlier equality premise');slot=key[2][0]
    return out[::-1]
def index(c,n,library,cap):
    terms=[a[2] for a in c['formulas']];allowed=set(terms);lookup={};items=[]
    for rid,r in enumerate(c['rules']):
        if r['recipe']['kind']=='block':
            p=r['recipe'];m=p['move'];lookup[sha([m['before'],m['after'],p['axiom'],m['bindings'],m['path'],m['direction']])]=rid
    for t in library:
        k=len(t['actions'])
        for before in terms:
            for context,sub in A.locations(before):
                for direction in (1,-1):
                    env={};pattern=t['before'] if direction==1 else t['after']
                    if not match(pattern,sub,set(t['variables']),env):continue
                    unbound=[x for x in t['variables'] if x not in env]
                    for values in itertools.product(terms,repeat=len(unbound)):
                        bindings=dict(env,**dict(zip(unbound,values)));current=before;rules=[]
                        steps=t['actions'] if direction==1 else t['actions'][::-1]
                        for move in steps:
                            expected=A.substitute_term(move['before'] if direction==1 else move['after'],bindings);new=A.substitute_term(move['after'] if direction==1 else move['before'],bindings)
                            if dict(A.locations(current)).get(context)!=expected:rules=[];break
                            after=A.put(current,context,new);inst={x:A.substitute_term(term,bindings) for x,term in move['bindings'].items()};p=context+move['path'];rid=lookup.get(sha([current,after,move['rule'],inst,p,move['direction']*direction]))
                            if after not in allowed or rid is None:rules=[];break
                            rules.append(rid);current=after
                        if len(rules)!=k:continue
                        for start in range(1,n-k+1):
                            for ref in range(start):
                                item=dict(template=t['name'],members=tuple((start+i,r,(ref if i==0 else start+i-1,)) for i,r in enumerate(rules)),instance=dict(before=before,after=current,bindings=bindings,context=context,direction=direction),level=t['level'])
                                if len(items)>=cap:return items,False
                                items.append(item)
    return items,True
class Points:
    def __init__(self,c,n):self.c=c;self.n=n;self.universe=A.candidates(c,n);self.cache={};self.samples=0
    def domains(self,order):
        key=tuple(sorted(order))
        if key not in self.cache:self.cache[key]=A.domains(self.universe,self.n,self.c['target_id'],order)
        return self.cache[key]
    def offered(self,items,order,point,limit):
        ds=self.domains(order);out=[]
        for item in items:
            if point not in [key[0] for key in item['members']]:continue
            if any(key not in ds.get(key[0],()) for key in item['members']):continue
            try:self.domains(tuple(order)+item['members'])
            except ValueError:continue
            out.append(item)
        out.sort(key=lambda x:(-int(any(key[0]==self.n-1 for key in x['members'])),-len(x['members']),-x['level'],sha(x)))
        return out[:limit],len(out)
    def transaction(self,order,item,trace):
        current=list(order);pending=set(item['members']);A.need(len(pending)==len(item['members']),'distinct cluster constituents')
        for step in trace['steps']:
            ds=self.domains(current);kind,p,keys=A.decision(ds);A.need(kind in ('forced','branch'),'transaction cannot pass a dead/empty graph')
            expected=keys[0] if kind=='forced' else min(pending.intersection(keys),default=None)
            A.need(expected is not None and step['kind']==kind and step['point']==(2*p,0) and step['key']==expected,'global scheduler and complete transaction domain')
            A.need(step['role']==('member' if expected in pending else 'global_forced'),'forced outside-cluster ownership');pending.discard(expected);current.append(expected)
        kind,p,keys=A.decision(self.domains(current));status=trace['status']
        if status=='accepted_cluster':A.need(not pending and kind!='dead','complete viable cluster')
        elif status=='rejected_dead':A.need(kind=='dead','proved dead rejection')
        elif status=='rejected_scheduler':A.need(pending and kind=='branch' and not pending.intersection(keys),'scheduler refusal is not a logical failure')
        elif status=='rejected_incomplete_cluster':A.need(pending and kind=='empty','incomplete-cluster rejection')
        elif status=='unknown_transaction_budget':A.need(pending,'incomplete budget trace remains unknown')
        else:raise ValueError('unknown transaction result')
        return current
def run_audit(c,n,r,library,points=None):
    points=points or Points(c,n);items,complete=index(c,n,library,r['limits']['index_instances']);A.need(len(items)==r['index_instances'] and complete==r['index_complete'],'independently reconstructed proposal index');A.need(sha(library)==r['library_sha256'],'frozen library version');A.need(len(points.universe)==r['candidate_universe'],'unchanged complete base universe')
    for sample in r['samples']:
        ds=points.domains(sample['order']);kind,p,keys=A.decision(ds);A.need(sample['kind']==kind and sample['point']==((2*p,0) if p is not None else None),'global sample decision');A.need(sample['degrees']=={str((2*i,0)):len(v) for i,v in ds.items()},'every sampled base degree')
    for sample in r['transaction_samples']:
        A.need(sample['item'] in items,'sample belongs to compiled proposal index');points.transaction(sample['order'],sample['item'],sample['trace'])
    ds=points.domains(r['placements']);solved=r['status']=='finite_exact_proof_tiling';A.need(not solved or not ds,'whole exact target');A.need(r['tile_generations']==(1,)*len(r['placements']),'root and tile generations')
    stats=dict(nodes=0,base_attempts=0,branches=0,forced=0,backtracks=0,proposal_trials=0,proposal_rejections=0,accepted_proposal_trials=0,singleton_attempts=0,validation_placements=0,constituent_branch_steps=0,constituent_forced_steps=0);leaf=None;leaf_transactions=[]
    def visit(tree,order,transactions):
        nonlocal leaf,leaf_transactions
        stats['nodes']+=1;kind,p,keys=A.decision(points.domains(order));A.need(tree['kind']==kind,'complete saved tree node');A.need(p is None or tree['point']==(2*p,0),'chosen tree point')
        if kind=='dead':return False
        if kind=='empty':leaf=order;leaf_transactions=transactions;return True
        stats['forced' if kind=='forced' else 'branches']+=1;offered=[]
        if kind=='branch' and library:offered,count=points.offered(items,order,p,r['limits']['proposal_limit'])
        if r['mode']=='rank' and kind=='branch' and library:
            A.need(tree['ranking_items']==tuple(offered),'same proposal prior for rank-only');priority=[]
            for item in offered:
                for key in item['members']:
                    if key in keys and key not in priority:priority.append(key)
            keys=priority+[key for key in keys if key not in priority]
        proposals=tree['proposals'];A.need(tuple(x['item'] for x in proposals)==tuple(offered[:len(proposals)]) if r['mode']=='clusters' else not proposals,'actual proposal-order prefix')
        for j,trial in enumerate(proposals):
            trace=trial['trace'];child=points.transaction(order,trial['item'],trace);stats['proposal_trials']+=1;stats['base_attempts']+=len(trace['steps']);stats['validation_placements']+=len(trace['steps']);stats['constituent_branch_steps']+=sum(s['kind']=='branch' for s in trace['steps']);stats['constituent_forced_steps']+=sum(s['kind']=='forced' for s in trace['steps'])
            if trace['status']!='accepted_cluster':stats['proposal_rejections']+=1;continue
            stats['accepted_proposal_trials']+=1
            transaction=dict(trial['item'],steps=trace['steps'])
            if visit(trial['tree'],child,transactions+[transaction]):A.need(j==len(proposals)-1 and not tree['children'],'stop on first successful proposal');return True
            stats['backtracks']+=1
        if r['mode']=='clusters':A.need(len(proposals)==len(offered),'all offered proposals tried before base fallback')
        children=tree['children'];A.need(tuple(x['key'] for x in children)==tuple(keys[:len(children)]),'every ordered base alternative remains')
        for j,child in enumerate(children):
            stats['base_attempts']+=1;stats['singleton_attempts']+=1
            if visit(child['tree'],order+[child['key']],transactions):A.need(j==len(children)-1,'stop on first base solution');return True
            stats['backtracks']+=1
        A.need(len(children)==len(keys),'full finite base exhaustion');return False
    if r['search_tree'] is not None:
        A.need(visit(r['search_tree'],[],[])==solved,'tree result');A.need(stats['nodes']==r['nodes'] and stats['base_attempts']==r['base_attempts'],'all recursive/constituent work')
        for k,v in stats.items():A.need(r['stats'].get(k,0)==v,'complete counter '+k)
        if solved:A.need(tuple(leaf)==r['placements'] and tuple(leaf_transactions)==r['solution_transactions'],'actual solution transactions and placements')
    else:A.need(r['status']=='unknown_search_budget','only unknown budget omits complete tree')
    if solved:A.check_decoded(c,n,r)
    return dict(full_tree_nodes=stats['nodes'],index_instances=len(items),transactions=stats['proposal_trials'],domain_samples=len(r['samples']),solved=solved)
def hierarchy_audit(c,n,r,h,library):
    original=r['decoded']['request'];request=h['request'];A.need(request['theory']==c['theory'] and request['target']==c['target'],'unchanged hierarchical external problem');A.need(h['input_check']['certificate_sha256']==sha(original) and h['check']['certificate_sha256']==sha(request),'entire input/output proof bindings')
    checked=A.whole_replay(json.loads(A.packed(request)),A.pin(request));A.need(checked['status']=='accepted','every nested definition and root prefix independently check')
    commands=goal_path(c,r['placements'],n);used=h['transactions_used'];mapping={};cursor=0;seen=[];i=0;by_name={b['name']:b for b in request['blocks']};available={t['name']:t['definition'] for t in library};available.update({x['recipe']['definition']['name']:x['recipe']['definition'] for x in c['rules'] if x['recipe']['kind']=='block'})
    while i<len(commands):
        key=commands[i];rule=c['rules'][key[1]];a=c['formulas'][rule['output']];choices=[t for t in r['solution_transactions'] if t['members']==tuple(commands[i:i+len(t['members'])]) and i+len(t['members'])<=len(commands)]
        if choices:
            t=max(choices,key=lambda x:len(x['members']));record=used[len(seen)];A.need(record['template']==t['template'] and record['members']==t['members'] and record['instance']==t['instance'] and record['root_line']==cursor,'only actual goal-chain transactions compact')
            anchor=c['formulas'][rule['inputs'][0]][1];p=L.Eq(anchor,t['instance']['before']);q=L.Eq(anchor,t['instance']['after']);name='cluster-instance-'+sha([t['template'],t['instance'],anchor])[:20];A.need(record['definition']==name,'compiled instance name');b=by_name[name];A.need(b['premises']==(p,) and b['conclusion']==q,'exact compiled interface');A.need([l['name'] for l in b['proof'] if l['rule']=='block']==[t['template']],'real learned theorem call');available[name]=b;expected=dict(rule='block',formula=q,name=name,inputs=(mapping[key[2][0]],));A.need(request['proof'][cursor]==expected,'hierarchical root call');mapping[commands[i+len(t['members'])-1][0]]=cursor;cursor+=1;i+=len(t['members']);seen.append(record);continue
        recipe=rule['recipe'];mapped=[mapping[ref] for ref in key[2]]
        if recipe['kind']=='primitive':expected=[recipe['witness']]
        elif recipe['kind']=='copy':expected=[dict(rule='tautology',formula=L.Imp(a,a)),dict(rule='mp',formula=a,antecedent=mapped[0],implication=cursor)]
        else:expected=[dict(rule='block',formula=a,name=recipe['definition']['name'],inputs=tuple(mapped))]
        A.need(request['proof'][cursor:cursor+len(expected)]==tuple(expected),'exact retained base commands');cursor+=len(expected);mapping[key[0]]=cursor-1;i+=1
    for x in reversed(c['close_variables']):a=L.All(x,request['proof'][cursor-1]['formula']);A.need(request['proof'][cursor]==dict(rule='generalize',formula=a,variable=x,source=cursor-1),'final universal closure');cursor+=1
    A.need(cursor==len(request['proof'])==h['root_lines'] and len(seen)==len(used),'all root commands and used transactions');A.need(h['original_root_lines']==len(original['proof']) and h['definitions']==len(by_name),'reported hierarchy sizes')
    reachable=set()
    def deps(lines):
        for l in lines:
            if l['rule']=='block' and l['name'] not in reachable:
                reachable.add(l['name']);A.need(l['name'] in available and by_name[l['name']]==available[l['name']],'unchanged earlier definitions');deps(by_name[l['name']]['proof'])
    deps(request['proof']);A.need(reachable==set(by_name),'no unused or unrelated hierarchy definitions')
    return dict(root_lines=cursor,blocks=len(by_name),transactions=len(used),expanded_lines=A.replay(A.packed(request),A.pin(request))['expanded_lines'])
def external():
    z=L.F('zero');s=lambda x:L.F('succ',x);plus=lambda a,b:L.F('add',a,b);x,y=L.V('x'),L.V('y');theory=dict(functions=dict(zero=0,succ=1,add=2),predicates={},axioms=dict(AZ=L.All('x',L.Eq(plus(x,z),x)),AS=L.All('x',L.All('y',L.Eq(plus(x,s(y)),s(plus(x,y)))))),schemas=[])
    def num(n):return z if not n else s(num(n-1))
    donors={};evaluation={}
    def record(target,n,bound,t=theory):return dict(theory=t,target=target,length=n,term_bound=bound)
    for n in (1,2):
        a=L.V('a');b=a
        for _ in range(n):b=s(b)
        donors[f'donor-{n}']=record(L.All('a',L.Eq(plus(a,num(n)),b)),n+2,n+4)
    for a,b in ((1,1),(2,2),(0,3),(2,3)):evaluation[f'add-{a}-{b}']=record(L.Eq(plus(num(a),num(b)),num(a+b)),b+2,a+b+3)
    one,two,three=num(1),num(2),num(3);evaluation.update({'successor-context':record(L.Eq(s(plus(one,two)),num(4)),4,7),'nested-left':record(L.Eq(plus(plus(one,one),one),three),5,8),'nested-right':record(L.Eq(plus(one,plus(one,one)),three),6,8),'short-envelope':record(L.Eq(plus(z,two),two),3,5),'different-target':record(L.Eq(plus(z,one),two),3,4)})
    arithmetic=copy.deepcopy(theory);arithmetic['functions']['mul']=2;m=lambda a,b:L.F('mul',a,b);arithmetic['axioms'].update(MZ=L.All('x',L.Eq(m(x,z),z)),MS=L.All('x',L.All('y',L.Eq(m(x,s(y)),plus(m(x,y),x)))));evaluation['mul-one']=record(L.Eq(m(one,one),one),5,7,arithmetic);return donors,evaluation
def audit(path=DOCS/'proof-clusters-001.json'):
    began=time.perf_counter();path=Path(path);d=json.loads(path.read_text());data=freeze(d);donors,evaluation=external();library=[];donor_reports=[];eval_reports=[];code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program']
    for n,h in d['sources'].items():A.need(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h,'source '+n)
    A.need(not data['initial_library'] and len(data['donors'])==2,'cold donor source set')
    def bind_problem(p,external):A.need(all(p[k]==freeze(v) for k,v in external.items()),'independent external statement')
    for row in data['donors']:
        p=row['problem'];bind_problem(p,donors[p['id']]);c=row['catalog'];A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'],'donor base grammar');inventory=A.equation_inventory(c);A.need(row['input_library']==tuple(t['name'] for t in library),'earlier-only donor library');r=row['result'];run=run_audit(c,p['length'],r,library);hierarchy=hierarchy_audit(c,p['length'],r,row['hierarchy'],library);native_binding(code,json.loads(A.packed(row['hierarchy']['request'])),json.loads(A.packed(row['native'])))
        A.need(row['native']['status']=='accepted','promotion gate is a complete machine check');moves=[];keys=[]
        for key in goal_path(c,r['placements'],p['length']):
            recipe=c['rules'][key[1]]['recipe']
            if recipe['kind']=='block':moves.append(dict(recipe['move'],rule=recipe['axiom']));keys.append(key)
        known={sha([t['before'],t['after'],t['actions']]) for t in library};expected=[]
        for i in range(len(moves)):
            for size in range(2,min(4,len(moves)-i)+1):
                fragment=moves[i:i+size];identity=sha([fragment[0]['before'],fragment[-1]['after'],fragment])
                if identity not in known:expected.append((i,i+size,fragment));known.add(identity)
        promoted=row['promotion']['templates'];A.need(len(promoted)==len(expected),'every eligible mined window')
        for t,(i,j,fragment) in zip(promoted,expected):
            A.need(t['actions']==tuple(fragment) and t['before']==fragment[0]['before'] and t['after']==fragment[-1]['after'],'literal searched fragment');A.need(t['source']==dict(problem=p['id'],certificate_sha256=sha(r['decoded']['request']),window=(i,j),members=tuple(keys[i:j])),'literal discovery provenance');vars=sorted(set().union(*(L.term_free(a['before'])|L.term_free(a['after'])|set().union(*(L.term_free(v) for v in a['bindings'].values())) for a in fragment)));A.need(t['variables']==tuple(vars),'all fragment parameters');formula=L.Eq(t['before'],t['after'])
            for x in reversed(vars):formula=L.All(x,formula)
            A.need(t['definition']['premises']==() and t['definition']['conclusion']==formula,'universally closed fragment interface');children=[];k=0;old={x['name']:x for x in library}
            while k<j-i:
                choices=[tr for tr in r['solution_transactions'] if tr['template'] in old and tr['members']==tuple(keys[i+k:i+k+len(tr['members'])]) and k+len(tr['members'])<=j-i]
                if choices:tr=max(choices,key=lambda x:len(x['members']));children.append(tr['template']);k+=len(tr['members'])
                else:k+=1
            A.need(t['children']==tuple(children) and t['level']==1+max((old[x]['level'] for x in children),default=0),'actual lower-level calls define hierarchy');A.need([l['name'] for l in t['definition']['proof'] if l['rule']=='block']==children,'real child calls in primitive proof');A.need(t['name']==t['definition']['name']=='proof-cluster-'+sha([formula,t['actions'],children])[:20],'checked type name')
        library+=list(promoted);target=L.Imp(('bot',),('bot',));probe=dict(protocol='gcts-fol-1',theory=c['theory'],target=target,blocks=[t['definition'] for t in library],proof=[dict(rule='tautology',formula=target)]);A.need(A.whole_replay(json.loads(A.packed(probe)),A.pin(probe))['status']=='accepted','every promoted type, including unused types, independently expands');donor_reports.append(dict(id=p['id'],inventory=inventory,search=run,hierarchy=hierarchy,promoted=len(promoted)))
    A.need(tuple(library)==data['library'],'exact final frozen library');probe=d['whole_library_native'];native_binding(code,probe['request'],probe['result']);A.need(freeze(probe['request']['blocks'])==tuple(t['definition'] for t in library) and freeze(probe['request']['theory'])==freeze(donors['donor-1']['theory']),'whole library native input contains every promoted definition');A.need(probe['result']['status']=='accepted','full library native check');A.need({r['problem']['id'] for r in data['evaluation']}==set(evaluation),'held-out evaluation set')
    for i,row in enumerate(data['evaluation']):
        p=row['problem'];bind_problem(p,evaluation[p['id']]);c=row['catalog'];A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'],'matched external grammar');A.need(sha(c)==row['catalog_sha256'],'exact grammar pin');inventory=A.equation_inventory(c);points=Points(c,p['length']);reports=[]
        for replica in range(2):
            lanes=['base','level1','hierarchy','rank-only'];shift=(i+replica)%4;expected=lanes[shift:]+lanes[:shift];actual=[r for r in row['runs'] if r['replica']==replica];A.need([r['lane'] for r in actual]==expected,'balanced run order')
            for run in actual:
                selected=[] if run['lane']=='base' else [t for t in library if t['level']==1] if run['lane']=='level1' else library;A.need(run['library']==tuple(t['name'] for t in selected) and run['catalog_sha256']==row['catalog_sha256'],'same base grammar; declared frozen hierarchy');r=run['result'];A.need(r['mode']==('rank' if run['lane']=='rank-only' else 'clusters'),'sequence versus singleton control');report=dict(lane=run['lane'],replica=replica,search=run_audit(c,p['length'],r,selected,points))
                if 'decoded' in r:report['hierarchy']=hierarchy_audit(c,p['length'],r,run['hierarchy'],selected);native_binding(code,json.loads(A.packed(run['hierarchy']['request'])),json.loads(A.packed(run['native'])));report['native_status']=run['native']['status']
                reports.append(report)
        eval_reports.append(dict(id=p['id'],inventory=inventory,runs=reports));print('audited',p['id'],flush=True)
    result=dict(status='passed',donors=donor_reports,evaluation=eval_reports,seconds=time.perf_counter()-began,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),dependencies={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('logic.py','audit_semantic_proofs.py','audit_serialized_kernel.py','audit_proof_compaction.py','audit_tree_kernel.py')},scope='Independent reconstruction of external targets, base rules, mined windows, source provenance, every hierarchy type, proposal indexes and every complete saved search tree/transaction. All sampled domains and all positive proof expansions checked; every native program/input bound. No independent replay of every native instruction, unknown truncated tree, or formal universal soundness claim.')
    d['independent_audit']=result;path.write_text(json.dumps(d,separators=(',',':'))+'\n');return result
if __name__=='__main__':print(json.dumps(audit(),indent=2))
