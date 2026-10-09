"""Native execution agrees with two distinct small-step implementations."""
import hashlib,json,struct,subprocess,tempfile,unittest
from pathlib import Path
from tree_machine import Compiler,Heap,encode_json,run
from audit_tree_kernel import replay
import tree_native

class NativeTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='gcts-native-test-')
        cls.directory=Path(cls.tmp.name);tree_native.compile_tool(cls.directory)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def compare(self,source,value=None,steps=10000,limit=10000):
        code=Compiler(source).declaration();heap=Heap(code['nodes'],limit=limit);root=encode_json(heap,value)
        initial=dict(node=root,nodes=list(heap.nodes));reference=run(code,heap,root,steps)
        independent=replay(code,initial,steps,limit)
        self.assertEqual({k:v for k,v in reference.items() if k!='seconds'},independent)
        d=self.directory;(d/'code').write_bytes(tree_native.code_bytes(code));raw=tree_native.input_bytes(code,value)
        (d/'input').write_bytes(raw)
        native=json.loads(subprocess.check_output([str(d/'tree'),str(d/'code'),str(d/'input'),str(d/'output'),str(steps),str(limit),str(d/'profile')]))
        profile=json.loads((d/'profile').read_text());native['profile']={f['name']:n for f,n in zip(code['functions'],profile) if n}
        for key in ('status','steps','event_sha256','peak_frames','heap_nodes','profile'):
            self.assertEqual(native[key],reference[key],key)
        if 'value' in reference:self.assertEqual(native['value'],reference['value'])
        values=struct.unpack('<'+'I'*((d/'output').stat().st_size//4),(d/'output').read_bytes())
        self.assertEqual(values[0],0x47544f31);self.assertEqual(values[2],len(heap.nodes))
        self.assertEqual(list(zip(values[3::2],values[4::2])),heap.nodes)
        return reference
    def test_every_opcode_calls_loops_and_canonical_pairs(self):
        source='''def main(x):
    n = 0
    while not atom_eq(n, 7):
        n = byte_succ(n)
    a = cons(n, None)
    b = cons(n, None)
    if is_pair(a):
        return same(head(b), tail(a))
    return False
def same(a, b):
    return atom_eq(a, 7) and atom_eq(b, None)
'''
        r=self.compare(source);self.assertEqual(r['status'],'accepted')
        seen={e[2] for e in r['trace']};self.assertTrue({'jump','branch','move','succ','not'}<=seen)
    def test_recursive_frames_and_structured_input(self):
        r=self.compare('def main(x):\n    return scan(tail(x))\ndef scan(x):\n    if atom_eq(x, None):\n        return True\n    return scan(tail(x))\n',list(range(24)))
        self.assertEqual(r['peak_frames'],25)
    def test_nonboolean_root_is_rejection(self):
        self.assertEqual(self.compare('def main(x):\n    return 2\n')['status'],'rejected')
    def test_partial_operations_leave_failed_event_unhashed(self):
        for expr in ('head(None)','tail(0)','byte_succ(255)','not None'):
            self.assertEqual(self.compare('def main(x):\n    return '+expr+'\n')['status'],'rejected')
        self.assertEqual(self.compare('def main(x):\n    if x:\n        return True\n    return False\n')['status'],'rejected')
    def test_short_circuit_and_cons_atoms_are_distinct(self):
        for expr in ('False and head(None)','True or head(None)','atom_eq(cons(0, None), cons(0, None))'):
            self.compare('def main(x):\n    return '+expr+'\n')
    def test_step_limits_are_unknown_with_exact_prefixes(self):
        for steps in (0,1,7,31):
            self.assertEqual(self.compare('def main(x):\n    while True:\n        x = x\n',steps=steps)['status'],'unknown_step_budget')
    def test_mid_execution_heap_cutoff_is_unknown(self):
        self.assertEqual(self.compare('def main(x):\n    return is_pair(cons(7, None))\n',limit=1)['status'],'unknown_heap_budget')
    def test_deep_text_integer_boolean_input_transport(self):
        self.compare('def main(x):\n    return is_pair(x)\n',{'values':[0,False,-2,None,'\u0000\u03b1\ud800'],'deep':[[[[]]]]})
    def test_input_heap_limit_and_external_pin_cannot_be_bypassed(self):
        from tree_kernel import program,canonical,problem_hash
        from serialized_examples import primitive_cases
        request=dict(primitive_cases())['reflexivity'];code=program();pin=problem_hash(request)
        r=tree_native.check(canonical(request),code,self.directory,pin,heap_limit=0)
        self.assertEqual(r['status'],'unknown_resource_budget')
        with self.assertRaises(ValueError):tree_native.check(canonical(request),code,self.directory,'0'*64)
    def test_static_grammar_and_malformed_binary_are_rejected(self):
        code=Compiler('def main(x):\n    return True\n').declaration();code['functions'][0]['code'][0]=['call',0,0,[]]
        with self.assertRaises(ValueError):tree_native.code_bytes(code)
        d=self.directory;(d/'bad').write_bytes(b'bad')
        r=subprocess.run([str(d/'tree'),str(d/'bad'),str(d/'bad'),str(d/'out'), '100','100',str(d/'prof')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertNotEqual(r.returncode,0)

if __name__=='__main__':unittest.main()
