"""Complete first-order point grammar with optional checked family commands."""
import collections,copy,math,time
from certificate_boundary_search import canonical
from first_order_receptors import domains
from native_receptor_points import assignment
from semantic_receptor_points import Model as Factored,center,mode_point,input_point

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
            for role in range(2+arity):self.align_cache[center(j,role)]=[]
            rows=domains(spec,compiled['catalog'],j)
            formulas=[spec['target']] if j+1==spec['length'] else compiled['basis']
            rows += [dict(rule='block',formula=f,name=d['name']) for f in formulas for d in self.interfaces]
            rows.sort(key=lambda c:(c['rule'],canonical(c['formula']),canonical(c)));self.domains.append(rows)
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
    def record(self):
        r=super().record();r.update(complete_words=math.prod(map(len,self.domains)),initial_marks=sorted(self.initial().marks.items()),families_enabled=self.families_enabled,
            scope='New first-order plus checked-family adapter. C/G and all declared input roots exist in every lane, including unused fillers in the primitive grammar. Enabling families changes the candidate inventory; ordering controls preserve that inventory. Full word markings, strict earlier input receptors, translation-only fixed roles and exact unit occupancy.')
        return r
