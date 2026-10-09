import copy,json,unittest
from pathlib import Path
from tree_machine import Compiler,Heap,Resource,encode_json,run,validate,fingerprint
from tree_kernel import program,check,canonical,problem_hash
from tree_examples import extra_cases
from serialized_examples import primitive_cases,addition_induction
from serialized_kernel import check as reference
from audit_tree_kernel import replay,decode_input,audit_row,PINNED_PROGRAM_SHA256,mutation_checks

class TreeKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.code=program();cls.examples=dict(extra_cases());cls.small=dict(primitive_cases())['reflexivity']
    def execute(self,source,value=None,steps=10000):
        p=Compiler(source).declaration();validate(p);h=Heap(p['nodes']);root=encode_json(h,value)
        initial=dict(node=root,nodes=list(h.nodes));r=run(p,h,root,steps)
        self.assertEqual({k:v for k,v in r.items() if k!='seconds'},replay(p,initial,steps,None))
        return r
    def test_explicit_call_frames_and_recursion(self):
        source='def main(x):\n    return scan(tail(x))\ndef scan(x):\n    if atom_eq(x, None):\n        return True\n    return scan(tail(x))\n'
        r=self.execute(source,list(range(24)));self.assertEqual(r['status'],'accepted');self.assertEqual(r['peak_frames'],25)
    def test_short_circuit_avoids_invalid_data_operation(self):
        for expression in ('False and head(None)','True or head(None)'):
            r=self.execute('def main(x):\n    return '+expression+'\n');self.assertEqual(r['value'],int(expression.startswith('True')))
    def test_loop_break_and_conditional_jump(self):
        r=self.execute('def main(x):\n    n = 0\n    while True:\n        n = byte_succ(n)\n        if atom_eq(n, 7):\n            break\n    return atom_eq(n, 7)\n')
        self.assertEqual(r['status'],'accepted')
    def test_atom_domain_and_partial_operations(self):
        self.assertEqual(self.execute('def main(x):\n    a = cons(0, None)\n    return atom_eq(a, a)\n')['status'],'rejected')
        for expr in ('head(None)','byte_succ(255)','not None'):
            self.assertIn('invalid data operation',self.execute('def main(x):\n    return '+expr+'\n')['reason'])
    def test_static_code_cannot_call_host_logic_or_compile_data(self):
        for source in ('import logic\ndef main(x):\n    return True\n','def main(x):\n    return eval(x)\n','def main(x):\n    return x.foo()\n'):
            with self.assertRaises((ValueError,KeyError)):Compiler(source)
        bad=copy.deepcopy(self.code);bad['functions'][0]['code'][0]=['call',0,0,[]]
        with self.assertRaises(ValueError):validate(bad)
    def test_heap_is_acyclic_exact_and_canonical(self):
        for nodes in ([(257,256)],[(True,256)],[(0,256),(0,256)],[(0,-1)]):
            with self.assertRaises(ValueError):Heap(nodes)
        h=Heap(limit=1);self.assertEqual(h.cons(0,256),h.cons(0,256))
        with self.assertRaises(Resource):h.cons(1,256)
    def test_adapter_round_trip_is_syntax_only_and_bool_is_distinct(self):
        raw={'values':[0,False,-2,None,'\u0000\u03b1\ud800'], 'deep':[[[[]]]]}
        h=Heap();root=encode_json(h,raw);self.assertEqual(canonical(decode_input(h.nodes,root)),canonical(raw))
        self.assertNotEqual(encode_json(h,False),encode_json(h,0))
    def test_capture_freshness_across_decimal_digit_boundary_and_shadowing(self):
        for name in ('capture-fresh12','shadowed-binder'):
            payload=canonical(self.examples[name]);r=check(payload,self.code);self.assertEqual(r['status'],'accepted');self.assertEqual(reference(payload,max_work=None)['status'],r['status'])
    def test_unicode_free_variable_order_with_surrogates(self):
        payload=canonical(self.examples['unicode-induction-order']);self.assertEqual(check(payload,self.code)['status'],'accepted')
    def test_eigenvariable_and_unused_block_failures(self):
        for name in ('free-distribution-antecedent','unused-invalid-block','negative-signature','boolean-term-name'):
            payload=canonical(self.examples[name]);self.assertEqual(check(payload,self.code)['status'],'rejected')
    def test_external_problem_and_program_pins_cannot_be_replaced_by_request(self):
        payload=canonical(self.small)
        self.assertEqual(check(payload,self.code,expected_problem_sha256='0'*64)['status'],'rejected')
        bad=copy.deepcopy(self.code);bad['functions'][0]['code'][0]=['return',0]
        self.assertEqual(check(payload,bad,expected_program_sha256=PINNED_PROGRAM_SHA256)['status'],'rejected')
        self.assertEqual(fingerprint(self.code),PINNED_PROGRAM_SHA256)
    def test_resource_exhaustion_is_unknown_including_mid_program_heap(self):
        payload=canonical(self.small);full=check(payload,self.code,keep_input=True)
        for steps in (0,20):
            r=check(payload,self.code,steps=steps,keep_input=True);self.assertEqual(r['status'],'unknown_step_budget')
            row=dict(payload_hex=payload.hex(),problem_pin=problem_hash(self.small),check=r,step_limit=steps,heap_limit=2000000);audit_row(self.code,row)
        r=check(payload,self.code,heap_limit=len(full['initial']['nodes']),keep_input=True);self.assertEqual(r['status'],'unknown_heap_budget')
        row=dict(payload_hex=payload.hex(),problem_pin=problem_hash(self.small),check=r,step_limit=20000000,heap_limit=len(full['initial']['nodes']));audit_row(self.code,row)
    def test_strict_json_and_pre_vm_budgets(self):
        for payload in (b'{"x":1,"x":2}',b'{"x":0.0}',b'{"x":NaN}',b'\xff'):
            self.assertEqual(check(payload,self.code)['status'],'rejected')
        payload=canonical(self.small)
        for kw in (dict(max_bytes=0),dict(heap_limit=0)):
            self.assertEqual(check(payload,self.code,**kw)['status'],'unknown_resource_budget')
    def test_published_replay_bindings_catch_forged_success(self):
        path=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal/tree-kernel-001.json'
        data=json.loads(path.read_text());self.assertEqual(len(mutation_checks(data)),15)

if __name__=='__main__':unittest.main()
