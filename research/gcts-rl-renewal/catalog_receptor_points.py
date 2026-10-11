"""Exact finite-catalog receptor values, preserving all command/guard candidates.

This is a finite high-level point representation. IDs are sequential values
under a total injective canonical-word dictionary, never hash matches.
"""
import collections,copy,json,math,time
from certificate_boundary_search import canonical
from first_order_receptors import domains
from native_receptor_points import assignment as word_assignment
from semantic_receptor_points import Model as Factored,center,mode_point,input_point
from turtle import State

class Catalog:
    def __init__(self,formulas,commands):
        self.words={kind:sorted({canonical(v) for v in values}) for kind,values in [('formula',formulas),('command',commands)]}
        self.ids={kind:{w:i for i,w in enumerate(words)} for kind,words in self.words.items()}
    def assignment(self,j,kind,value):
        return [((4*j+2,0 if kind=='formula' else 1),self.ids[kind][canonical(value)])]
    def length(self,point,value):
        x,y=point
        if x%4==2 and y in (0,1):return len(self.words['formula' if y==0 else 'command'][value])+1
        return 1
    def record(self):
        return {kind:[dict(id=i,value=json.loads(w),word_hex=w.hex(),expanded_points=len(w)+1) for i,w in enumerate(words)] for kind,words in self.words.items()}

class Model(Factored):
    def __init__(self,spec,compiled,inventory,arity=3,families=True):
        if compiled['status']!='complete' or inventory['status']!='native_accepted':raise ValueError('unfinished admission is not authority')
        self.spec=spec;self.compiled=compiled;self.inventory=inventory;self.arity=arity;self.families_enabled=families
        self.metrics=collections.Counter();self.dependencies=collections.defaultdict(set);self.cache={};self.align_cache={};self.metadata={};self.conflicts=[]
        defs={d['name']:d for d in inventory['definitions']};self.interfaces=[defs[n] for n in inventory['interfaces']] if families else []
        if max([len(d['definition']['premises']) for d in self.interfaces]+[0])>arity:raise ValueError('insufficient declared input roles')
        self.mode={d['name']:i+1 for i,d in enumerate(self.interfaces)};self.mode_names={v:k for k,v in self.mode.items()}
        self.domains=[];began=time.perf_counter();tauts={canonical(f) for f in compiled['tautologies']};schemes={canonical(c) for c in compiled['admitted_schemes']}
        for j in range(spec['length']):
            rows=domains(spec,compiled['catalog'],j)
            formulas=[spec['target']] if j+1==spec['length'] else compiled['basis']
            rows += [dict(rule='block',formula=f,name=d['name']) for f in formulas for d in self.interfaces]
            rows.sort(key=lambda c:(c['rule'],canonical(c['formula']),canonical(c)));self.domains.append(rows)
        formulas=compiled['basis']+[spec['target']]+[p for d in self.interfaces for p in d['definition']['premises']]
        self.catalog=Catalog(formulas,[c for rows in self.domains for c in rows])
        assignment=self.catalog.assignment
        for j,rows in enumerate(self.domains):
            for role in range(2+arity):self.align_cache[center(j,role)]=[]
            for k,c in enumerate(rows):
                f=c['formula'];r=c['rule'];mode=self.mode[c['name']] if r=='block' else 0
                entries=assignment(j,'command',c)+assignment(j,'formula',f)+[(mode_point(j),mode)]
                self.add((j,0,k,0),entries,c,[],'command');req=[]
                if r=='mp':
                    for v,imp in enumerate(compiled['basis']):
                        if imp[0]=='imp' and imp[2]==f:
                            wanted=[(c['antecedent'],imp[1]),(c['implication'],imp)]
                            self.add((j,1,k,v),entries+[e for i,a in wanted for e in assignment(i,'formula',a)],c,wanted,'guard')
                    continue
                if r=='axiom':valid=spec['theory']['axioms'][c['name']]==f
                elif r=='refl':valid=f[0]=='eq' and f[1]==f[2]
                elif r=='tautology':valid=canonical(f) in tauts
                elif r=='generalize':
                    valid=f[0]=='all' and f[1]==c['variable']
                    if valid:req=[(c['source'],f[2])]
                elif r=='block':valid=defs[c['name']]['definition']['conclusion']==f
                else:valid=canonical(c) in schemes
                if valid:self.add((j,1,k,0),entries+[e for i,a in req for e in assignment(i,'formula',a)],c,req,'guard')
            for r in range(arity):
                self.add((j,2+r,0,0),[(mode_point(j),0),(input_point(j,r),-1)],None,[],'unused_input',input=r,mode=0,source=None)
                for d in self.interfaces:
                    mode=self.mode[d['name']];premises=d['definition']['premises']
                    if r>=len(premises):self.add((j,2+r,mode,0),[(mode_point(j),mode),(input_point(j,r),-1)],None,[],'unused_input',input=r,mode=mode,source=None)
                    else:
                        for source in range(j):
                            req=[(source,premises[r])]
                            self.add((j,2+r,mode,source+1),[(mode_point(j),mode),(input_point(j,r),source)]+assignment(source,'formula',premises[r]),None,req,'lemma_input',input=r,mode=mode,source=source)
        self.compile_seconds=time.perf_counter()-began
        for p in self.align_cache:self.align_cache[p]=tuple(self.align_cache[p])
    def initial(self):
        roots={p:0 for p in self.align_cache}
        return State(marks=dict(self.catalog.assignment(self.spec['length']-1,'formula',self.spec['target'])),generations=roots.copy(),roots=roots.copy(),allowed_points=frozenset(roots))
    def expanded_new_marks(self,item,state):
        new={}
        for k in item['pending']:
            for p,v in self.placement(k).marks:
                if p not in state.marks:new[p]=v
        return sum(self.catalog.length(p,v) for p,v in new.items())
    def record(self):
        r=super().record();r.update(complete_words=math.prod(map(len,self.domains)),initial_marks=sorted(self.initial().marks.items()),families_enabled=self.families_enabled,
            catalog=self.catalog.record(),encoding='One exact scalar per complete canonical command/formula word, under an injective finite dictionary. Mode/source fields unchanged.',
            scope='Exact finite-catalog compression of the complete Notebook 68 family point model. Candidate identities, occupancy, target roots and fixed orientations retained; no primitive Wang occupancy compression claim.')
        return r
