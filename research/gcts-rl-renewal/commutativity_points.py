"""Prospective point geometry only; no forged native authority or target search.

Copied explicit C/G/I1/I2 generation from the frozen induction adaptation. All
templates remain potentially valid during preflight, even if unadmitted. The
object deliberately refuses proof decode and search authority.
"""
import collections,copy,time
from certificate_boundary_search import canonical
from catalog_receptor_points import Catalog
from semantic_receptor_points import Model as Factored,center,mode_point,input_point
from turtle import State

class ProspectiveModel(Factored):
    def __init__(self,spec,catalog):
        self.spec=spec;self.compiled=catalog;self.arity=2;self.metrics=collections.Counter();self.dependencies=collections.defaultdict(set)
        self.cache={};self.align_cache={};self.metadata={};self.conflicts=[];self.definitions=catalog['definitions'];self.inventory=dict(status='prospective_native_unadmitted')
        self.domains=[];self.mode={};self.mode_names={};self.rule_modes={};self.rules=catalog['rules'];began=time.perf_counter()
        for i,r in enumerate(self.rules):
            self.rule_modes[i]=i+1 if r['premises'] else 0
            if r['premises'] and r['command']['rule']=='block':self.mode[r['command']['name']]=i+1;self.mode_names[i+1]=r['command']['name']
        for j in range(spec['length']):self.domains.append([dict(rule=i,command=copy.deepcopy(r['command'])) for i,r in enumerate(self.rules) if j+1<spec['length'] or canonical(r['conclusion'])==canonical(spec['target'])])
        self.catalog=Catalog(catalog['basis'],[r['command'] for r in self.rules]);assign=self.catalog.assignment
        for j,rows in enumerate(self.domains):
            for role in range(4):self.align_cache[center(j,role)]=[]
            for k,row in enumerate(rows):
                i=row['rule'];r=self.rules[i];c=row['command'];mode=self.rule_modes[i];marks=assign(j,'command',c)+assign(j,'formula',r['conclusion'])+[(mode_point(j),mode)]
                self.add((j,0,k,0),marks,c,[],'command',inference=i);self.add((j,1,k,0),marks,c,[],'guard',inference=i)
            for role in range(2):
                self.add((j,2+role,0,0),[(mode_point(j),0),(input_point(j,role),-1)],None,[],'unused_input',input=role,mode=0,source=None)
                for i,r in enumerate(self.rules):
                    mode=self.rule_modes[i]
                    if not mode:continue
                    if role>=len(r['premises']):self.add((j,2+role,mode,0),[(mode_point(j),mode),(input_point(j,role),-1)],None,[],'unused_input',input=role,mode=mode,source=None)
                    else:
                        for source in range(j):
                            p=r['premises'][role];self.add((j,2+role,mode,source+1),[(mode_point(j),mode),(input_point(j,role),source)]+assign(source,'formula',p),None,[(source,p)],'inference_input',input=role,mode=mode,source=source)
        self.compile_seconds=time.perf_counter()-began
        for p in self.align_cache:self.align_cache[p]=tuple(self.align_cache[p])
    def initial(self):
        roots={p:0 for p in self.align_cache};return State(marks=dict(self.catalog.assignment(self.spec['length']-1,'formula',self.spec['target'])),generations=roots.copy(),roots=roots.copy(),allowed_points=frozenset(roots))
    def decode(self,placements):raise ValueError('prospective native-unadmitted geometry is not a proof-search model')
    def record(self):
        r=super().record();r.update(initial_marks=sorted(self.initial().marks.items()),catalog=self.catalog.record(),inference_rules=self.rules,authority='prospective_native_unadmitted',scope='Complete exact C/G/I1/I2 geometry for capacity/graph preflight only. Every potentially valid retained interface and prior source is represented. No target search or proof decode allowed.')
        return r

def row_keys(model,row,rule,sources):
    matches=[k for k,d in enumerate(model.domains[row]) if d['rule']==rule]
    if len(matches)!=1:raise ValueError('one existing command candidate required')
    k=matches[0];r=model.rules[rule];mode=model.rule_modes[rule];out=[(row,0,k,0),(row,1,k,0)]
    if len(sources)!=len(r['premises']):raise ValueError('exact source arity')
    for role in range(2):out.append((row,2+role,mode,sources[role]+1 if role<len(sources) else 0))
    return out

def aggregate(model,keys):
    keys=list(dict.fromkeys(keys));totals={};marks={}
    for k in keys:
        tile=model.placement(k)
        for p,v in tile.occupancy:
            totals[p]=totals.get(p,0)+v
            if totals[p]>12:return None
        for p,v in tile.marks:
            if p in marks and marks[p]!=v:return None
            marks[p]=v
    return dict(keys=keys,occupancy=sorted(totals.items()),marks=sorted(marks.items()))
