"""Finite accepting-computation certificates compiled to equality-marked points.

General radius-one Turing transition compiler, not a universal-machine proof.
The demo machine writes two ones and halts. The checker is independent of the
tiling search and rejects every invalid transition or mismatched point marking.
"""
from itertools import product
import time

def head(q,a): return ("head",q,a)

class Compiler:
    def __init__(self,alphabet,states,transitions,halt):
        self.alphabet = tuple(alphabet)
        self.states = tuple(states)
        self.transitions = dict(transitions)
        self.halt = halt
        self.symbols = self.alphabet + tuple(head(q,a) for q in states for a in alphabet)
    def rule(self,a,b,c):
        # Local neighborhoods of a legal single-head configuration have <=1 head.
        heads = [x for x in (a,b,c) if isinstance(x,tuple)]
        if len(heads)>1: return None
        if isinstance(b,tuple):
            _,q,s = b
            if q==self.halt: return b  # Absorbing accepting state.
            if (q,s) not in self.transitions: return None
            q2,w,d = self.transitions[q,s]
            return head(q2,w) if d==0 else w
        incoming = []
        for x,direction in ((a,1),(c,-1)):
            if isinstance(x,tuple) and x[1]!=self.halt:
                transition = self.transitions.get((x[1],x[2]))
                if transition and transition[2]==direction: incoming.append(transition[0])
        return head(incoming[0],b) if len(incoming)==1 else (b if not incoming else None)
    def tiles(self):
        return [{"S":b,"N":d,"W":(a,b),"E":(b,c),"triple":(a,b,c)}
                for a,b,c in product(self.symbols,repeat=3) if (d:=self.rule(a,b,c)) is not None]

def point_tile(tile,x,y):
    # Doubled integer grid. Occupancy only at even/even centers; edge marking
    # points are in separate parity classes, so corners cannot impose extras.
    t = {(2*x,2*y):1}
    m = {(2*x,2*y-1):tile["S"],(2*x,2*y+1):tile["N"],
         (2*x-1,2*y):tile["W"],(2*x+1,2*y):tile["E"]}
    return t,m

def direct_step(compiler,row):
    """Independent operational TM semantics on a bounded tape."""
    result = list(row)
    heads = [(i,s) for i,s in enumerate(row) if isinstance(s,tuple)]
    if len(heads)!=1: raise ValueError("one head required")
    i,(_,q,a) = heads[0]
    if q==compiler.halt: return tuple(result)
    q2,w,d = compiler.transitions[q,a]
    j = i+d
    if not 0<=j<len(row): raise ValueError("head crossed finite tape boundary")
    result[i] = w
    result[j] = head(q2,w if i==j else row[j])
    return tuple(result)

def certificate_check(compiler,initial,rows,placements):
    if not rows or tuple(rows[0])!=tuple(initial): return False
    for before,after in zip(rows,rows[1:]):
        try:
            if direct_step(compiler,before)!=tuple(after): return False
        except (ValueError,KeyError): return False
    if not any(isinstance(s,tuple) and s[1]==compiler.halt for s in rows[-1]): return False
    inventory = {repr(t) for t in compiler.tiles()}
    totals = {}
    marks = {}
    for x,y,tile in placements:
        if repr(tile) not in inventory: return False
        if tile["S"]!=rows[y][x] or tile["N"]!=rows[y+1][x]: return False
        t,m = point_tile(tile,x,y)
        for p,v in t.items(): totals[p] = totals.get(p,0)+v
        for p,v in m.items():
            if p in marks and marks[p]!=v: return False
            marks[p] = v
    target = {(2*x,2*y) for y in range(len(rows)-1) for x in range(len(initial))}
    return set(totals)==target and all(v==1 for v in totals.values())

