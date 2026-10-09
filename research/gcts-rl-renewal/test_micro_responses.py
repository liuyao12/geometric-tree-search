import copy,json,random,struct,subprocess,tempfile,unittest
from pathlib import Path
from micro_cert import compile_tools,run,write_cuts,write_grammar,leaf,compose
from tape_tree_machine import RAW,physical_declaration
from tape_binary import write_micro,write_micro_input,write_machine,write_input,read_micro_output,read_output

HERE=Path(__file__).resolve().parent
class MicroResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='gcts-response-test-',dir='/private/tmp');cls.path=Path(cls.tmp.name);compile_tools(cls.path)
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'tape_runner.cpp'),'-o',str(cls.path/'literal')],check=True)
        write_cuts([],cls.path/'cuts')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def micro(self,rows):return dict(rows=[None,None,None]+rows,start=3,accept=0,reject=1,space=2,tapes=2,names=['state']*(len(rows)+3))
    def initial(self,a='0',b='1',h=4):return dict(words=['B'*(h-1)+a,'B'*(h-1)+b],heads=[h,h],capacities=[16,16])
    def execute(self,m,initial):
        write_micro(m,self.path/'code');write_micro_input(initial,self.path/'input')
        built=run(self.path/'builder',[self.path/'code',self.path/'input',self.path/'grammar',self.path/'output',10**6,100000,self.path/'cuts'])
        checked=run(self.path/'checker',[self.path/'code',self.path/'input',self.path/'grammar',self.path/'derived',10**6,1000000,self.path/'root'])
        self.assertEqual(checked['status'],'checked_response');self.assertEqual(checked['result'],built['status']);self.assertEqual((self.path/'derived').read_bytes(),(self.path/'output').read_bytes())
        literal=physical_declaration(m);write_machine(literal,m,self.path/'literal-code');write_input(literal,initial,self.path/'literal-input')
        native=run(self.path/'literal',[self.path/'literal-code',self.path/'literal-input',self.path/'literal-output',10**9])
        self.assertEqual(native['physical_steps'],checked['physical_steps']);self.assertEqual(native['micro_steps'],checked['micro_steps'])
        physical=read_output(literal,initial,self.path/'literal-output');symbol=read_micro_output(self.path/'derived')
        for k in ('heads','words'):self.assertEqual(physical[k],symbol[k])
        return built,checked,json.loads((self.path/'root').read_text())
    def test_all_symbol_actions_match_literal_transitions(self):
        for a in RAW:
            for w in RAW:
                for d in (-1,0,1):
                    with self.subTest(read=a,write=w,move=d):self.execute(self.micro([[0,{a:[0,w,d]}]]),self.initial(a))
    def test_right_copy_sweep_has_exact_quadratic_physical_count(self):
        m=self.micro([[0,{'0':[3,'0',1],'1':[3,'1',1],'B':[0,'B',0]}]])
        initial=dict(words=['00101001',''],heads=[1,1],capacities=[16,16]);self.execute(m,initial)
    def test_left_copy_sweep_has_exact_quadratic_physical_count(self):
        m=self.micro([[0,{'0':[3,'0',-1],'1':[3,'1',-1],'^':[0,'^',0]}]])
        initial=dict(words=['00101001',''],heads=[8,1],capacities=[16,16]);self.execute(m,initial)
    def test_mixed_tapes_and_head_shifts_compose_correctly(self):
        random.seed(26)
        for _ in range(30):
            rows=[]
            for i in range(5):rows.append([random.randrange(2),{s:[0 if i==4 else i+4,random.choice(RAW),random.choice((-1,0,1))] for s in RAW}])
            self.execute(self.micro(rows),self.initial(h=7))
    def test_writes_are_checked_against_later_reads(self):
        m=self.micro([[0,{'0':[4,'1',0]}],[0,{'1':[0,'0',0]}]])
        self.execute(m,self.initial());a=leaf(m,[0,3,2,0]);b=leaf(m,[0,4,3,0]);r=compose(a,b)
        self.assertEqual(r['bands'][0]['writes'],[]);self.assertEqual(r['bands'][0]['pre'],[[0,1,4]])
        bad=copy.deepcopy(b);bad['bands'][0]['pre']=[[0,1,4]]
        with self.assertRaises(ValueError):compose(a,bad)
    def test_partial_symbol_masks_intersect_without_becoming_values(self):
        m=self.micro([[0,{'0':[3,'0',1],'1':[3,'1',1]}]])
        a=leaf(m,[1,3,2,3]);self.assertEqual(a['bands'][0]['pre'],[[0,3,12]])
    def test_python_affine_algebra_agrees_with_executable(self):
        m=self.micro([[0,{'0':[4,'1',1]}],[1,{'1':[0,'0',-1]}]]);_,checked,root=self.execute(m,self.initial())
        r=compose(leaf(m,[0,3,2,0]),leaf(m,[0,4,3,0]))
        self.assertEqual(str(r['constant']),root['physical_constant'])
        self.assertEqual(r['steps'],root['steps'])
        for b in root['bands']:
            expected=r['bands'][b['tape']]
            for key in ('shift','pre','writes','extent'):self.assertEqual(expected[key],b[key])
            self.assertEqual(expected['coefficient'],b['physical_coefficient'])
    def malformed(self,mutate):
        m=self.micro([[0,{'0':[4,'1',0]}],[0,{'1':[0,'0',0]}]]);self.execute(m,self.initial());raw=bytearray((self.path/'grammar').read_bytes());mutate(raw);(self.path/'bad').write_bytes(raw)
        r=subprocess.run([str(self.path/'checker'),str(self.path/'code'),str(self.path/'input'),str(self.path/'bad'),str(self.path/'badout'),'1000000','1000000',str(self.path/'badroot')],stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.assertNotEqual(r.returncode,0)
    def test_cycles_and_changed_states_reject(self):
        for offset,value in ((8,0xffffffff),(12,0),(48,0xffffffff)):
            self.malformed(lambda raw:struct.pack_into('<I',raw,offset,value))
        def cycle(raw):
            n=struct.unpack_from('<I',raw,4)[0];struct.pack_into('<I',raw,44+16*(n-1)+4,n-1)
        self.malformed(cycle)
    def test_changed_length_and_physical_boundary_reject(self):
        for offset in (20,28,36):self.malformed(lambda raw:struct.pack_into('<Q',raw,offset,99999))
    def test_unused_invalid_node_is_checked(self):
        def mutate(raw):
            n=struct.unpack_from('<I',raw,4)[0];struct.pack_into('<I',raw,4,n+1);raw.extend(struct.pack('<4I',0,0xffffffff,0,0))
        self.malformed(mutate)
    def test_supplied_interface_cannot_replace_derived_interface(self):
        self.malformed(lambda raw:raw.extend(b'forged interface'))
    def test_frame_and_input_preconditions_are_enforced(self):
        m=self.micro([[0,{'0':[0,'1',0]}]]);self.execute(m,self.initial());initial=self.initial('1');write_micro_input(initial,self.path/'input')
        r=subprocess.run([str(self.path/'checker'),str(self.path/'code'),str(self.path/'input'),str(self.path/'grammar'),str(self.path/'badout'),'1000000','1000000',str(self.path/'badroot')],stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.assertNotEqual(r.returncode,0)
        m=self.micro([[0,{'0':[3,'0',1],'1':[3,'1',1],'B':[0,'B',0]}]])
        initial=dict(words=['00101001',''],heads=[1,1],capacities=[16,16]);self.execute(m,initial);initial['heads'][0]=15;write_micro_input(initial,self.path/'input')
        r=subprocess.run([str(self.path/'checker'),str(self.path/'code'),str(self.path/'input'),str(self.path/'grammar'),str(self.path/'badout'),'1000000','1000000',str(self.path/'badroot')],stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.assertNotEqual(r.returncode,0)
    def test_expansion_and_interface_budgets_remain_unknown(self):
        m=self.micro([[0,{'0':[0,'1',0]}]]);self.execute(m,self.initial())
        for symbols,work in ((0,1000),(1000,0)):
            r=run(self.path/'checker',[self.path/'code',self.path/'input',self.path/'grammar',self.path/'limited',symbols,work,self.path/'limited-root']);self.assertEqual(r['status'],'unknown_certificate_budget')
    def test_published_whole_induction_response(self):
        d=json.loads((HERE.parents[1]/'docs/research/gcts-rl-renewal/micro-responses-001.json').read_text());r=d['cases'][0]
        self.assertEqual(r['name'],'addition-induction');self.assertEqual(r['checker']['result'],'accepted');self.assertEqual(r['checker']['physical_steps'],r['prior_literal']['physical_steps'])
        self.assertEqual(r['checker']['micro_steps'],r['prior_selected']['micro_steps']);self.assertEqual(len(d['independent_audit']['cases']),3)

if __name__=='__main__':unittest.main()
