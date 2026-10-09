import copy,itertools,json,unittest
import wang
from binary_stack_machine import BinaryMachine
from computation_blocks import certify,check,compose,leaf,machine_data,digest
from flat_computation import from_dag,verify,problem_hash
from audit_computation_blocks import validate,dense
from stack_program import equality_program
from uniform_examples import words,operation_cases

class ComputationBlocksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=BinaryMachine();cls.d=cls.m.declaration()
    def prove(self,p,left=(),right=(),capacities=(4,4),limit=1000000,workspace_capacity=None):
        row=self.m.initial(p,left,right,capacities,workspace_capacity=workspace_capacity)
        proof=certify(self.d,row,limit)
        self.assertEqual(check(self.d,proof,proof['problem_sha256'])['result'],proof['status'])
        self.assertEqual(verify(self.d,from_dag(proof),proof['problem_sha256'])['result'],proof['status'])
        self.assertEqual(validate(self.d,json.loads(json.dumps(proof)),proof['problem_sha256'])['steps'],proof['steps'])
        actual=self.m.run(p,left,right,capacities,limit=limit,workspace_capacity=workspace_capacity)
        for k in ('status','steps','final'):self.assertEqual(json.loads(json.dumps(proof[k])),json.loads(json.dumps(actual[k])))
        return proof
    def test_operation_and_resource_controls(self):
        for name,p,l,r,c,limit in operation_cases():
            with self.subTest(name=name):self.prove(p,l,r,c,limit)
    def test_exhaustive_short_equality(self):
        for a,b in itertools.product(words(2),repeat=2):
            self.assertEqual(self.prove(equality_program(),a,b,(2,2))['status'],'accept' if a==b else 'reject')
    def test_empty_prefix_and_halt(self):
        p=self.prove((('accept',),),capacities=(0,0),limit=0);self.assertIsNone(p['root']);self.assertEqual(p['status'],'unknown_step_budget')
        row=('B',wang.head('accept','0'),'B');proof=certify(self.d,row,0);self.assertEqual(check(self.d,proof)['result'],'accept');validate(self.d,proof,proof['problem_sha256'])
    def test_nonhalting_prefix(self):self.assertEqual(self.prove((('jump',0),),capacities=(0,0),limit=10000)['status'],'unknown_step_budget')
    def test_workspace_cutoff(self):
        p=(('jump',2),('reject',),('accept',));self.assertEqual(self.prove(p,capacities=(0,0),workspace_capacity=0)['status'],'unknown_workspace_bound')
    def test_all_dense_points(self):
        proof=self.prove((('pushR1',1),('popR',3,4,3),('reject',),('accept',),('reject',)),capacities=(0,1));self.assertEqual(dense(self.d,proof),len(proof['initial'])*proof['steps'])
    def test_all_declarations_checked(self):
        proof=self.prove((('accept',),),capacities=(0,0));bad=copy.deepcopy(proof);bad['nodes'].append({'children':[len(bad['nodes']),0]})
        for checker in (check,validate):
            with self.assertRaises(ValueError):checker(self.d,bad,proof['problem_sha256'])
    def test_mutated_interfaces_and_composition(self):
        proof=self.prove((('pushR1',1),('accept',)),capacities=(0,1))
        changes=[lambda p:p['observations'][0]['interface'].__setitem__('steps',1),lambda p:p['tokens'].__setitem__(0,p['tokens'][-1]),lambda p:p['nodes'][p['root']]['children'].reverse(),lambda p:p['initial'].__setitem__(3,'R'),lambda p:p['final'].__setitem__(3,'1')]
        for change in changes:
            bad=copy.deepcopy(proof);change(bad)
            for checker in (check,validate):
                with self.assertRaises(ValueError):checker(self.d,bad,proof['problem_sha256'])
    def test_strict_data_and_limits(self):
        for limit in (True,-1,.5):
            with self.assertRaises(ValueError):certify(self.d,('B',wang.head('accept','0'),'B'),limit)
        proof=self.prove((('accept',),),capacities=(0,0))
        for key in ('steps','limit','version'):
            bad=copy.deepcopy(proof);bad[key]=True
            with self.assertRaises(ValueError):check(self.d,bad)
        self.assertEqual(verify(self.d,from_dag(proof),max_tokens=0)['status'],'unknown_certificate_budget')
        flat=from_dag(proof);flat['limit']=-1;flat['problem_sha256']=problem_hash(flat)
        with self.assertRaises(ValueError):verify(self.d,flat)
        self.assertEqual(check(self.d,proof,max_nodes=0)['status'],'unknown_certificate_budget')
        self.assertEqual(check(self.d,proof,max_cells=0)['status'],'unknown_certificate_budget')
        self.assertEqual(check(self.d,proof,max_tokens=0)['status'],'unknown_certificate_budget')
    def test_frame_and_head_tags(self):
        for row in (('B',('invalid','accept','0'),'B'),('0',wang.head('accept','0'),'B'),('B',wang.head('accept','0'),wang.head('accept','0'),'B')):
            with self.assertRaises(ValueError):certify(self.d,row)
    def test_zero_symbol_and_missing_are_distinct(self):
        # Symbol index zero is B; it must be substituted rather than treated as absent.
        a=dict(q='a',out='b',shift=0,steps=1,extent=[0,0],pre=[[0,1,2]],writes=[[0,1,0]])
        b=dict(q='b',out='c',shift=0,steps=1,extent=[0,0],pre=[[0,1,1]],writes=[])
        result=compose(a,b);self.assertEqual(result['pre'],[[0,1,2]]);self.assertEqual(result['writes'],[[0,1,0]])
        b['pre']=[[0,1,2]]
        with self.assertRaises(ValueError):compose(a,b)
    def test_new_input_constraints_and_frame(self):
        a=dict(q='a',out='b',shift=2,steps=2,extent=[0,2],pre=[[0,1,3]],writes=[])
        b=dict(q='b',out='c',shift=-1,steps=1,extent=[-1,0],pre=[[-1,0,2]],writes=[[-1,0,0]])
        c=compose(a,b);self.assertEqual(c['pre'],[[0,1,3],[1,2,2]]);self.assertEqual(c['extent'],[0,2]);self.assertEqual(c['shift'],1)
    def test_associativity_of_valid_interfaces(self):
        proof=self.prove((('pushR1',1),('accept',)),capacities=(0,1));_,sweeps=machine_data(self.d);values=[leaf(self.d,proof['nodes'][i],sweeps) for i in proof['tokens'][:3]]
        self.assertEqual(compose(compose(values[0],values[1]),values[2]),compose(values[0],compose(values[1],values[2])))
    def test_translation_and_headless_frame(self):
        row=self.m.initial((('accept',),),capacities=(0,0));proof=certify(self.d,row);larger=('B','B')+row+('0','1','B');other=certify(self.d,larger)
        self.assertEqual(proof['steps'],other['steps']);self.assertEqual(proof['nodes'],other['nodes']);self.assertEqual(other['final'][-3:],['0','1','B']);check(self.d,other);validate(self.d,other,other['problem_sha256'])
    def test_every_concretization_of_a_copy_schema(self):
        d=dict(alphabet=['B','0','1'],states=['q','halt'],halt='halt',transitions=[['q','B','q','B',1],['q','0','q','0',1],['q','1','halt','0',0]])
        roots=[]
        for a,b in itertools.product(('B','0'),repeat=2):
            row=('B',wang.head('q',a),b,'1','B');proof=certify(d,row)
            self.assertEqual(proof['steps'],3);self.assertEqual(check(d,proof)['result'],'accept');validate(d,proof,proof['problem_sha256']);self.assertEqual(dense(d,proof),15)
            roots.append(proof['observations'][0]['interface'])
        self.assertTrue(all(r==roots[0] for r in roots))
    def test_machine_binding_and_nonsweep(self):
        proof=self.prove((('accept',),),capacities=(0,0));d=copy.deepcopy(self.d);d['transitions']=list(d['transitions']);d['transitions'][0]=tuple(d['transitions'][0]);d['transitions'][0]=(*d['transitions'][0][:4],0)
        with self.assertRaises(ValueError):check(d,proof)
        _,sweeps=machine_data(self.d)
        with self.assertRaises(ValueError):leaf(self.d,{'sweep':['accept',1,100]},sweeps)

if __name__=='__main__':unittest.main()
