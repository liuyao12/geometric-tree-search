"""Complete symbolic Wang domains for finite deterministic TM rectangles.

The compiler's allowed triples have zero heads or one head at one of three
positions. Four disjoint Cartesian-product blocks count/enumerate ALL types
without materializing their inventory. Fixed bottom pattern restrictions,
blank side pairs and a fixed accepting top are declared boundary conditions.
All centers are generation-zero roots; placed tile generations are one.

Each placement touches one required center, so reverse incidence is implicit
and exact: (center, triple) -> {center}. All four marking dependencies update
adjacent domains. Trail rollback restores selections, marks and domains.
"""
import heapq,time
from collections import Counter
from itertools import product
import wang

class Domain:
    __slots__=("blocks","count","a","b","c","north","universe")
    def __init__(self,universe,a,b,c,north,blocks):
        self.universe=universe
        self.a=universe.symbol_set if a is universe.symbols else frozenset(a)
        self.b=universe.symbol_set if b is universe.symbols else frozenset(b)
        self.c=universe.symbol_set if c is universe.symbols else frozenset(c);self.north=north
        self.blocks=tuple(block for block in blocks if all(block));self.count=sum(len(a)*len(b)*len(c) for a,b,c in self.blocks)
    def options(self):
        for block in self.blocks:yield from product(*block)
    def contains(self,triple):
        if not isinstance(triple,tuple) or len(triple)!=3:return False
        a,b,c=triple
        if a not in self.a or b not in self.b or c not in self.c:return False
        n=self.universe.compiler.rule(a,b,c)
        return n is not None and (self.north is None or n==self.north)

class Universe:
    def __init__(self,compiler):
        self.compiler=compiler;self.base=tuple(compiler.alphabet);self.heads=tuple(wang.head(q,s) for q in compiler.states for s in self.base)
        if len(set(self.base))!=len(self.base) or any(isinstance(s,tuple) for s in self.base):raise ValueError("distinct non-head tape symbols required")
        if len(set(compiler.states))!=len(compiler.states) or compiler.halt not in compiler.states:raise ValueError("invalid states")
        self.symbols=self.base+self.heads;self.symbol_set=frozenset(self.symbols);self.base_set=frozenset(self.base)
        for (q,s),(next_q,w,d) in compiler.transitions.items():
            if q not in compiler.states or s not in self.base_set or next_q not in compiler.states or w not in self.base_set or d not in (-1,0,1):raise ValueError("invalid transition")
        self.center={};self.left={};self.right={};self.cache={};self.metrics=Counter()
        for h in self.heads:
            _,q,s=h;tr=compiler.transitions.get((q,s))
            self.center[h]=h if q==compiler.halt else None if tr is None else wang.head(tr[0],tr[1]) if tr[2]==0 else tr[1]
            self.left[h]=tr[0] if q!=compiler.halt and tr and tr[2]==1 else None
            self.right[h]=tr[0] if q!=compiler.halt and tr and tr[2]==-1 else None
        self.valid_centers=tuple(h for h in self.heads if self.center[h] is not None)
        self.left_stays=tuple(h for h in self.heads if self.left[h] is None)
        self.right_stays=tuple(h for h in self.heads if self.right[h] is None)
        self.full=self.domain();self.inventory_count=self.full.count
    def domain(self,allowed_a=None,allowed_b=None,allowed_c=None,north=None,south=None,west=None,east=None):
        key=allowed_a,allowed_b,allowed_c,north,south,west,east
        if key in self.cache:self.metrics["domain_cache_hits"]+=1;return self.cache[key]
        self.metrics["domain_constructions"]+=1
        a=self.symbols if allowed_a is None else tuple(dict.fromkeys(allowed_a))
        b=self.symbols if allowed_b is None else tuple(dict.fromkeys(allowed_b))
        c=self.symbols if allowed_c is None else tuple(dict.fromkeys(allowed_c))
        if any(s not in self.symbol_set for seq in (a,b,c) if seq is not self.symbols for s in seq) or (north is not None and north not in self.symbol_set):
            a=b=c=()
        if south is not None:b=tuple(s for s in b if s==south)
        if west is not None:
            if not isinstance(west,tuple) or len(west)!=2:a=b=()
            else:a=tuple(s for s in a if s==west[0]);b=tuple(s for s in b if s==west[1])
        if east is not None:
            if not isinstance(east,tuple) or len(east)!=2:b=c=()
            else:b=tuple(s for s in b if s==east[0]);c=tuple(s for s in c if s==east[1])
        ab=self.base if a is self.symbols else tuple(s for s in a if s in self.base_set)
        ah=self.heads if a is self.symbols else tuple(s for s in a if s not in self.base_set)
        bb=self.base if b is self.symbols else tuple(s for s in b if s in self.base_set)
        bh=self.heads if b is self.symbols else tuple(s for s in b if s not in self.base_set)
        cb=self.base if c is self.symbols else tuple(s for s in c if s in self.base_set)
        ch=self.heads if c is self.symbols else tuple(s for s in c if s not in self.base_set)
        normal=bb if north is None else tuple(s for s in bb if s==north)
        center=self.valid_centers if bh is self.heads and north is None else tuple(h for h in bh if self.center[h] is not None and (north is None or self.center[h]==north))
        if north is None:left,right=ah,ch;side_b=bb
        elif north in self.base_set:
            left=self.left_stays if ah is self.heads else tuple(h for h in ah if self.left[h] is None)
            right=self.right_stays if ch is self.heads else tuple(h for h in ch if self.right[h] is None);side_b=normal
        else:
            left=tuple(h for h in ah if self.left[h]==north[1]);right=tuple(h for h in ch if self.right[h]==north[1])
            side_b=tuple(s for s in bb if s==north[2])
        result=Domain(self,a,b,c,north,((ab,normal,cb),(ab,center,cb),(left,side_b,cb),(ab,side_b,right)))
        self.cache[key]=result;return result
    def tile(self,triple):
        a,b,c=triple;n=self.compiler.rule(a,b,c)
        if n is None:raise ValueError("not a compiled tile")
        return {"S":b,"N":n,"W":(a,b),"E":(b,c),"triple":triple}

