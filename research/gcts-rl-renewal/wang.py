"""Finite accepting-computation certificates compiled to equality-marked points.

General radius-one Turing transition compiler, not a universal-machine proof.
The demo machine writes two ones and halts. The checker is independent of the
tiling search and rejects every invalid transition or mismatched point marking.
"""
from itertools import product

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
