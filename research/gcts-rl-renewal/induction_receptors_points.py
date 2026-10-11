"""Exact scalar receptor point model for a complete finite inference catalog.

Translations only, integer occupancy 12, all C/G/I1/I2 roots generation zero.
There is no geometric rule beyond occupancy and agreement of assigned marks.
"""
import collections,copy,math,time
from certificate_boundary_search import canonical
from catalog_receptor_points import Catalog
from semantic_receptor_points import Model as Factored,center,mode_point,input_point
from turtle import State

class Model(Factored):
    def __init__(self,spec,catalog,admission):
        if admission['status']!='native_accepted':raise ValueError('unfinished native admission is not authority')
        self.spec=spec;self.compiled=catalog;self.arity=2;self.metrics=collections.Counter();self.dependencies=collections.defaultdict(set)
        self.cache={};self.align_cache={};self.metadata={};self.conflicts=[];self.definitions=catalog['definitions']
        self.inventory=dict(status=admission['status'],definitions=[dict(name=d['name'],definition=d,level=1) for d in self.definitions],native_blocks=self.definitions,interfaces=[d['name'] for d in self.definitions])
        self.interfaces=self.inventory['definitions'];self.rules=catalog['rules'];self.domains=[];self.mode={};self.mode_names={};self.rule_modes={};began=time.perf_counter()
        for i,r in enumerate(self.rules):
            if r['premises']:
                self.rule_modes[i]=i+1
                if r['command']['rule']=='block':self.mode[r['command']['name']]=i+1;self.mode_names[i+1]=r['command']['name']
            else:self.rule_modes[i]=0
        for j in range(spec['length']):
            rows=[dict(rule=i,command=copy.deepcopy(r['command'])) for i,r in enumerate(self.rules) if j+1<spec['length'] or canonical(r['conclusion'])==canonical(spec['target'])]
            self.domains.append(rows)
        self.catalog=Catalog(catalog['basis'],[r['command'] for r in self.rules]);assign=self.catalog.assignment
        for j,rows in enumerate(self.domains):
            for role in range(4):self.align_cache[center(j,role)]=[]
            for k,row in enumerate(rows):
                i=row['rule'];r=self.rules[i];c=row['command'];mode=self.rule_modes[i]
                marks=assign(j,'command',c)+assign(j,'formula',r['conclusion'])+[(mode_point(j),mode)]
                self.add((j,0,k,0),marks,c,[],'command',inference=i)
                self.add((j,1,k,0),marks,c,[],'guard',inference=i)
            # All distinct modes, including zero, have every strict-prior input
            # source. Missing sources yield degree zero globally, not a shortcut.
            mode_rules={self.rule_modes[i]:r for i,r in enumerate(self.rules) if self.rule_modes[i]}
            for role in range(2):
                self.add((j,2+role,0,0),[(mode_point(j),0),(input_point(j,role),-1)],None,[],'unused_input',input=role,mode=0,source=None)
                for mode,r in sorted(mode_rules.items()):
                    if role>=len(r['premises']):self.add((j,2+role,mode,0),[(mode_point(j),mode),(input_point(j,role),-1)],None,[],'unused_input',input=role,mode=mode,source=None)
                    else:
                        for source in range(j):
                            p=r['premises'][role];self.add((j,2+role,mode,source+1),[(mode_point(j),mode),(input_point(j,role),source)]+assign(source,'formula',p),None,[(source,p)],'inference_input',input=role,mode=mode,source=source)
        self.compile_seconds=time.perf_counter()-began
        for p in self.align_cache:self.align_cache[p]=tuple(self.align_cache[p])
    def initial(self):
        roots={p:0 for p in self.align_cache}
        return State(marks=dict(self.catalog.assignment(self.spec['length']-1,'formula',self.spec['target'])),generations=roots.copy(),roots=roots.copy(),allowed_points=frozenset(roots))
    def decode(self,placements):
        by={center(k[0],k[1]):k for k in placements};proof=[]
        if set(by)!=set(self.align_cache):raise ValueError('incomplete target')
        for j in range(self.spec['length']):
            cmeta=self.metadata[by[center(j,0)]];gmeta=self.metadata[by[center(j,1)]]
            if cmeta['command']!=gmeta['command']:raise ValueError('command guard disagreement')
            r=self.rules[cmeta['inference']];c=copy.deepcopy(cmeta['command']);inputs=[]
            for role in range(2):
                m=self.metadata[by[center(j,2+role)]]
                if m['mode']!=self.rule_modes[cmeta['inference']]:raise ValueError('input mode mismatch')
                if role<len(r['premises']):
                    src=m['source']
                    if src is None or not 0<=src<j:raise ValueError('strict earlier reference required')
                    inputs.append(src)
                elif m['source'] is not None:raise ValueError('unused input must be explicit -1')
            if c['rule']=='block':c['inputs']=inputs
            elif c['rule']=='generalize':c['source']=inputs[0]
            elif inputs:raise ValueError('undeclared primitive input')
            proof.append(c)
        return proof
    def record(self):
        r=super().record();r.update(initial_marks=sorted(self.initial().marks.items()),catalog=self.catalog.record(),inference_rules=self.rules,complete_words=math.prod(map(len,self.domains)),scope='Complete finite contextual-equation grammar represented by C/G/I1/I2 roots and extended source markings, fixed orientation, exact catalog scalar values. All native definitions must be separately accepted before this model exists. This is a high-level point adaptation, not a primitive Wang occupancy embedding or full-FOL search.')
        return r