def point_tile(tile,x,y,extended=False):
    occupancy,marks=wang.point_tile(tile,x,y)
    if extended:
        a,b,c=tile["triple"];marks[2*x-2,2*y-1]=a;marks[2*x+2,2*y-1]=c
    return occupancy,marks

class Graph:
    def __init__(self,universe,pattern,height,top,blank="B",extended=False):
        self.universe=universe;self.pattern=tuple(tuple(dict.fromkeys(s)) for s in pattern);self.extended=extended
        self.width=len(pattern);self.height=height;self.required=frozenset((x,y) for y in range(height) for x in range(self.width))
        if type(height) is not int or height<=0 or len(top)!=self.width or self.width<3:raise ValueError("invalid rectangle")
        if any(not s or any(v not in universe.symbol_set for v in s) for s in self.pattern):raise ValueError("invalid bottom pattern")
        self.boundary={};self.marks={};self.domains={};self.selected={};self.order=[];self.trail=[]
        self.tile_generations=[];self.dead=set();self.forced=set();self.heap=[];self.metrics=Counter()
        for x,s in enumerate(top):self.boundary[2*x,2*height-1]=s
        for y in range(height):
            self.boundary[-1,2*y]=(blank,blank);self.boundary[2*self.width-1,2*y]=(blank,blank)
        for x,allowed in enumerate(self.pattern):
            if len(allowed)==1:self.boundary[2*x,-1]=allowed[0]
        self.marks=self.boundary.copy();self.blank=blank
        for p in self.required:self.replace(p,self.calculate(p))
        self.initial_candidate_count=sum(d.count for d in self.domains.values())
    def calculate(self,p):
        x,y=p;kw={}
        if y==0:
            kw={"allowed_a":self.pattern[x-1] if x else (self.blank,),"allowed_b":self.pattern[x],
                "allowed_c":self.pattern[x+1] if x+1<self.width else (self.blank,)}
        if self.extended:
            for name,pair in (("allowed_a",(2*x-2,2*y-1)),("allowed_c",(2*x+2,2*y-1))):
                if pair in self.marks:
                    old=kw.get(name);value=self.marks[pair]
                    kw[name]=(value,) if old is None or value in old else ()
        return self.universe.domain(**kw,north=self.marks.get((2*x,2*y+1)),south=self.marks.get((2*x,2*y-1)),
                                    west=self.marks.get((2*x-1,2*y)),east=self.marks.get((2*x+1,2*y)))
    def replace(self,p,domain):
        self.dead.discard(p);self.forced.discard(p)
        if domain is None:self.domains.pop(p,None);return
        self.domains[p]=domain
        if domain.count==0:self.dead.add(p)
        elif domain.count==1:self.forced.add(p)
        else:heapq.heappush(self.heap,(p[1],p[0],domain.count))
    def decision(self):
        if self.dead:return "dead",min(self.dead,key=lambda p:(p[1],p[0])),None
        if self.forced:
            p=min(self.forced,key=lambda p:(p[1],p[0]));return "forced",p,self.domains[p]
        if not self.domains:return "empty",None,None
        while self.heap:
            y,x,count=self.heap[0];p=x,y
            if p in self.domains and self.domains[p].count==count:return "branch",p,self.domains[p]
            heapq.heappop(self.heap)
        raise AssertionError("frontier missing priority entry")
    def place(self,p,triple):
        if p not in self.domains or not self.domains[p].contains(triple):raise ValueError("illegal point placement")
        x,y=p;tile=self.universe.tile(triple);_,marks=point_tile(tile,x,y,self.extended)
        if any(q in self.marks and self.marks[q]!=s for q,s in marks.items()):raise AssertionError("domain/mark disagreement")
        added=[q for q in marks if q not in self.marks]
        if self.extended:
            # Vertical value points occur as N of one cell and as the three
            # bottom value points of its own row. Horizontal pair points keep
            # the original two-cell dependency. Include every such owner.
            affected={p}
            for mx,my in marks:
                if mx%2==0:
                    j=mx//2;row=(my+1)//2
                    affected.update(((j,row-1),(j-1,row),(j,row),(j+1,row)))
                else:
                    row=my//2;j=(mx+1)//2;affected.update(((j,row),(j-1,row)))
            affected=sorted(q for q in affected if q in self.required)
        else:affected=[q for q in (p,(x-1,y),(x+1,y),(x,y-1),(x,y+1)) if q in self.required]
        prior={q:self.domains.get(q) for q in affected}
        self.trail.append((p,added,prior));self.selected[p]=triple;self.order.append(p);self.tile_generations.append(1)
        self.marks.update(marks);self.replace(p,None)
        for q in affected:
            if q!=p and q not in self.selected:self.replace(q,self.calculate(q))
        self.metrics["placements"]+=1;self.metrics["domain_updates"]+=len(affected)
    def rollback(self,token):
        if type(token) is not int or not 0<=token<=len(self.trail):raise ValueError("invalid rollback token")
        while len(self.trail)>token:
            p,added,prior=self.trail.pop();del self.selected[p];self.order.pop();self.tile_generations.pop()
            for q in added:del self.marks[q]
            for q,domain in prior.items():self.replace(q,domain)
            self.metrics["rollback_placements"]+=1
    def fingerprint(self):
        return self.selected.copy(),self.marks.copy(),{p:(d.count,d.blocks) for p,d in self.domains.items()},self.order.copy(),self.tile_generations.copy()

