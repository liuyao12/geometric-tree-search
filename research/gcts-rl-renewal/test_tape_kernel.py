import copy,json,struct,subprocess,tempfile,unittest
from pathlib import Path
from tree_machine import Compiler,Heap,encode_json,run
from tape_tree_machine import Lowering,physical_declaration,virtual_run
from tape_binary import write_machine,write_input,read_output
from audit_tape_kernel import check_table

HERE=Path(__file__).resolve().parent
class TapeKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='gcts-tape-test-',dir='/private/tmp');cls.path=Path(cls.temp.name)
        cls.exe=cls.path/'runner'
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'tape_runner.cpp'),'-o',str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def execute(self,source,value=None,word_capacity=64,heap_padding=1024,stack_capacity=4096):
        p=Compiler(source).declaration();h=Heap(p['nodes']);root=encode_json(h,value);initial={'node':root,'nodes':list(h.nodes)}
        expected=run(p,h,root);lower=Lowering(p);d=lower.declaration();literal=physical_declaration(d)
        bound=lower.initial(initial,word_capacity,heap_padding,stack_capacity)
        write_machine(literal,d,self.path/'code');write_input(literal,bound,self.path/'input')
        native=json.loads(subprocess.check_output([str(self.exe),str(self.path/'code'),str(self.path/'input'),str(self.path/'output'),str(10**12)]))
        independent=virtual_run(d,bound,limit=1000000)
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):self.assertEqual(native[k],independent[k],k)
        end=read_output(literal,bound,self.path/'output')
        for k in ('words','heads'):self.assertEqual(end[k],independent[k],k)
        if native['status'] in ('accepted','rejected'):
            self.assertEqual(native['status'],expected['status'])
            records=end['words'][d['heap']].split(';')[:-1]
            actual=[]
            for i,record in enumerate(records):
                label,children=record.split(':');a,b=children.split(',')
                self.assertEqual(int(label[::-1],2),257+i);actual.append((int(a[::-1],2),int(b[::-1],2)))
            self.assertEqual(actual,h.nodes)
        return native,independent,d,literal
    def test_recursive_frames_and_live_caller_values(self):
        source='def main(x):\n    a = 7\n    z = scan(tail(x))\n    return atom_eq(a,7) and z\ndef scan(a):\n    if atom_eq(a,None):\n        return True\n    return scan(tail(a))\n'
        r,*_=self.execute(source,[1,2,3,4]);self.assertEqual(r['status'],'accepted')
    def test_permuted_and_duplicate_arguments(self):
        source='def main(x):\n    return same(7,8,7)\ndef same(a,b,c):\n    return atom_eq(a,c) and not atom_eq(a,b)\n'
        self.assertEqual(self.execute(source)[0]['status'],'accepted')
    def test_loop_back_edge_preserves_colored_registers(self):
        source='def main(x):\n    n = 0\n    a = 7\n    while not atom_eq(n,9):\n        n = byte_succ(n)\n    return atom_eq(a,7) and atom_eq(n,9)\n'
        self.assertEqual(self.execute(source)[0]['status'],'accepted')
    def test_entry_live_uninitialized_local_is_nil(self):
        self.assertEqual(self.execute('def main(x):\n    if False:\n        a = 7\n    return atom_eq(a,None)\n')[0]['status'],'accepted')
    def test_aliasing_move_and_same_register_atom_test(self):
        self.assertEqual(self.execute('def main(x):\n    a = 12\n    b = a\n    return atom_eq(b,b)\n')[0]['status'],'accepted')
    def test_nine_bit_atom_boundary_and_pair_ids(self):
        source='def main(x):\n    a = cons(255,None)\n    return is_pair(a) and not is_pair(None) and atom_eq(head(a),255) and atom_eq(tail(a),None)\n'
        self.assertEqual(self.execute(source)[0]['status'],'accepted')
    def test_canonical_allocation_reuses_equal_cons_cells(self):
        source='def main(x):\n    a = cons(7,None)\n    b = cons(7,None)\n    return atom_eq(head(a),head(b))\n'
        self.assertEqual(self.execute(source)[0]['status'],'accepted')
    def test_partial_operations_reject_without_host_callbacks(self):
        for expression in ('head(None)','byte_succ(255)','not None'):
            self.assertEqual(self.execute('def main(x):\n    return '+expression+'\n')[0]['status'],'rejected')
    def test_root_only_atom_one_accepts(self):
        for expr in ('None','0','7','cons(0,None)'):
            self.assertEqual(self.execute('def main(x):\n    return '+expr+'\n')[0]['status'],'rejected')
    def test_short_circuit_avoids_illegal_second_operand(self):
        self.assertEqual(self.execute('def main(x):\n    return True or head(None)\n')[0]['status'],'accepted')
    def test_space_exhaustion_is_unknown_and_preserves_declared_bound(self):
        source='def main(x):\n    a = cons(7,None)\n    b = cons(8,a)\n    return True\n'
        self.assertEqual(self.execute(source,heap_padding=2)[0]['status'],'unknown_space_budget')
    def test_every_finite_selection_transition_obeys_the_law(self):
        _,_,d,_=self.execute('def main(x):\n    return True\n')
        binary=(self.path/'code').read_bytes();self.assertGreater(check_table(d,binary)['expanded_defined_transitions'],0)
        bad=bytearray(binary);struct.pack_into('<I',bad,0,0)
        with self.assertRaises(ValueError):check_table(d,bad)
        bad=bytearray(binary);bad[-4:]=struct.pack('<I',999999)
        with self.assertRaises(ValueError):check_table(d,bad)
    def test_live_register_collision_is_detected(self):
        from audit_tape_kernel import check_allocation
        p=Compiler('def main(x):\n    a = 7\n    b = 8\n    return atom_eq(a,b)\n').declaration();d=Lowering(p).declaration()
        self.assertGreater(check_allocation(p,d),0)
        bad=copy.deepcopy(d);bad['allocation'][0]['slots']=[0]*p['functions'][0]['registers']
        with self.assertRaises(ValueError):check_allocation(p,bad)
    def test_published_full_induction_case_is_literal_and_independently_replayed(self):
        d=json.loads((HERE.parents[1]/'docs/research/gcts-rl-renewal/tape-kernel-001.json').read_text())
        r=next(r for r in d['cases'] if r['name']=='addition-induction')
        self.assertEqual(r['native']['status'],'accepted');self.assertEqual(r['native']['physical_steps'],r['independent']['physical_steps'])
        self.assertEqual(d['space_control']['native']['status'],'unknown_space_budget')
        self.assertEqual(d['independent_audit']['cases'],len(d['cases']))
if __name__=='__main__':unittest.main()
