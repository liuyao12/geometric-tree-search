"""All cold native trees, counted domains, original certificates and cone pins."""
import copy,gzip,hashlib,json,statistics,time
from pathlib import Path
from check_native_wang import Reference,normalize,need
from check_native_rectangle import Primitive
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(ref):
    p=DOC/ref['file'];need(sha(p)==ref['sha256'],'whole raw trace digest');return json.loads(gzip.decompress(p.read_bytes()))

def cone(spec,A):
    head=[];ordinary={}
    for x,value in enumerate(spec['pattern']):
        s=normalize(value);need(s is not None and len(s)>0,'nonempty cone input')
        has_plain=any(v in s for v in range(A));has_head=(s.stop>A if isinstance(s,range) else any(v>=A for v in s))
        if has_head:need(not has_plain,'known head presence');head.append(x)
        elif len(s)==1:ordinary[x]=s[0]
    need(len(head)==1,'single input head')
    return head[0],[[[2*x,2*k-1,1],v] for k in range(1,spec['height']+1) for x,v in ordinary.items() if abs(x-head[0])>=k]

class Replay:
    def __init__(self,reference,row):
        self.ref=reference;self.row=row;self.spec=row['spec'];self.r=row['result'];self.width=len(self.spec['pattern']);self.height=self.spec['height'];self.values={};self.order=[];self.states=0
        self.boundary={tuple(p):tuple(v) if isinstance(v,list) else v for p,v in self.r['boundary']}
        self.required={(x,y) for y in range(self.height) for x in range(self.width)}
    def markings(self):
        result=self.boundary.copy();A=self.ref.A
        for (x,y),(a,b,c) in self.values.items():
            n=self.ref.successor((a,b,c));values={(2*x,2*y-1):b,(2*x,2*y+1):n,(2*x-1,2*y):(a,b),(2*x+1,2*y):(b,c)}
            if self.r['extended']:values.update({(2*x-2,2*y-1):a,(2*x+2,2*y-1):c})
            if self.r['projected']:
                for px,py,v in ((2*x-2,2*y-1,a),(2*x,2*y-1,b),(2*x+2,2*y-1,c),(2*x,2*y+1,n)):values[px,py,1]=v if v<A else (v-A)%A
            for p,v in values.items():need(p not in result or result[p]==v,'actual global point agreement');result[p]=v
        return result
    def domain(self,p,marks):
        x,y=p;allowed=[None,None,None]
        if y==0:
            for j,slot in enumerate((x-1,x,x+1)):
                if 0<=slot<self.width:allowed[j]=normalize(self.spec['pattern'][slot])
        def pin(j,v):allowed[j]=(v,) if allowed[j] is None or v in allowed[j] else ()
        if self.r['extended']:
            for j,q in ((0,(2*x-2,2*y-1)),(2,(2*x+2,2*y-1))):
                if q in marks:pin(j,marks[q])
        for q,indices in (((2*x,2*y-1),(1,)),((2*x-1,2*y),(0,1)),((2*x+1,2*y),(1,2))):
            if q in marks:
                v=marks[q];vs=(v,) if len(indices)==1 else v
                for j,a in zip(indices,vs):pin(j,a)
        projections=tuple(marks.get(q) for q in ((2*x-2,2*y-1,1),(2*x,2*y-1,1),(2*x+2,2*y-1,1),(2*x,2*y+1,1))) if self.r['projected'] else (None,)*4
        return self.ref.domain(allowed,marks.get((2*x,2*y+1)),projections)
    def census(self):
        marks=self.markings();domains={p:self.domain(p,marks) for p in self.required-self.values.keys()};self.states+=1
        return [[list(p),v[1]] for p,v in sorted(domains.items(),key=lambda v:(v[0][1],v[0][0]))],domains
    def check(self):
        r=self.r;census,_=self.census();need(census==r['initial_census'] and sum(v for _,v in census)==r['initial_candidate_nodes'],'complete initial graph')
        frames=[];attempts=forced=branches=backtracks=0;pending=None;terminal=None
        for e in r['events']:
            if e['kind']=='alternative':
                need(pending is not None,'original fallback expected');p,key=pending;need(e['point']==list(p) and e['key']==list(key) and e['depth']==len(self.order),'whole fallback order and rollback');pending=None;self.values[p]=key;self.order.append(p);attempts+=1;continue
            need(pending is None and terminal is None,'no skipped fallback or terminal')
            census,domains=self.census();need(census==e['census'] and e['depth']==len(self.order),'complete global frontier census')
            dead=[p for p,(_,n) in domains.items() if n==0];single=[p for p,(_,n) in domains.items() if n==1]
            if dead:kind='dead';p=min(dead,key=lambda p:(p[1],p[0]))
            elif single:kind='forced';p=min(single,key=lambda p:(p[1],p[0]))
            elif domains:kind='branch';p=min(domains,key=lambda p:(domains[p][1],p[1],p[0]))
            else:kind='empty';p=None
            need(e['kind']==kind and e['point']==(None if p is None else list(p)) and e['count']==(None if p is None else domains[p][1]),'global dead/forced and generation-zero branch tie')
            if kind=='empty':terminal='finite_exact_native_rectangle';continue
            if kind=='dead':
                while frames:
                    prior,p0,options=frames[-1];self.values=dict(prior);self.order=list(prior)
                    try:key=next(options)
                    except StopIteration:frames.pop();backtracks+=1;continue
                    pending=p0,key;backtracks+=1;break
                if pending is None:terminal='exhausted_finite_native_rectangle'
                continue
            options=self.ref.options(domains[p][0]);key=next(options);need(e['key']==list(key),'actual first original candidate')
            if kind=='branch':frames.append((self.values.copy(),p,options));branches+=1
            else:forced+=1
            self.values[p]=key;self.order.append(p);attempts+=1
        need(pending is None and (attempts,forced,branches,backtracks)==(r['attempts'],r['forced'],r['branches'],r['backtracks']),'all actual placements and fallback counts')
        need(r['status']==(terminal or 'unknown_search_budget'),'tri-state result')
        if terminal is None:need(attempts>=r['limits']['attempts'] or r['seconds']>=r['limits']['seconds'],'actual declared cutoff')
        need([(t['x'],t['y']) for t in r['tiles']]==self.order and all(list(self.values[t['x'],t['y']])==t['triple'] for t in r['tiles']),'exact selected partial or complete placements')
        return self.states

