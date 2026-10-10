"""Complete counted native tile domains and the reference point scheduler.

The unchanged finite palette is not specialized by formula, theory or trace.
Head components are exact counted selectors with lazy complete pagination.
Each candidate occupies one center, so reverse incidence is exactly a singleton.
The optional neighbor-value layer is redundant on complete Wang rectangles.
"""
import hashlib,heapq,subprocess,time
from collections import Counter
from pathlib import Path
from shared_wang_inventory import Inventory,points,TABLE_PIN

def pool(s):
    if s is None:return None
    if isinstance(s,dict) and set(s)=={'range'}:return range(*s['range'])
    if isinstance(s,range):return s
    return tuple(sorted(set(s)))

def encoded(s):return {'range':[s.start,s.stop,s.step]} if isinstance(s,range) else s

class HeadSet:
    def __init__(self,oracle,role,north,allowed):
        self.oracle,self.role,self.north,self.allowed=oracle,role,north,allowed
        self.count=oracle.count(role,north,allowed)
    def __len__(self):return self.count
    def __iter__(self):
        cursor=self.oracle.inventory.A;seen=0
        while seen<self.count:
            values=self.oracle.page(self.role,self.north,self.allowed,cursor,512)
            if not values:raise ValueError('incomplete head page')
            yield from values;seen+=len(values);cursor=values[-1]+1
        if seen!=self.count:raise ValueError('head count/page mismatch')
    def declaration(self):return dict(role=self.role,north=self.north,allowed=encoded(self.allowed),count=self.count)

