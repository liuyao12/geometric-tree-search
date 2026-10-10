"""All cold native trees, independently mined families, matching and learning."""
import copy,gzip,hashlib,json,math,random,statistics,time
from collections import Counter
from pathlib import Path
from check_native_wang import Reference,need
from check_native_rectangle import Primitive
from audit_native_wang_search import Replay,cone
import check_native_families as F
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(ref):
    p=DOC/ref['file'];need(sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes'],'whole cold trace digest');return json.loads(gzip.decompress(p.read_bytes()))
def preferred_options(ref,blocks,keys):
    first=sorted(set(tuple(k) for k in keys));yield from first
    yield from (v for v in ref.options(blocks) if v not in first)
class FamilyReplay(Replay):
    def __init__(self,ref,row,library):super().__init__(ref,row);self.library=library;self.matches=self.actions=self.reviews=0
    def check(self):
        r=self.r;census,_=self.census();need(census==r['initial_census'] and sum(n for _,n in census)==r['initial_candidate_nodes'],'complete native initial graph');rng=random.Random(r['seed']);agenda=();completed=();frames=[];pending=None;terminal=None;metrics=Counter();attempts=forced=branches=backtracks=policies=hints=0
        for e in r['events']:
            if e['kind']=='alternative':
                need(pending is not None,'native fallback expected');p,key,hint=pending;pending=None;need(e['point']==list(p) and e['key']==list(key) and e['depth']==len(self.order) and e['hint']==(hint['id'] if hint else None),'exact native fallback and hint restoration');role='member' if hint and any(tuple(q)==p and tuple(v)==key for q,v in hint['item']['members']) else 'unrelated' if hint else 'base';need(e['role']==role,'fallback family role');metrics['role_'+role]+=1;self.values[p]=key;self.order.append(p);attempts+=1;continue
            need(pending is None and terminal is None,'no skipped original alternative or terminal');census,domains=self.census();need(census==e['census'] and e['depth']==len(self.order),'all global native frontier counts');dead=[p for p,v in domains.items() if v[1]==0];single=[p for p,v in domains.items() if v[1]==1]
            if dead:kind='dead';point=min(dead,key=lambda p:(p[1],p[0]))
            elif single:kind='forced';point=min(single,key=lambda p:(p[1],p[0]))
            elif domains:kind='branch';point=min(domains,key=lambda p:(domains[p][1],p[1],p[0]))
            else:kind='empty';point=None
            need((e['kind'],e['point'],e['count'])==(kind,None if point is None else list(point),None if point is None else domains[point][1]),'global dead/forced/earliest-generation native decision');need(e['agenda_in']==[h['id'] for h in agenda],'restored pending-family agenda');kept=[];reviews=[];active=None;trace=dict(phase='none',pending=[],eligible=[])
            for hint in agenda:
                current,review=F.review(self,hint,kind,point);reviews.append(dict(id=hint['id'],**review));metrics['hint_reviews']+=1;metrics['hint_'+review['phase']]+=1;self.reviews+=1
                if review['phase']=='completed':completed+=(hint['id'],)
                if current:
                    kept.append(current)
                    if active is None and review['eligible']:active=current;trace=review
            need(e['reviews']==reviews,'every native hint lifetime and absent-member semantics');agenda=tuple(kept)
            if kind=='empty':terminal='finite_exact_native_rectangle';continue
            if kind=='dead':
                while frames:
                    prior,p,options,parent_agenda,parent_completed,identity=frames[-1];self.values=prior.copy();self.order=list(prior);agenda=parent_agenda;completed=parent_completed;hint=next((h for h in agenda if h['id']==identity),None)
                    try:key=next(options)
                    except StopIteration:frames.pop();backtracks+=1;continue
                    pending=p,key,hint;backtracks+=1;break
                if pending is None:terminal='exhausted_finite_native_rectangle'
                continue
            if kind=='branch' and active is None and self.library and r['mode']!='base':
                pool,work=F.proposals(self,self.library,point,r['limits']['proposal_limit']);need(e['proposal_pool']==pool,'every complete bounded native family pool');self.matches+=1
                for k,v in work.items():metrics['proposal_'+k]+=v
                item,decision=F.policy(self,pool,F.FIXED if r['mode']=='fixed' else r['weights'],r['stochastic'] if r['mode']=='policy' else False,rng);decision.update(id=policies,depth=len(self.order),point=list(point),items=pool);need(e['policy_event']==policies and r['policy_events'][policies]==json.loads(canonical(decision)),'all scores, softmax, actual draws and likelihood gradients');policies+=1;self.actions+=1
                if item is not None:
                    record=dict(id=hints,chosen=[[list(p),list(self.values[p])] for p in self.order],point=list(point),item=item);need(r['hints'][hints]==record and e['hint_start']==hints,'exact native family start');active=dict(id=hints,item=item,waiting=False);active,trace=F.review(self,active,kind,point);need(active is not None and trace['eligible'] and e['start_review']==trace,'new family must attach to scheduled receptor');agenda+=(active,);metrics['hint_started']+=1;hints+=1
            preferred=trace['eligible'] if active else ();options=iter(self.ref.options(domains[point][0])) if kind=='forced' else iter(preferred_options(self.ref,domains[point][0],preferred));key=next(options);need(e['key']==list(key),'first preferred or original native tile');role='member' if active and list(key) in preferred else 'unrelated' if active else 'base';need(e['role']==role and e['hint_used']==(active['id'] if active else None),'actual native member role');metrics['role_'+role]+=1
            if kind=='branch':frames.append((self.values.copy(),point,options,agenda,completed,active['id'] if active else None));branches+=1
            else:forced+=1
            self.values[point]=key;self.order.append(point);attempts+=1
        need(pending is None and (attempts,forced,branches,backtracks)==(r['attempts'],r['forced'],r['branches'],r['backtracks']),'all native attempts and backtracks');need(r['status']==(terminal or 'unknown_search_budget'),'tri-state native result')
        if terminal is None:need(attempts>=r['limits']['attempts'] or r['seconds']>=r['limits']['seconds'],'actual native resource cutoff')
        need(policies==len(r['policy_events']) and hints==len(r['hints']) and list(completed)==r['solution_hints'],'complete sampled events and path-restored completions');need([(t['x'],t['y']) for t in r['tiles']]==self.order and all(self.values[t['x'],t['y']]==tuple(t['triple']) for t in r['tiles']),'actual native partial or positive leaf');need(dict(metrics)=={k:v for k,v in r['metrics'].items() if k!='proposal_seconds'},'all declared proposal/review/role counters');return self.states
def completed_clusters(primitive,row):
    r=row['result'];selected={(t['x'],t['y']):t for t in r['tiles']};out=[]
    for identity in r['solution_hints']:
        h=r['hints'][identity];marks={};seen=set()
        for p,key in h['item']['members']:
            p=tuple(p);need(p not in seen and selected[p]['triple']==key,'distinct completed original native members');seen.add(p);n=primitive.output(key)
            for q,v in F.assignments(p,key,n,primitive).items():need(q not in marks or marks[q]==v,'completed original native union');marks[q]=v
        need(h['item']['marks']==[[list(q),list(v) if isinstance(v,tuple) else v] for q,v in sorted(marks.items())],'exact completed family marking union');out.append(dict(id=identity,cells=len(seen),level=h['item']['level'],status='accepted_original_native_cluster'))
    need(out==r['cluster_checks'],'independent completed-cluster checks')
def check_row(ref,primitive,row,library):
    r=row['result'];need(r['projected'] is True and r['extended'] is False and row['library_sha256']==hashlib.sha256(canonical(library)).hexdigest(),'fixed marking layer and input inventory');head,pins=cone(row['spec'],ref.A);cert=row['certificate'];need(cert['head_position']==head and cert['pins']==pins and cert['pattern']==row['spec']['pattern'] and cert['height']==row['spec']['height'] and r['boundary']==row['spec']['boundary']+pins,'complete original and certified root boundary')
    for name,decorated in (('original',False),('decorated',True)):need(r['point_checks'][name]==primitive.check(row['spec'],r,decorated),'original/decorated native point certificate')
    completed_clusters(primitive,row)
    for q in row['domain_queries']:need(ref.count(q['role'],q['north'],q['allowed'])==q['count'],'every full counted native domain')
    replay=FamilyReplay(ref,row,library);states=replay.check();semantic={k:v for k,v in r.items() if k not in ('seconds','total_seconds','preparation_seconds','verification_seconds','peak_process_rss_bytes','metrics')};semantic['metrics']={k:v for k,v in r['metrics'].items() if k!='proposal_seconds'};need(hashlib.sha256(canonical(semantic)).hexdigest()==row['semantic_sha256'],'full native semantic hash');need(r['root_rollback_verified'] is True and r['total_seconds']>=r['preparation_seconds']+r['seconds']+r['verification_seconds']>=0 and r['peak_process_rss_bytes']>0,'root witness and cold clock algebra');return states,replay.matches,replay.actions,replay.reviews
def main():
    began=time.perf_counter();path=DOC/'native-families-001.json';data=json.loads(path.read_text())
    for n,pin in data['sources'].items():need(sha(HERE/n)==pin,'measured source '+n)
    for n,pin in data['reused_inputs'].items():need(sha(DOC/n)==pin,'fixed input '+n)
    refs=[d['raw'] for d in data['donors']]+[e['raw'] for e in data['training']['episodes']]+[r for c in data['cases'] for r in c['runs']];rows=[load(v) for v in refs];raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());need(hashlib.sha256(raw).hexdigest()==data['literal_table_sha256'],'fixed original palette');reference=Reference(raw,[q for row in rows for q in row['domain_queries']]);primitive=Primitive(raw);totals=Counter();donors=[];library=[];sampled=chosen=0
    def examine(row,ref,lib):
        result=check_row(reference,primitive,row,lib)
        for k,v in zip(('states','joins','actions','reviews'),result):totals[k]+=v
        totals['searches']+=1;totals['queries']+=len(row['domain_queries']);totals['positive']+=row['result']['status']=='finite_exact_native_rectangle';need(ref['semantic_sha256']==row['semantic_sha256'] and ref['status']==row['result']['status'] and ref['attempts']==row['result']['attempts'] and ref['total_seconds']==row['result']['total_seconds'] and ref['stage_seconds']>=ref['total_seconds'],'whole cold observation binding')
    for d in data['donors']:
        need(d['input_library']==library,'cold prior native inventory');row=load(d['raw']);need(row['spec']==d['spec'],'cold donor input');examine(row,d['raw'],library);donors.append(row);library,mining=F.mine(donors)
    need(library==data['library'] and canonical(mining)==canonical({k:v for k,v in data['mining'].items() if k!='seconds'}),'independently reconstructed native families and hierarchy');weights=[0.]*8;baselines={s['id']:0. for s in data['training']['specs']};need(data['training']['initial_weights']==weights and tuple(data['training']['features'])==F.FEATURES,'zero shared parameter start')
    for number,e in enumerate(data['training']['episodes']):
        row=load(e['raw']);r=row['result'];need((e['epoch'],e['index'])==divmod(number,len(data['training']['specs'])) and row['spec']==data['training']['specs'][e['index']] and e['weights_before']==weights and r['weights']==weights and r['stochastic'] is True and r['seed']==59000+number,'cold sampled training input');examine(row,e['raw'],library);value=int(r['status']=='finite_exact_native_rectangle')-math.log1p(r['total_seconds']/.001)/math.log1p(r['limits']['seconds']/.001);baseline=baselines[row['spec']['id']];gradient=[sum(a['gradient'][j] for a in r['policy_events']) for j in range(8)];after=[max(-6.,min(6.,w+2*(value-baseline)*g)) for w,g in zip(weights,gradient)];change=dict(reward=value,baseline_before=baseline,advantage=value-baseline,gradient=gradient,rate=2.,weights_after=after);need(e['update']==change,'every actual likelihood-ratio update');weights=after;baselines[row['spec']['id']]=.9*baseline+.1*value;sampled+=len(r['policy_events']);chosen+=sum(a['selected']>0 for a in r['policy_events'])
    need(len(data['training']['episodes'])==data['training']['epochs']*len(data['training']['specs']) and weights==data['training']['weights'] and baselines==data['training']['baselines'],'frozen shared policy and complete training');pairs=0
    for index,c in enumerate(data['cases']):
        for v in c['runs']:
            row=load(v);r=row['result'];lane=v['lane'];off=(index+v['repetition'])%4;lanes=list(data['lanes']);need(list(v['order'])==lanes[off:]+lanes[:off] and row['spec']==c['spec'] and r['stochastic'] is False,'balanced independent cold input');mode='base' if lane=='marks' else 'fixed' if lane=='families' else 'policy';ws=weights if lane=='rl' else [0.]*8 if lane=='zero' else None;need(r['mode']==mode and r['weights']==ws,'frozen native control');examine(row,v,[] if lane=='marks' else library)
        for lane in data['lanes']:
            samples=[r for r in c['runs'] if r['lane']==lane];need(c['timings'][lane]['samples']==samples and sorted(v['repetition'] for v in samples)==list(range(4)) and c['timings'][lane]['median_seconds']==statistics.median(v['total_seconds'] for v in samples),'every native repeat and median')
        for rep in range(4):
            a=load(next(v for v in c['runs'] if v['lane']=='marks' and v['repetition']==rep))['result'];b=load(next(v for v in c['runs'] if v['lane']=='zero' and v['repetition']==rep))['result'];fields=('kind','point','key','count','depth','census');strip=lambda r:[{k:v for k,v in e.items() if k in fields} for e in r['events']];need((a['status'],a['tiles'],strip(a))==(b['status'],b['tiles'],strip(b)),'zero-policy complete original controller equality');pairs+=1
        print(c['spec']['id'],'all sixteen complete native trees and zero pairs passed',flush=True)
    positive=next(load(v) for c in data['cases'] for v in c['runs'] if v['lane']=='rl' and v['status']=='finite_exact_native_rectangle' and load(v)['result']['hints']);mutations=[]
    for kind in ('census','selector','tile','generation','cone','binding','aggregate','scores','probability','gradient','agenda','fallback','completion'):
        bad=copy.deepcopy(positive);r=bad['result']
        if kind=='census':r['events'][0]['census'][0][1]+=1
        elif kind=='selector':bad['domain_queries'][0]['count']+=1
        elif kind=='tile':r['tiles'][0]['N']+=1
        elif kind=='generation':r['tile_generations'][0]=2
        elif kind=='cone':bad['certificate']['pins'][0][1]=0
        elif kind=='binding':next(iter(r['policy_events'][0]['items'][0]['binding']));r['policy_events'][0]['items'][0]['binding']['s0']+=1
        elif kind=='aggregate':r['hints'][0]['item']['marks'][0][1]=0
        elif kind=='scores':r['policy_events'][0]['scores'][0]+=1
        elif kind=='probability':r['policy_events'][0]['probabilities'][0]+=1
        elif kind=='gradient':r['policy_events'][0]['gradient'][0]+=1
        elif kind=='agenda':next(e for e in r['events'] if e['agenda_in'])['agenda_in']=[]
        elif kind=='fallback':next(e for e in r['events'] if e['kind']=='branch')['key'][0]+=1
        else:r['solution_hints']=[]
        semantic={k:v for k,v in r.items() if k not in ('seconds','total_seconds','preparation_seconds','verification_seconds','peak_process_rss_bytes','metrics')};semantic['metrics']={k:v for k,v in r['metrics'].items() if k!='proposal_seconds'};bad['semantic_sha256']=hashlib.sha256(canonical(semantic)).hexdigest()
        try:check_row(reference,primitive,bad,library)
        except (ValueError,KeyError,IndexError,StopIteration):mutations.append(kind)
        else:raise ValueError('accepted corrupted native family '+kind)
    out=dict(version='native-families-audit-001',status='passed',input_sha256=sha(path),source_sha256=sha(__file__),helpers={n:sha(HERE/n) for n in ('check_native_families.py','check_native_wang.py','check_native_rectangle.py','audit_native_wang_search.py')},counts=dict(totals),zero_original_pairs=pairs,sampled_actions=sampled,sampled_families=chosen,mutations_rejected=mutations,seconds=time.perf_counter()-began,scope='Every donor, training and repeated evaluation tree: full raw-table selectors/frontier censuses, independent cold family mining, typed live receptor binding, every bounded proposal pool, aggregate guards, concurrent hint lifetimes/restoration, complete original fallback, all softmax draws/gradients/updates, actual native leaves, original/decorated points and completed clusters, digests and clock algebra. Physical clock authenticity, summed native-plus-Python RSS, logical macro compilation and full mathematical theorem discovery remain outside this audit.')
    (DOC/'native-families-audit-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