def search_rectangle(compiler,initial,height,blank=0):
    """Actual finite candidate search, global dead/forced then generation order.

    All rectangle cells are root obligations at generation zero. This is a
    separate fixed-boundary Wang control, not the unmarked turtle learner.
    """
    width = len(initial)
    inventory = compiler.tiles()
    required = {(x,y) for y in range(height) for x in range(width)}
    boundary = {}
    for x,s in enumerate(initial): boundary[(2*x,-1)] = s
    for y in range(height):
        boundary[(-1,2*y)] = (blank,blank)
        boundary[(2*width-1,2*y)] = (blank,blank)
    # Top boundary requires one accepting head; enumerate its location/symbol.
    nodes = forced = branches = 0
    found = None
    def visit(selected,marks):
        nonlocal nodes,forced,branches,found
        nodes += 1
        if len(selected)==len(required):
            top = [marks[(2*x,2*height-1)] for x in range(width)]
            if sum(isinstance(s,tuple) and s[1]==compiler.halt for s in top)!=1: return False
            found = selected
            return True
        domains = {}
        for x,y in required-selected.keys():
            domains[x,y] = [t for t in inventory if all(p not in marks or marks[p]==v for p,v in point_tile(t,x,y)[1].items())]
        if any(not cs for cs in domains.values()): return False
        singleton = sorted(p for p,cs in domains.items() if len(cs)==1)
        p = singleton[0] if singleton else min(domains,key=lambda p:(len(domains[p]),p[1],p[0]))
        if singleton: forced += 1
        else: branches += 1
        x,y = p
        for tile in domains[p]:
            selected2,marks2 = selected.copy(),marks.copy()
            selected2[p] = tile
            marks2.update(point_tile(tile,x,y)[1])
            if visit(selected2,marks2): return True
        return False
    visit({},boundary)
    if found is None: return {"status":"exhausted_finite_rectangle","nodes":nodes}
    placements = [(x,y,t) for (x,y),t in sorted(found.items(),key=lambda item:(item[0][1],item[0][0]))]
    rows = [initial]
    for y in range(height): rows.append(tuple(found[x,y]["N"] for x in range(width)))
    assert certificate_check(compiler,initial,rows,placements)
    return {"status":"finite_accepting_computation","tile_types":len(inventory),"nodes":nodes,
            "forced":forced,"branches":branches,"rows":rows,"placements":placements,"verified":True}

def demo():
    compiler = Compiler((0,1),("write1","write2","halt"),
                        {("write1",0):("write2",1,1),("write2",0):("halt",1,0)},"halt")
    initial = (0,0,head("write1",0),0,0,0,0)
    result = search_rectangle(compiler,initial,2)
    altered = list(result["rows"])
    altered[-1] = tuple(0 for _ in initial)
    result["tampered_certificate_rejected"] = not certificate_check(compiler,initial,altered,result["placements"])
    result["scope"] = "two-step toy Turing machine; general compiler, no universal-machine or theorem-prover certification"
    return result

def search_certificate_rectangle(compiler,pattern,height,blank="B",node_limit=100000,seconds=20):
    """Search an unknown certificate on the bottom boundary of a Wang rectangle.

    Each pattern entry is a finite set of allowed symbols, part of the declared
    boundary problem. Only one designated entry permits a head. Every cell is
    a generation-zero required point. Bitsets represent complete cell/candidate
    incidence; edge-mark dependencies are exactly the four adjacent cells.
    Domains shrink only from placed point markings. Snapshots restore all
    semantic data. No inference from a resource limit is made.
    """
    width=len(pattern); inventory=compiler.tiles(); full=(1<<len(inventory))-1
    masks={f:{} for f in ("N","S","E","W")}
    for i,tile in enumerate(inventory):
        for f in masks: masks[f][tile[f]]=masks[f].get(tile[f],0)|(1<<i)
    domains={}; start=time.monotonic(); nodes=forced=branches=backtracks=0; found=None
    for y in range(height):
        for x in range(width):
            bits=full
            if y==0:
                allowed=0
                for v in pattern[x]: allowed|=masks["S"].get(v,0)
                bits&=allowed
            if x==0: bits&=masks["W"].get((blank,blank),0)
            if x==width-1: bits&=masks["E"].get((blank,blank),0)
            domains[x,y]=bits
    # Python 3.9 compatibility; bit_count is available on newer Python.
    count_bits=lambda n: n.bit_count() if hasattr(n,"bit_count") else bin(n).count("1")
    neighbors=((0,1,"N","S"),(0,-1,"S","N"),(1,0,"E","W"),(-1,0,"W","E"))
    class Budget(Exception): pass
    def visit(ds,selected):
        nonlocal nodes,forced,branches,backtracks,found
        nodes+=1
        if nodes>node_limit or time.monotonic()-start>seconds: raise Budget()
        if any(bits==0 for bits in ds.values()): return False
        if not ds:
            top=[inventory[selected[x,height-1]]["N"] for x in range(width)]
            if sum(isinstance(s,tuple) and s[1]==compiler.halt for s in top)!=1: return False
            found=selected; return True
        singleton=sorted(p for p,bits in ds.items() if bits&(bits-1)==0)
        p=singleton[0] if singleton else min(ds,key=lambda p:(count_bits(ds[p]),p[1],p[0]))
        if singleton: forced+=1
        else: branches+=1
        options=ds[p]
        while options:
            bit=options&-options; options-=bit; i=bit.bit_length()-1
            tile=inventory[i]; child=ds.copy(); del child[p]
            selected2=selected.copy(); selected2[p]=i; consistent=True
            for dx,dy,f,opposite in neighbors:
                q=(p[0]+dx,p[1]+dy)
                if q in child: child[q]&=masks[opposite].get(tile[f],0)
                elif q in selected2 and inventory[selected2[q]][opposite]!=tile[f]: consistent=False
            if consistent and visit(child,selected2): return True
            backtracks+=1
        return False
    try:
        success=visit(domains,{})
        status="finite_accepting_certificate" if success else "exhausted_finite_rectangle"
    except (Budget,RecursionError): status="unknown_budget"
    result={"status":status,"tile_types":len(inventory),"width":width,"height":height,
            "nodes":nodes,"forced":forced,"branches":branches,"backtracks":backtracks,
            "seconds":time.monotonic()-start,"budget":{"nodes":node_limit,"seconds":seconds},
            "candidate_representation":"complete bitsets per required center; all root generations zero"}
    if found is not None:
        placements=[(x,y,inventory[i]) for (x,y),i in sorted(found.items(),key=lambda t:(t[0][1],t[0][0]))]
        initial=tuple(inventory[found[x,0]]["S"] for x in range(width))
        rows=[initial]+[tuple(inventory[found[x,y]]["N"] for x in range(width)) for y in range(height)]
        assert all(s in allowed for s,allowed in zip(initial,pattern))
        assert sum(isinstance(s,tuple) for s in initial)==1
        assert certificate_check(compiler,initial,rows,placements)
        result.update({"initial":initial,"rows":rows,"placements":placements,"verified":True})
    return result

