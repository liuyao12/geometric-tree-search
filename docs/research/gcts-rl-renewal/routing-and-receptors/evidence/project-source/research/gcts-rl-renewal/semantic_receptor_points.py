"""Exact factored command/guard/input-port model for registered semantic lemmas.

Each proof slot has C, G and a fixed number of input-field obligations. Ordinary
commands use no-input fillers. A block command selects a checked ground interface;
each active input field independently chooses any strict-earlier source.
"""
import collections,copy,time
from certificate_boundary_search import canonical,choices
from native_receptor_points import assignment,merge,search as reference_search
from turtle import CAPACITY,Placement,State

def center(j,role):return (4*j,role)
def mode_point(j):return (4*j+2,90)
def input_point(j,k):return (4*j+2,100+k)

class Model:
    def __init__(self,spec,compiled,inventory):
        if compiled['status']!='complete' or inventory['status']!='native_accepted':raise ValueError('unfinished catalog is not authority')
        self.spec=spec;self.compiled=compiled;self.inventory=inventory;self.metrics=collections.Counter()
        self.dependencies=collections.defaultdict(set);self.cache={};self.align_cache={};self.metadata={};self.conflicts=[]
        defs={d['name']:d for d in inventory['definitions']}
        self.interfaces=[defs[n] for n in inventory['interfaces']]
        self.arity=max([len(d['definition']['premises']) for d in self.interfaces]+[0])
        self.mode={d['name']:i+1 for i,d in enumerate(self.interfaces)};self.mode_names={v:k for k,v in self.mode.items()}
        self.domains=[];began=time.perf_counter();taut={canonical(f) for f in compiled['tautologies']}
        for j in range(spec['length']):
            for role in range(2+self.arity):self.align_cache[center(j,role)]=[]
            rows=choices(spec,j,compiled['basis'],compiled['variables'])
            formulas=[spec['target']] if j+1==spec['length'] else compiled['basis']
            rows += [dict(rule='block',formula=f,name=d['name']) for f in formulas for d in self.interfaces]
            rows.sort(key=lambda c:(c['rule'],canonical(c['formula']),canonical(c)));self.domains.append(rows)
            for k,c in enumerate(rows):
                f=c['formula'];rule=c['rule'];mode=self.mode[c['name']] if rule=='block' else 0
                entries=assignment(j,'command',c)+assignment(j,'formula',f)+[(mode_point(j),mode)]
                self.add((j,0,k,0),entries,c,[],'command')
                req=[]
                if rule=='axiom':valid=spec['theory']['axioms'][c['name']]==f
                elif rule=='refl':valid=f[0]=='eq' and f[1]==f[2]
                elif rule=='tautology':valid=canonical(f) in taut
                elif rule=='generalize':
                    valid=f[0]=='all' and f[1]==c['variable']
                    if valid:req=[(c['source'],f[2])]
                elif rule=='block':valid=defs[c['name']]['definition']['conclusion']==f
                else:
                    for variant,imp in enumerate(compiled['basis']):
                        if imp[0]=='imp' and imp[2]==f:
                            wanted=[(c['antecedent'],imp[1]),(c['implication'],imp)]
                            self.add((j,1,k,variant),entries+[e for i,a in wanted for e in assignment(i,'formula',a)],c,wanted,'guard')
                    continue
                if valid:self.add((j,1,k,0),entries+[e for i,a in req for e in assignment(i,'formula',a)],c,req,'guard')
            # Every input-field root exists even for non-block commands.
            for r in range(self.arity):
                self.add((j,2+r,0,0),[(mode_point(j),0),(input_point(j,r),-1)],None,[],'unused_input',input=r,mode=0,source=None)
                for d in self.interfaces:
                    mode=self.mode[d['name']];premises=d['definition']['premises']
                    if r>=len(premises):
                        self.add((j,2+r,mode,0),[(mode_point(j),mode),(input_point(j,r),-1)],None,[],'unused_input',input=r,mode=mode,source=None)
                    else:
                        for source in range(j):
                            req=[(source,premises[r])]
                            self.add((j,2+r,mode,source+1),[(mode_point(j),mode),(input_point(j,r),source)]+assignment(source,'formula',premises[r]),None,req,'lemma_input',input=r,mode=mode,source=source)
        self.compile_seconds=time.perf_counter()-began
        for p in self.align_cache:self.align_cache[p]=tuple(self.align_cache[p])
    def add(self,key,entries,command,requirements,kind,**extra):
        marks=merge(entries)
        if marks is None:self.conflicts.append(dict(key=key,reason='internally unequal markings'));return
        if key in self.cache:raise ValueError('duplicate placement')
        p=center(key[0],key[1]);tile=Placement(key,((p,CAPACITY),),marks,())
        self.cache[key]=tile;self.metadata[key]=dict(slot=key[0],kind=kind,command=command,requirements=requirements,**extra)
        self.align_cache[p].append(key)
        for q,_ in tile.occupancy+tile.marks:self.dependencies[q].add(key)
    def alignments(self,p):return self.align_cache[p]
    def placement(self,k):return self.cache[k]
    def initial(self):
        roots={p:0 for p in self.align_cache}
        return State(marks=dict(assignment(self.spec['length']-1,'formula',self.spec['target'])),generations=roots.copy(),roots=roots.copy(),allowed_points=frozenset(roots))
    def decode(self,placements):
        selected={center(k[0],k[1]):k for k in placements};proof=[]
        if set(selected)!=set(self.align_cache):raise ValueError('incomplete proof rectangle')
        for j in range(self.spec['length']):
            c=copy.deepcopy(self.metadata[selected[center(j,0)]]['command'])
            g=self.metadata[selected[center(j,1)]]
            if c!=g['command']:raise ValueError('command/guard words disagree')
            if c['rule']=='block':
                d=next(d for d in self.interfaces if d['name']==c['name']);n=len(d['definition']['premises'])
                inputs=[self.metadata[selected[center(j,2+r)]]['source'] for r in range(n)]
                if any(i is None or not 0<=i<j for i in inputs):raise ValueError('invalid earlier premise field')
                c['inputs']=inputs
            proof.append(c)
        return proof
    def record(self):
        return dict(domains=self.domains,command_counts=list(map(len,self.domains)),arity=self.arity,mode_ids=self.mode,
                    placements=[dict(key=k,occupancy=c.occupancy,marks=c.marks,**self.metadata[k]) for k,c in sorted(self.cache.items())],
                    conflicts=self.conflicts,roots=sorted(self.align_cache),compile_seconds=self.compile_seconds,
                    encoding='Canonical full JSON words with integer terminator 256; exact mode and source-index values at additional points.',
                    scope='Factored six-rule certificate grammar with registered ground lemma interfaces. Separate auxiliary roots choose every strict-earlier input independently. This changes the high-level grammar; it is not occupancy compression of the older two-center point region.')

def search(model,attempts=20000,seconds=60):
    r=reference_search(model,attempts=attempts,seconds=seconds)
    r['command_skeleton']=r['proof']
    if r['proof'] is not None:r['proof']=model.decode(r['placements'])
    r['scope']='Unchanged reference complete point scheduler on the new factored lemma grammar. Every command, guard and input-field root is active. No new RL or learned pruning in this increment.'
    return r