def check_row(reference,primitive,row):
    r=row['result'];lane=row['lane'];need(r['extended']==(lane=='neighbors') and r['projected']==(lane=='projected'),'declared actual marking layer')
    cert=row['certificate'];expected=row['spec']['boundary'][:]
    if lane=='projected':
        head,pins=cone(row['spec'],reference.A);need(cert['head_position']==head and cert['pins']==pins and cert['pattern']==row['spec']['pattern'] and cert['height']==row['spec']['height'],'independently synthesized cone pins');expected+=pins
    else:need(cert is None,'no undeclared redundant root layer')
    need(r['boundary']==expected,'all original and derived root assignments')
    for name,decorated in (('original',False),('decorated',True)):need(r['point_checks'][name]==primitive.check(row['spec'],r,decorated),'independent original/decorated certificate')
    for query in row['domain_queries']:need(reference.count(query['role'],query['north'],query['allowed'])==query['count'],'complete native selector cardinality')
    states=Replay(reference,row).check();need(r['root_rollback_verified'] is True,'producer root rollback witness')
    return states

def main():
    began=time.perf_counter();path=DOC/'native-wang-search-001.json';data=json.loads(path.read_text())
    for n,pin in data['sources'].items():need(sha(HERE/n)==pin,'measured source '+n)
    for n,pin in data['reused_inputs'].items():need(sha(DOC/n)==pin,'fixed input '+n)
    rows=[record(ref) for c in data['cases'] for ref in c['runs']];raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());need(hashlib.sha256(raw).hexdigest()==data['literal_table_sha256'],'fixed palette bytes')
    reference=Reference(raw,[q for row in rows for q in row['domain_queries']]);primitive=Primitive(raw);states=queries=positive=0;mutations=[]
    for index,c in enumerate(data['cases']):
        for ref in c['runs']:
            row=record(ref);need(row['spec']==c['spec'] and row['lane']==ref['lane'],'whole statement-only fixture input');r=row['result'];states+=check_row(reference,primitive,row);queries+=len(row['domain_queries']);positive+=int(r['status']=='finite_exact_native_rectangle')
            semantic={k:v for k,v in r.items() if k not in ('seconds','total_seconds','preparation_seconds','verification_seconds','peak_process_rss_bytes')};need(hashlib.sha256(canonical(semantic)).hexdigest()==row['semantic_sha256']==ref['semantic_sha256'],'whole raw semantic binding')
            off=(index+ref['repetition'])%3;lanes=data['lanes'];need(ref['order']==lanes[off:]+lanes[:off] and r['status']==ref['status'] and r['attempts']==ref['attempts'] and r['total_seconds']==ref['total_seconds'],'balanced observations')
            need(r['total_seconds']>=r['preparation_seconds']+r['seconds']+r['verification_seconds']>=0 and ref['stage_seconds']>=r['total_seconds'] and r['peak_process_rss_bytes']>0,'literal observed clock algebra')
        for lane in data['lanes']:
            samples=[r for r in c['runs'] if r['lane']==lane];need(c['timings'][lane]['samples']==samples and len(samples)==3 and c['timings'][lane]['median_seconds']==statistics.median(s['total_seconds'] for s in samples),'all actual timing summaries')
        print(c['spec']['id'],'all nine complete native trees passed',flush=True)
    first=next(row for row in rows if row['lane']=='projected' and row['result']['status']=='finite_exact_native_rectangle')
    for kind in ('domain-count','census','tile-color','tile-head','cone-pin','root-zero','fallback','generation'):
        bad=copy.deepcopy(first)
        if kind=='domain-count':bad['domain_queries'][0]['count']+=1
        elif kind=='census':bad['result']['events'][0]['census'][0][1]+=1
        elif kind=='tile-color':bad['result']['tiles'][0]['N']+=1
        elif kind=='tile-head':bad['result']['tiles'][0]['triple'][0]=reference.A+1
        elif kind=='cone-pin':bad['certificate']['pins'][0][1]=0
        elif kind=='root-zero':bad['result']['boundary'][0][1]=[0,0]
        elif kind=='fallback':next(e for e in bad['result']['events'] if e['kind']=='branch')['key'][0]=0
        else:bad['result']['tile_generations'][0]=2
        try:check_row(reference,primitive,bad)
        except (ValueError,KeyError,IndexError,StopIteration):mutations.append(kind)
        else:raise ValueError('accepted corrupted '+kind)
    out=dict(version='native-wang-search-audit-001',status='passed',input_sha256=sha(path),source_sha256=sha(__file__),helpers={n:sha(HERE/n) for n in ('check_native_wang.py','check_native_rectangle.py')},searches=len(rows),states=states,selector_queries=queries,positive_rectangles=positive,mutations_rejected=mutations,seconds=time.perf_counter()-began,
        scope='Every cold observation: complete raw-table head counts, every frontier census, literal point assignments, original candidate order/fallback, global dead/forced/generation scheduling, partial/complete state, cone pins, original and decorated certificates, semantic hashes and timing algebra. Physical clock authenticity, summed native-plus-Python RSS, universal compiler correctness and full mathematical proof discovery are outside this audit.')
    (DOC/'native-wang-search-audit-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