def search(compiler,pattern,height,top,node_limit=100000,seconds=20,preferred=None,extended=False):
    start=time.monotonic();u=Universe(compiler);g=Graph(u,pattern,height,top,extended=extended)
    nodes=forced=branches=backtracks=0;frames=[];success=False;status="unknown_budget";preferred=preferred or {}
    def choices(p,d):
        wanted=preferred.get(p)
        if wanted is not None and d.contains(wanted):yield wanted
        for triple in d.options():
            if triple!=wanted:yield triple
    def next_alternative():
        nonlocal backtracks,nodes
        while frames:
            token,p,options=frames[-1];g.rollback(token)
            try:triple=next(options)
            except StopIteration:frames.pop();backtracks+=1;continue
            g.place(p,triple);nodes+=1;backtracks+=1;return True
        return False
    while True:
        if nodes>=node_limit or time.monotonic()-start>=seconds:break
        mode,p,domain=g.decision()
        if mode=="dead":
            if not next_alternative():status="exhausted_finite_rectangle";break
        elif mode=="empty":status="finite_accepting_proof_rectangle";success=True;break
        elif mode=="forced":g.place(p,next(domain.options()));forced+=1;nodes+=1
        else:
            branches+=1;options=iter(choices(p,domain));frames.append((len(g.trail),p,options))
            g.place(p,next(options));nodes+=1
    result={"status":status,"nodes":nodes,"forced":forced,"branches":branches,"backtracks":backtracks,
            "seconds":time.monotonic()-start,"width":g.width,"height":height,"tile_types":u.inventory_count,
            "initial_candidate_nodes":g.initial_candidate_count,"placed_centers":len(g.selected),
            "metrics":dict(g.metrics),"universe_metrics":dict(u.metrics),"symbolic_domain_signatures":len(u.cache),
            "budget":{"nodes":node_limit,"seconds":seconds},
            "marking":"redundant-neighbor-values" if extended else "standard-Wang-colors",
            "scheduler":"global dead, global forced; all root generations zero; branch tie by row then column",
            "scope":"fixed finite word-buffer/certificate/rectangle bounds; complete symbolic domains and base fallback"}
    if success:
        placements=[(x,y,u.tile(g.selected[x,y])) for y in range(height) for x in range(g.width)]
        initial=tuple(g.selected[x,0][1] for x in range(g.width))
        rows=[initial]+[tuple(u.tile(g.selected[x,y])["N"] for x in range(g.width)) for y in range(height)]
        assert independent_check(compiler,pattern,top,rows,placements,extended=extended)
        result.update({"initial":initial,"rows":rows,"placements":placements,"verified":True,
                       "tile_generations":g.tile_generations.copy()})
    return result