def addition_machine():
    """Unary arithmetic certificate verifier, not a general proof-kernel compiler.

    Input is 1^a + 1^b = certificate $, surrounded by blank tape. Match every
    input 1 with a certificate 1, reject extra/missing symbols, then accept.
    The machine works for arbitrary finite a,b and certificate lengths.
    """
    transitions={}
    for s in ("X","+"): transitions["take",s]=("take",s,1)
    transitions["take","1"]=("seek", "X",1)
    transitions["take","="]=("finish","=",1)
    for s in ("1","X","+"): transitions["seek",s]=("seek",s,1)
    transitions["seek","="]=("consume","=",1)
    transitions["consume","Y"]=("consume","Y",1)
    transitions["consume","1"]=("return","Y",-1)
    for s in ("1","X","Y","+","="): transitions["return",s]=("return",s,-1)
    transitions["return","B"]=("take","B",1)
    transitions["finish","Y"]=("finish","Y",1)
    transitions["finish","$"]=("halt","$",0)
    return Compiler(("B","1","X","Y","+","=","$"),
                    ("take","seek","consume","return","finish","halt"),transitions,"halt")

def addition_pattern(a,b,certificate_length):
    tape=["B","B"]+["1"]*a+["+"]+["1"]*b+["="]
    pattern=[(s,) for s in tape]+[("B","1")]*certificate_length+[("$",),("B",),("B",)]
    s=pattern[2][0]; pattern[2]=(head("take",s),)
    return pattern

def certificate_demo():
    compiler=addition_machine(); pattern=addition_pattern(1,1,2)
    result=search_certificate_rectangle(compiler,pattern,32,node_limit=100000,seconds=30)
    if "initial" in result:
        tape=result["initial"]; i=tape.index("=")+1; j=tape.index("$")
        result["certificate"]="".join(tape[i:j])
        result["arithmetic_verified_independently"]=sum(s=="1" or (isinstance(s,tuple) and s[2]=="1") for s in tape[:i])==len(result["certificate"]) and set(result["certificate"])=={"1"}
        altered=list(tape); altered[i]="B"
        result["tampered_input_rejected"]=not certificate_check(compiler,altered,result["rows"],result["placements"])
    result["statement"]="1+1=2"
    result["unknown_bottom_cells"]=2
    result["scope"]="Wang search chooses an unknown unary certificate; independent TM and arithmetic verification; general first-order kernel not yet compiled"
    return result
