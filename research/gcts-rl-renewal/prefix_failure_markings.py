"""Learn instance-scoped, redundant marking values from exhausted prefixes.

Teachers always use the original point model.  A cutoff is never a negative.
The extra values enter State/Graph through ordinary, distant marking points;
no prefix lookup, proof evaluator or learned clause scanner runs in search.
This is a proof-strip adaptation, not the Turtle pair-corona protocol.
"""
import collections,copy,time
from certificate_boundary_search import canonical,digest
from semantic_receptor_points import Model
from semantic_inventory_search import search
from native_receptor_points import assignment
from turtle import Placement

def context(model):
    return dict(theory=model.spec['theory'],basis=model.compiled['basis'],
        variables=model.compiled['variables'],tautologies=model.compiled['tautologies'],
        definitions=model.inventory['definitions'],interfaces=model.inventory['interfaces'],
        native_blocks=model.inventory['native_blocks'],arity=model.arity,
        mode_ids=model.mode,
        encoding='Exact canonical command/formula words and strict earlier source ports; semantic-receptor model 001')

def identity(tile):
    # Positional inventory keys can change when the final command domain is
    # restricted. Matching the complete decorations establishes the lift.
    return canonical(dict(occupancy=tile.occupancy,marks=tile.marks))

def prefix_spec(spec,length,formula):
    out=copy.deepcopy(spec);out.update(id=spec['id']+'-prefix-'+str(length)+'-'+digest(formula)[:12],
        length=length,target=copy.deepcopy(formula),
        scope='Unmarked finite prefix with the same whole-case vocabulary and checked lemma registry.')
    return out

def catalog(model):
    initial=model.initial();groups=collections.defaultdict(list)
    for key,c in sorted(model.cache.items()):
        if key[1]==0 and initial.legal(c):
            groups[key[0],canonical(model.metadata[key]['command']['formula'])].append(key)
    formulas={canonical(f):f for f in model.compiled['basis']}
    return [dict(id=i,slot=j,length=j+1,formula=formulas[word],command_keys=keys)
            for i,((j,word),keys) in enumerate(sorted(groups.items()))]

def prefix_lift(parent,teacher,formula):
    """Finite structural evidence for the causal restriction argument.

    Every command/guard at the last prefix row must output this formula.
    Every other original positional candidate is retained. Premise fields and
    mode IDs have identical domains; no candidate reads a later row.
    """
    n=teacher.spec['length'];required={}
    for k,c in parent.cache.items():
        if k[0]>=n:continue
        if k[0]+1==n and k[1]<2 and parent.metadata[k]['command']['formula']!=formula:continue
        word=identity(c)
        if word in required:raise ValueError('undistinguished positional inventory identity')
        required[word]=k
    lifted=[]
    for k,c in sorted(teacher.cache.items()):
        word=identity(c)
        if word not in required:raise ValueError('prefix introduced a different decorated candidate')
        if any(p[0]>4*k[0]+2 for p,v in c.marks):raise ValueError('candidate reads a future row')
        lifted.append((k,required.pop(word)))
    if required:raise ValueError('prefix restriction omitted an original candidate')
    if set(teacher.align_cache)!={p for p in parent.align_cache if p[0]<4*n}:
        raise ValueError('prefix required roots do not restrict the full rectangle')
    return dict(pairs=lifted,sha256=digest(lifted),scope=
        'Exact equality of all decorated candidates in the necessary prefix restriction. A full region with this last-prefix formula restricts to these roots; strict earlier references ensure no omitted future marking is needed.')

