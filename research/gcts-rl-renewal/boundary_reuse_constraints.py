"""Two representations of the same certified, scoped writer conjunctions.

PointModel assigns ordinary extra m-values. DirectModel is a labeled constraint
control: it has no extra tile marks and updates clause-to-candidate dependencies.
The direct control is restricted to base ordering in the matched experiment.
"""
import collections
import copy
from certificate_boundary_search import digest
from native_receptor_points import assignment
from prefix_failure_markings import context
from semantic_receptor_points import Model
from turtle import Placement, State


def packet(learning, source):
    return dict(version='boundary-reuse-constraints-001', source=source,
        learning_sha256=digest(learning), context=learning['context'],
        context_sha256=learning['context_sha256'], counts=learning['counts'],
        pair_certificate=None,
        negatives=[dict(id=p['id'], slots=p['slots'], formulas=p['formulas'])
                   for p in learning['probes'] if p['label']=='negative'])


def require(base, constraints, certificate):
    if certificate.get('status') != 'passed' or certificate['packet_sha256'] != digest(constraints):
        raise ValueError('independent boundary-transfer admission required')
    if certificate['target_spec_sha256'] != digest(base.spec):
        raise ValueError('admission belongs to another boundary')
    if context(base) != constraints['context'] or digest(context(base)) != constraints['context_sha256']:
        raise ValueError('changed theory, syntax vocabulary or lemma inventory')
    if any(not 0 <= a < b < base.spec['length'] for a,b in (p['slots'] for p in constraints['negatives'])):
        raise ValueError('clause outside declared target rows')


def writers(base, constraints):
    values={k:dict(c.marks) for k,c in base.cache.items()}
    failures=[]
    for probe in constraints['negatives']:
        words=[assignment(j,'formula',f) for j,f in zip(probe['slots'],probe['formulas'])]
        groups=[{k for k,m in values.items() if all(m.get(p)==v for p,v in w)} for w in words]
        both=groups[0]&groups[1]
        failures.append(dict(probe=probe['id'],slots=probe['slots'],formulas=probe['formulas'],
            pair_point=(3,200000+2*probe['id']),single_point=(3,200001+2*probe['id']),
            left_keys=sorted(groups[0]-both),right_keys=sorted(groups[1]-both),joint_keys=sorted(both)))
    return failures


class PointModel(Model):
    def __init__(self,base,constraints,certificate):
        require(base,constraints,certificate)
        self.__dict__=base.__dict__.copy();self.cache=base.cache.copy()
        self.dependencies=collections.defaultdict(set,{p:set(ks) for p,ks in base.dependencies.items()})
        self.metrics=collections.Counter();self.exterior={};self.failures=writers(base,constraints)
        for failure in self.failures:
            if failure['joint_keys']:self.exterior[failure['single_point']]=0
            assigned=[]
            for group,value in [('left_keys',0),('right_keys',1),('joint_keys',1)]:
                point=failure['single_point'] if group=='joint_keys' else failure['pair_point']
                for key in failure[group]:
                    c=self.cache[key]
                    if any(p==point for p,v in c.occupancy+c.marks):raise ValueError('private port collision')
                    self.cache[key]=Placement(c.key,c.occupancy,tuple(sorted(c.marks+((point,value),))),c.vertices)
                    self.dependencies[point].add(key);assigned.append(dict(key=key,point=point,value=value))
            failure['assignments']=sorted(assigned,key=lambda a:a['key'])
        self.learning_pin=constraints['learning_sha256'];self.certificate=constraints['pair_certificate']
        self.transfer_certificate=certificate

    def initial(self):
        s=super().initial();s.marks.update(self.exterior);return s

    def record(self):
        return dict(super().record(),initial_marks=sorted(self.initial().marks.items()),
            conditional_overlay=dict(learning_sha256=self.learning_pin,
                context_sha256=digest(context(self)),certificate=self.certificate,
                exterior=sorted(self.exterior.items()),failures=self.failures),
            scope='Reused certified row conjunctions at independently admitted boundary. Ordinary point-value search only.')


class DirectState(State):
    def __init__(self,rules,active_left=0,active_right=0,**kwargs):
        super().__init__(**kwargs);self.rules=rules;self.active_left=active_left;self.active_right=active_right

    def copy(self):
        return DirectState(self.rules,self.active_left,self.active_right,
            totals=self.totals.copy(),marks=self.marks.copy(),generations=self.generations.copy(),
            roots=self.roots.copy(),selected=self.selected.copy(),order=self.order.copy(),
            tile_generations=self.tile_generations.copy(),allowed_points=self.allowed_points)

    def legal(self,c):
        if not super().legal(c):return False
        left,right,joint=self.rules.get(c.key,(0,0,0))
        return not (joint or left&self.active_right or right&self.active_left)

    def place(self,c,seed=False):
        changed=super().place(c,seed)
        left,right,_=self.rules.get(c.key,(0,0,0))
        newly=(left&~self.active_left)|(right&~self.active_right)
        self.active_left|=left;self.active_right|=right
        while newly:
            bit=newly&-newly;changed.add(('failure',bit.bit_length()-1));newly-=bit
        return changed


class DirectModel(Model):
    def __init__(self,base,constraints,certificate):
        require(base,constraints,certificate)
        self.__dict__=base.__dict__.copy();self.cache=base.cache.copy()
        self.dependencies=collections.defaultdict(set,{p:set(ks) for p,ks in base.dependencies.items()})
        self.metrics=collections.Counter();self.failures=writers(base,constraints)
        membership=collections.defaultdict(lambda:[0,0,0])
        for f in self.failures:
            token=('failure',f['probe']);self.dependencies[token]=set()
            for i,field in enumerate(('left_keys','right_keys','joint_keys')):
                for k in f[field]:
                    membership[k][i]|=1<<f['probe'];self.dependencies[token].add(k)
        self.rules={k:tuple(v) for k,v in membership.items()}
        self.transfer_certificate=certificate

    def initial(self):
        s=super().initial()
        return DirectState(self.rules,totals=s.totals,marks=s.marks,generations=s.generations,
            roots=s.roots,selected=s.selected,order=s.order,tile_generations=s.tile_generations,
            allowed_points=s.allowed_points)

    def record(self):
        return dict(super().record(),initial_marks=sorted(self.initial().marks.items()),
            direct_constraints=dict(failures=self.failures,
                dependency_tokens=[dict(token=('failure',f['probe']),keys=sorted(self.dependencies['failure',f['probe']]))
                                   for f in self.failures],
                membership=[dict(key=k,left=a,right=b,joint=c) for k,(a,b,c) in sorted(self.rules.items())]),
            scope='Direct writer-conjunction control, without additional tile m-values. Active clauses update complete shared candidate incidence through explicit dependency tokens. The ordinary global scheduler is unchanged; no lookahead or arc consistency.')


def original_record(model):
    return dict(model.record(),initial_marks=sorted(model.initial().marks.items()))