class Oracle:
    def __init__(self,raw,executable,table_path):
        if hashlib.sha256(Path(table_path).read_bytes()).hexdigest()!=TABLE_PIN:raise ValueError('native file differs from fixed palette')
        self.inventory=Inventory(raw);self.process=subprocess.Popen([str(executable),str(table_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        i=self.inventory;expected=['READY',str(i.A),str(i.Q),str(i.start),str(i.accept),str(i.defined)]
        if self.process.stdout.readline().split()!=expected:raise ValueError('native table binding')
        self.cache={};self.queries=[];self.metrics=Counter()
    def close(self):
        if self.process.poll() is None:self.process.stdin.write('quit\n');self.process.stdin.flush();self.process.wait(timeout=10)
        if self.process.returncode!=0:raise ValueError(self.process.stderr.read())
    def query(self,command,role,north,allowed,cursor=0,limit=0):
        self.metrics[command+'_calls']+=1
        values=[] if allowed is None else [allowed.start,allowed.stop,allowed.step] if isinstance(allowed,range) else list(allowed)
        n=-1 if allowed is None else -3 if isinstance(allowed,range) else len(values)
        text=' '.join(map(str,[command,role,-1 if north is None else north,n,cursor,limit,*values]))+'\n'
        self.process.stdin.write(text);self.process.stdin.flush();reply=self.process.stdout.readline().split()
        if not reply:raise ValueError('native domain process stopped: '+self.process.stderr.read())
        if command=='count':
            if len(reply)!=2 or reply[0]!='COUNT':raise ValueError('count protocol')
            result=int(reply[1]);self.queries.append(dict(role=role,north=north,allowed=encoded(allowed),count=result));return result
        if reply[0]!='PAGE' or int(reply[1])!=len(reply)-2:raise ValueError('page protocol')
        result=tuple(map(int,reply[2:]));self.metrics['paged_heads']+=len(result);return result
    def count(self,role,north,allowed):
        key=role,north,allowed
        if key not in self.cache:self.cache[key]=self.query('count',*key)
        else:self.metrics['count_cache_hits']+=1
        return self.cache[key]
    def page(self,*args):return self.query('page',*args)

class Domain:
    def __init__(self,universe,a,b,c,north,blocks):
        self.universe=universe;self.allowed=a,b,c;self.north=north
        self.projections=(None,)*4
        self.blocks=tuple(block for block in blocks if all(len(v) for v in block))
        self.count=sum(len(a)*len(b)*len(c) for a,b,c in self.blocks)
    def options(self):
        # itertools.product would materialize millions of heads. Nested lazy
        # loops preserve the complete Cartesian product without that allocation.
        for aa,bb,cc in self.blocks:
            for a in aa:
                for b in bb:
                    for c in cc:yield a,b,c
    def contains(self,triple):
        if not isinstance(triple,tuple) or len(triple)!=3:return False
        if any(allowed is not None and v not in allowed for v,allowed in zip(triple,self.allowed)):return False
        try:n=self.universe.inventory.successor(*triple)
        except (ValueError,TypeError):return False
        if n is None or (self.north is not None and n!=self.north):return False
        A=self.universe.inventory.A
        return all(tau is None or (v if v<A else (v-A)%A)==tau for v,tau in zip((*triple,n),self.projections))
    def declaration(self):
        return dict(allowed=[encoded(v) for v in self.allowed],north=self.north,projections=self.projections,count=self.count,
            blocks=[[v.declaration() if isinstance(v,HeadSet) else list(v) for v in block] for block in self.blocks])

class Universe:
    def __init__(self,oracle):
        self.oracle=oracle;self.inventory=oracle.inventory;self.cache={};self.metrics=Counter()
        self.full=self.domain();self.inventory_count=self.full.count
        if self.inventory_count!=sum(self.inventory.counts.values()):raise ValueError('entire fixed palette count')
    def domain(self,a=None,b=None,c=None,north=None,south=None,west=None,east=None,ta=None,tb=None,tc=None,tn=None):
        i=self.inventory;allowed=[pool(s) for s in (a,b,c)]
        def narrow(j,value):allowed[j]=(value,) if (allowed[j] is None or value in allowed[j]) else ()
        if south is not None:narrow(1,south)
        if west is not None:narrow(0,west[0]);narrow(1,west[1])
        if east is not None:narrow(1,east[0]);narrow(2,east[1])
        def valid(s):
            if s is None:return True
            if isinstance(s,range):return s.step in (1,i.A) and 0<=s.start<=s.stop<=i.D
            return all(type(v) is int and 0<=v<i.D for v in s)
        if not all(map(valid,allowed)) or (north is not None and (type(north) is not int or not 0<=north<i.D)):
            result=Domain(self,(),(),(),north,());return result
        key=(*allowed,north,ta,tb,tc,tn)
        if key in self.cache:self.metrics['domain_cache_hits']+=1;return self.cache[key]
        self.metrics['domain_constructions']+=1
        ordinary=[tuple(range(i.A)) if s is None else tuple(v for v in range(i.A) if v in s) for s in allowed]
        heads=[]
        for s in allowed:
            if s is None:heads.append(None)
            elif isinstance(s,range):
                first=s.start+max(0,(i.A-s.start+s.step-1)//s.step)*s.step;heads.append(range(first,s.stop,s.step) if first<s.stop else ())
            else:heads.append(tuple(v for v in s if v>=i.A))
        for j,tau in enumerate((ta,tb,tc)):
            if tau is None:continue
            if type(tau) is not int or not 0<=tau<i.A:return Domain(self,(),(),(),north,())
            ordinary[j]=tuple(v for v in ordinary[j] if v==tau);h=heads[j]
            if h is None:heads[j]=range(i.A+tau,i.D,i.A)
            elif isinstance(h,range):
                first=h.start+(tau-(h.start-i.A)%i.A)%i.A
                heads[j]=range(first,h.stop,i.A) if first<h.stop and (h.step==1 or first==h.start) else ()
            else:heads[j]=tuple(v for v in h if (v-i.A)%i.A==tau)
        ab,bb,cb=ordinary
        if tn is not None and (type(tn) is not int or not 0<=tn<i.A or (north is not None and (north if north<i.A else (north-i.A)%i.A)!=tn)):return Domain(self,(),(),(),north,())
        normal=bb if north is None else tuple(s for s in bb if s==north)
        side=normal if north is None or north<i.A else tuple(s for s in bb if s==(north-i.A)%i.A)
        if tn is not None:normal=tuple(s for s in normal if s==tn);side=tuple(s for s in side if s==tn)
        selector=north if north is not None or tn is None else -2-tn
        center=HeadSet(self.oracle,0,selector,heads[1]);left=HeadSet(self.oracle,1,selector,heads[0]);right=HeadSet(self.oracle,2,selector,heads[2])
        result=Domain(self,*allowed,north,((ab,normal,cb),(ab,center,cb),(left,side,cb),(ab,side,right)));result.projections=ta,tb,tc,tn
        self.cache[key]=result;return result
    def tile(self,key):return self.inventory.tile(*key)

def assignments(tile,x,y,extended=False,projected=False,A=60):
    value=points(tile,x,y);occ={tuple(p):v for p,v in value['t']};marks={tuple(p):tuple(v) if isinstance(v,list) else v for p,v in value['m']}
    if extended:
        a,b,c=tile['triple'];marks[2*x-2,2*y-1]=a;marks[2*x+2,2*y-1]=c
    if projected:
        for (px,py),v in list(marks.items()):
            if px%2==0:marks[px,py,1]=v if v<A else (v-A)%A
        a,b,c=tile['triple']
        for px,v in ((2*x-2,a),(2*x+2,c)):marks[px,2*y-1,1]=v if v<A else (v-A)%A
    return occ,marks

class Graph:
    def __init__(self,universe,pattern,height,boundary,extended=False,projected=False):
        if type(height) is not int or height<1 or not pattern:raise ValueError('finite rectangle')
        self.universe=universe;self.pattern=tuple(pool(s) for s in pattern);self.width=len(pattern);self.height=height;self.extended=extended
        self.projected=projected
        self.required=frozenset((x,y) for y in range(height) for x in range(self.width))
        self.boundary={}
        for p,v in boundary:
            p=tuple(p);v=tuple(v) if isinstance(v,list) else v
            if p in self.boundary and self.boundary[p]!=v:raise ValueError('inconsistent root markings')
            self.boundary[p]=v
        self.marks=self.boundary.copy()
        self.selected={};self.order=[];self.tile_generations=[];self.domains={};self.trail=[];self.versions=Counter();self.dead=[];self.forced=[];self.branches=[];self.metrics=Counter()
        self.initial=[]
        for p in sorted(self.required,key=lambda p:(p[1],p[0])):
            self.replace(p,self.calculate(p));self.initial.append([list(p),self.domains[p].count])
        self.initial_candidate_count=sum(d.count for d in self.domains.values())
    def calculate(self,p):
        x,y=p;kw={}
        if y==0:
            if x>0:kw['a']=self.pattern[x-1]
            kw['b']=self.pattern[x]
            if x+1<self.width:kw['c']=self.pattern[x+1]
        if self.extended:
            for name,q in (('a',(2*x-2,2*y-1)),('c',(2*x+2,2*y-1))):
                if q in self.marks:
                    old=kw.get(name);v=self.marks[q];kw[name]=(v,) if old is None or v in old else ()
        if self.projected:
            for name,q in (('ta',(2*x-2,2*y-1,1)),('tb',(2*x,2*y-1,1)),('tc',(2*x+2,2*y-1,1)),('tn',(2*x,2*y+1,1))):
                if q in self.marks:kw[name]=self.marks[q]
        return self.universe.domain(**kw,north=self.marks.get((2*x,2*y+1)),south=self.marks.get((2*x,2*y-1)),west=self.marks.get((2*x-1,2*y)),east=self.marks.get((2*x+1,2*y)))
    def replace(self,p,domain):
        self.versions[p]+=1
        if domain is None:self.domains.pop(p,None);return
        self.domains[p]=domain;x,y=p;entry=y,x,self.versions[p]
        heapq.heappush(self.dead if domain.count==0 else self.forced if domain.count==1 else self.branches,entry if domain.count<2 else (domain.count,*entry))
    def decision(self):
        for kind,heap in (('dead',self.dead),('forced',self.forced),('branch',self.branches)):
            while heap:
                e=heap[0];y,x,version=e[-3:];p=x,y
                if p in self.domains and self.versions[p]==version:return kind,p,self.domains[p]
                heapq.heappop(heap)
        if self.domains:raise ValueError('missing complete frontier')
        return 'empty',None,None
    def census(self):return [[list(p),d.count] for p,d in sorted(self.domains.items(),key=lambda v:(v[0][1],v[0][0]))]
    def place(self,p,key):
        if p not in self.domains or not self.domains[p].contains(key):raise ValueError('illegal native tile')
        x,y=p;tile=self.universe.tile(key);_,marks=assignments(tile,x,y,self.extended,self.projected,self.universe.inventory.A)
        if any(q in self.marks and self.marks[q]!=v for q,v in marks.items()):raise ValueError('literal marking conflict')
        affected={p}
        for point in marks:
            mx,my=point[:2]
            if mx%2==0:
                j=mx//2;row=(my+1)//2;affected.update(((j,row-1),(j,row)))
                if self.extended or self.projected:affected.update(((j-1,row),(j+1,row)))
            else:
                j=(mx+1)//2;row=my//2;affected.update(((j-1,row),(j,row)))
        affected=sorted(affected&self.required);prior={q:self.domains.get(q) for q in affected};added=[q for q in marks if q not in self.marks]
        self.trail.append((p,added,prior));self.selected[p]=key;self.order.append(p);self.tile_generations.append(1);self.marks.update(marks);self.replace(p,None)
        for q in affected:
            if q not in self.selected:self.replace(q,self.calculate(q))
        self.metrics['placements']+=1;self.metrics['domain_updates']+=len(affected)
    def rollback(self,token):
        if type(token) is not int or not 0<=token<=len(self.trail):raise ValueError('rollback token')
        while len(self.trail)>token:
            p,added,prior=self.trail.pop();del self.selected[p];self.order.pop();self.tile_generations.pop()
            for q in added:del self.marks[q]
            for q,d in prior.items():self.replace(q,d)
            self.metrics['rollback_placements']+=1
    def fingerprint(self):
        return self.selected.copy(),self.marks.copy(),self.order.copy(),self.tile_generations.copy(),{p:d.declaration() for p,d in self.domains.items()}

def search(universe,pattern,height,boundary,extended=False,projected=False,attempts=10000,seconds=30,trace_limit=30000):
    start=time.perf_counter();g=Graph(universe,pattern,height,boundary,extended,projected);frames=[];events=[];steps=forced=branches=backtracks=0;status='unknown_search_budget'
    def event(kind,p,d):
        if len(events)>=trace_limit:raise ValueError('trace budget exhausted')
        e=dict(kind=kind,point=p,count=None if d is None else d.count,census=g.census(),depth=len(g.order));events.append(e);return e
    def alternative():
        nonlocal steps,backtracks
        while frames:
            token,p,options=frames[-1];g.rollback(token)
            try:key=next(options)
            except StopIteration:frames.pop();backtracks+=1;continue
            events.append(dict(kind='alternative',point=p,key=key,depth=len(g.order)));g.place(p,key);steps+=1;backtracks+=1;return True
        return False
    while steps<attempts and time.perf_counter()-start<seconds:
        kind,p,d=g.decision();e=event(kind,p,d)
        if kind=='empty':status='finite_exact_native_rectangle';break
        if kind=='dead':
            if not alternative():status='exhausted_finite_native_rectangle';break
        elif kind=='forced':
            key=next(d.options());e['key']=key;g.place(p,key);steps+=1;forced+=1
        else:
            options=iter(d.options());key=next(options);e['key']=key;frames.append((len(g.trail),p,options));g.place(p,key);steps+=1;branches+=1
    tiles=[dict(x=x,y=y,**universe.tile(g.selected[x,y])) for x,y in g.order]
    result=dict(status=status,attempts=steps,forced=forced,branches=branches,backtracks=backtracks,seconds=time.perf_counter()-start,
        width=g.width,height=height,extended=extended,projected=projected,pattern=pattern,boundary=boundary,events=events,tiles=tiles,tile_generations=g.tile_generations.copy(),
        initial_census=g.initial,initial_candidate_nodes=g.initial_candidate_count,metrics=dict(g.metrics),limits=dict(attempts=attempts,seconds=seconds))
    g.rollback(0)
    if g.selected or g.order or g.tile_generations or g.marks!=g.boundary or g.census()!=g.initial:raise ValueError('whole root rollback')
    result['root_rollback_verified']=True
    return result