def independent_check(compiler,pattern,top,rows,placements,blank="B",extended=False):
    """Direct TM and all point sums/agreement; no symbolic domain/count code."""
    try:
        if len(rows)<2 or any(len(row)!=len(pattern) for row in rows):return False
        if any(s not in allowed for s,allowed in zip(rows[0],pattern)) or tuple(rows[-1])!=tuple(top):return False
        if any(wang.direct_step(compiler,a)!=tuple(b) for a,b in zip(rows,rows[1:])):return False
        width=len(pattern);height=len(rows)-1;totals=Counter();marks={};seen=set();symbols=set(compiler.symbols)
        for x,y,tile in placements:
            if type(x) is not int or type(y) is not int or not (0<=x<width and 0<=y<height) or (x,y) in seen:return False
            seen.add((x,y));a,b,c=tile["triple"]
            if a not in symbols or b not in symbols or c not in symbols:return False
            n=compiler.rule(a,b,c)
            if n is None or tile!={"S":b,"N":n,"W":(a,b),"E":(b,c),"triple":(a,b,c)}:return False
            if b!=rows[y][x] or n!=rows[y+1][x]:return False
            occupancy,m=point_tile(tile,x,y,extended);totals.update(occupancy)
            for p,v in m.items():
                if p in marks and marks[p]!=v:return False
                marks[p]=v
            if x==0 and tile["W"]!=(blank,blank):return False
            if x==width-1 and tile["E"]!=(blank,blank):return False
        return len(seen)==width*height and all(v==1 for v in totals.values())
    except (ValueError,TypeError,KeyError,IndexError):return False

def preferred_from_rows(compiler,rows,blank="B"):
    return {(x,y):((before[x-1] if x else blank),before[x],(before[x+1] if x+1<len(before) else blank))
            for y,before in enumerate(rows[:-1]) for x in range(len(before))}