def learn(model,attempts=1000,seconds=.5,check=None):
    began=time.perf_counter();rows=catalog(model);probes=[];counts=collections.Counter()
    for row in rows:
        spec=prefix_spec(model.spec,row['length'],row['formula'])
        teacher=Model(spec,model.compiled,model.inventory)
        lift=prefix_lift(model,teacher,row['formula'])
        result=search(teacher,'base',attempts=attempts,seconds=seconds)
        label={'finite_marked_proof_region':'positive',
               'exhausted_finite_marked_region':'negative',
               'unknown_search_budget':'unknown'}[result['status']]
        counts[label]+=1
        probe=dict(**row,spec=spec,model=teacher.record(),lift=lift,label=label,search=result)
        if check is not None:probe['independent_check']=check(model,probe)
        probes.append(probe)
    return dict(version='prefix-failure-learning-001',context=context(model),
        context_sha256=digest(context(model)),catalog=rows,probes=probes,
        counts=dict(counts),seconds=time.perf_counter()-began,
        limits=dict(attempts=attempts,seconds=seconds),
        scope='Online exhaustive-prefix constraint synthesis in a fixed finite proof grammar, starting with no additional markings. Native-admitted logical markings and checked semantic lemmas are reused. All resolved samples are retained; unknowns impose no constraint. Not a pair-corona learner, global mathematical unprovability claim or universal compiler theorem.')

def port(slot,formula_index):return (4*slot+3,100000+formula_index)

class MarkedModel(Model):
    def __init__(self,base,learning,certificate):
        if certificate.get('status')!='passed' or certificate['learning_sha256']!=digest(learning):
            raise ValueError('failure layer requires the independently checked transcript')
        if context(base)!=learning['context'] or certificate['context_sha256']!=digest(context(base)):
            raise ValueError('failure marking belongs to another theory, vocabulary or lemma registry')
        self.__dict__=base.__dict__.copy();self.cache=base.cache.copy()
        self.dependencies=collections.defaultdict(set,{p:set(ks) for p,ks in base.dependencies.items()})
        self.metrics=collections.Counter();self.exterior={};self.failures=[]
        indices={canonical(f):i for i,f in enumerate(base.compiled['basis'])}
        original_values={k:dict(c.marks) for k,c in base.cache.items()}
        for probe in learning['probes']:
            if probe['label']!='negative':continue
            if probe['search']['status']!='exhausted_finite_marked_region':
                raise ValueError('unfinished prefix cannot supply an exclusion')
            p=port(probe['slot'],indices[canonical(probe['formula'])]);self.exterior[p]=0
            word=assignment(probe['slot'],'formula',probe['formula'])
            # Propagate the certified value to every complete writer of that
            # formula word: its output, rule guard and any distant consumer.
            # The certificate proves that no full region can include one.
            keys=[k for k,c in base.cache.items()
                  if all(original_values[k].get(q)==v for q,v in word)]
            for k in keys:
                c=self.cache[k]
                if any(q==p for q,v in c.occupancy+c.marks):raise ValueError('failure port collides with original data')
                self.cache[k]=Placement(c.key,c.occupancy,tuple(sorted(c.marks+((p,1),))),c.vertices)
                self.dependencies[p].add(k)
            self.failures.append(dict(probe=probe['id'],slot=probe['slot'],formula=probe['formula'],point=p,
                exterior_value=0,tile_value=1,affected_keys=sorted(keys),
                by_kind=dict(collections.Counter(base.metadata[k]['kind'] for k in keys))))
        self.learning_pin=digest(learning);self.certificate=certificate
        if set(self.cache)!=set(base.cache) or self.align_cache!=base.align_cache:
            raise ValueError('failure learning changed the original candidate universe')
    def initial(self):
        state=super().initial();state.marks.update(self.exterior);return state
    def record(self):
        out=super().record();out.update(failure_overlay=dict(context_sha256=digest(context(self)),
            learning_sha256=self.learning_pin,certificate=self.certificate,
            exterior=sorted(self.exterior.items()),failures=self.failures),
            initial_marks=sorted(self.initial().marks.items()),
            scope='Identical original t-data, roots, positional identities and alignments; additional exact marking values at distant points, independently certified redundant for this prefix context. Search uses the ordinary point/candidate graph only.')
        return out
