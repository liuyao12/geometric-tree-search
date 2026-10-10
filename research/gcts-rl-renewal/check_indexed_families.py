"""Separate full enumeration reconstructs every lazy index and cache query."""
import collections,itertools
import check_resumable_clusters as W
V=W.V;A=W.A;F,N=W.F,W.N
unify=W.unify

def index_pool(rules,spec,templates,chosen,point,limit,recorder):
    filled,ports,marks=A.state(rules,spec,chosen);ds=A.domains(rules,spec,chosen)
    available={j:a for j,a in ports.items() if j<0 or j in filled};slots=sorted(p[0]//2 for p in ds if p[0]//2<spec['bound'])
    pool={};scanned=0
    for t in sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name'])):
        pattern=F(t['pattern'])
        for embedding in itertools.combinations(slots,len(pattern)):
            if point[0]//2 not in embedding:continue
            states=[((),{},{})]
            for i,node in enumerate(pattern):
                following=[];j=embedding[i]
                for members,binding,outside in states:
                    recorder.query(node,binding)
                    for rid,r in enumerate(rules):
                        if r['kind']!=node['kind']:continue
                        env=dict(binding)
                        for p,a in zip(node['inputs']+(node['output'],),r['inputs']+(r['output'],)):
                            env=unify(p,a,env)
                            if env is None:break
                        if env is None:continue
                        scanned+=1;choices=[]
                        for (kind,k),a in zip(node['refs'],r['inputs']):
                            if kind=='inside':N(k<i,'acyclic learned pattern');vs=(embedding[k],)
                            elif str(k) in outside:
                                v=outside[str(k)];vs=(v,) if v<j and available.get(v)==a else ()
                            else:vs=tuple(v for v,b in sorted(available.items()) if v<j and b==a)
                            choices.append(vs)
                        for refs in itertools.product(*choices):
                            key=(j,rid,refs)
                            if key not in ds[A.cell(j)]:continue
                            ext=dict(outside);okay=True
                            for (kind,k),ref in zip(node['refs'],refs):
                                if kind=='outside':
                                    if str(k) in ext and ext[str(k)]!=ref:okay=False;break
                                    ext[str(k)]=ref
                            if okay:following.append((members+(key,),env,ext))
                states=following
                if not states:break
            for members,binding,outside in states:
                if members in pool:recorder.counts['duplicate_expansions']+=1;continue
                recorder.aggregate(members)
                totals=collections.Counter();union={};okay=True
                for key in members:
                    tile=A.tile(rules,spec,key)
                    for p,v in tile['occupancy']:totals[p]+=v
                    for p,v in tile['marks']:
                        if p in union and union[p]!=v:okay=False
                        union[p]=v
                if not okay or any(v>12 for v in totals.values()) or any(p in marks and marks[p]!=v for p,v in union.items()):continue
                item=dict(template=t['name'],members=members,bindings=binding,outside=outside,level=t['level'],
                    occupancy=tuple(sorted(totals.items())),marks=tuple(sorted(union.items())))
                pool.setdefault(members,item)
    for item in pool.values():recorder.item(item)
    items=sorted(pool.values(),key=lambda t:(-int(rules[t['members'][-1][1]]['output']==F(spec['target'])),-len(t['members']),V.digest(t)))
    return items[:limit],dict(compatible=len(items),scanned=scanned,truncated=max(0,len(items)-limit))

def names(a):
    if a[0]=='meta':yield str(a[1])
    else:
        for v in a[1:]:yield from names(v)

class Replay:
    def __init__(self,rules,templates):
        self.rules=rules;self.declared={};self.nodes={};self.queries=[];self.q=set();self.a=set();self.d=set();self.counts=collections.Counter()
        for t in sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name'])):
            for node in F(t['pattern']):
                pin=V.digest({k:node[k] for k in ('kind','inputs','output')});self.declared.setdefault(pin,node)
    def query(self,p,binding):
        identity=V.digest({k:p[k] for k in ('kind','inputs','output')});node=self.declared[identity]
        variables=tuple(sorted(set(v for a in node['inputs']+(node['output'],) for v in names(a))))
        if identity not in self.nodes:
            rows=[]
            for rid,r in enumerate(self.rules):
                if r['kind']!=node['kind']:continue
                self.counts['syntax_rule_tests']+=1;env={}
                for pat,formula in zip(node['inputs']+(node['output'],),r['inputs']+(r['output'],)):
                    env=unify(pat,formula,env)
                    if env is None:break
                if env is not None:rows.append((rid,env))
            self.nodes[identity]=dict(node=node,variables=variables,rows=tuple(rows));self.counts['ground_matches']+=len(rows)
        bound=tuple((k,binding[k]) for k in variables if k in binding);key=(identity,bound)
        self.queries.append(dict(node=identity,bound=bound));self.counts['queries']+=1
        self.counts['query_cache_hits' if key in self.q else 'query_cache_misses']+=1;self.q.add(key)
    def aggregate(self,members):
        self.counts['aggregate_cache_hits' if members in self.a else 'aggregate_cache_misses']+=1;self.a.add(members)
    def item(self,item):
        key=(item['template'],item['members']);self.counts['item_digest_hits' if key in self.d else 'item_digest_misses']+=1;self.d.add(key)

def index(c,r,templates,enabled):
    rules,spec=F(c['catalog']['rules']),F(c['spec']);rec=Replay(rules,templates);joins=0
    def walk(t,chosen):
        nonlocal joins
        if 'proposal_pool' in t:
            joins+=1
            if enabled:
                items,work=index_pool(rules,spec,templates,chosen,F(t['point']),r['limits']['proposal_limit'],rec)
                N(F(items)==F(t['proposal_pool']),'same complete indexed pool through separate enumeration')
        for child in t['children']:walk(child['tree'],chosen+(F(child['key']),))
    walk(r['search_tree'],())
    if not enabled or not joins:N(r['index'] is None,'no uncharged unused index');return dict(joins=joins,indexed=False)
    out=F(r['index']);N(out is not None,'all actual indexed joins recorded')
    N(out['nodes']==rec.nodes,'every and only demanded static syntax match')
    N(out['queries']==F(rec.queries),'every actual query in complete tree order')
    N(all(out['metrics'].get(k,0)==v for k,v in rec.counts.items()),'all index/cache work counters')
    N(set(out['metrics'])<=set(rec.counts)|{'ground_matches'},'no unexplained work counters')
    N(out['context']==A.context_hash(c['catalog'],spec),'exact immutable model snapshot')
    ordered=sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name']))
    N(out['library_pin']==V.digest([(t['name'],t['pattern'],t['level']) for t in ordered]),'same immutable family inventory')
    N(0<=out['build_seconds']<=r['seconds'],'cold build charged within search')
    return dict(joins=joins,indexed=True,nodes=len(rec.nodes),**dict(rec.counts))
