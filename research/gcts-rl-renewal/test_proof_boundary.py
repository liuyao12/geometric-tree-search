import copy,json,subprocess,tempfile,unittest
from pathlib import Path
from tree_machine import Compiler,Heap,encode_json,run
from proof_boundary import BoundaryLowering,boundary_program,boundary_words,value_word,tree_word
from tape_binary import write_micro,write_micro_input
from audit_proof_boundary import wire_parse,expected_constructor,micro_output,heap_records
from serialized_examples import primitive_cases

HERE=Path(__file__).resolve().parent
class ProofBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='gcts-boundary-test-',dir='/private/tmp');cls.path=Path(cls.temp.name)
        cls.exe=cls.path/'runner';subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_boundary_micro.cpp'),'-o',str(cls.exe)],check=True)
        cls.p=Compiler('def main(x):\n    return True\n').declaration();cls.lower=BoundaryLowering(cls.p);cls.micro=cls.lower.declaration()
        write_micro(cls.micro,cls.path/'code');cls.syntax=boundary_program()
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def execute(self,request,free=None,padding=8192,limit=10**9,stop=False):
        fixed,wire=boundary_words(request);initial=self.lower.initial_boundary(fixed,wire if free is None else free,heap_padding=padding)
        write_micro_input(initial,self.path/'input');r=json.loads(subprocess.check_output([str(self.exe),str(self.path/'code'),str(self.path/'input'),str(self.path/'output'),str(limit),str(self.lower.old_start if stop else len(self.micro['rows']))]))
        return r,micro_output(self.path/'output'),initial
    def request(self,proof=None):return dict(protocol='gcts-fol-1',theory={},target=None,blocks=[],proof=proof if proof is not None else [])
    def test_unknown_certificate_builds_exact_heap_and_bound_request(self):
        request=self.request([{'nested':[0,False,-2,None,'\u0000\u03b1\ud800']}]);r,out,initial=self.execute(request,stop=True)
        self.assertEqual(r['status'],'stopped_state');expected,root=expected_constructor(self.micro,initial,request)
        self.assertEqual(heap_records(out['words'][self.micro['heap']]),expected)
        self.assertEqual(int(out['words'][self.micro['allocation'][0]['slots'][0]][::-1],2),root)
    def test_all_finite_atoms_and_nil_have_canonical_wire_meaning(self):
        for n in range(257):self.assertEqual(wire_parse('0'+format(n,'b')[::-1].ljust(9,'0')+';',[]),[n])
        for n in (257,511):
            with self.assertRaises(ValueError):wire_parse('0'+format(n,'b')[::-1].ljust(9,'0')+';',[])
    def test_cons_not_a_user_supplied_pointer(self):
        for wire in ('1;','01000000001;','0111111111;','000;'):
            self.assertEqual(self.execute(self.request(),free=wire)[0]['status'],'rejected')
    def test_exactly_two_free_trees_required(self):
        for n in (0,1,3):self.assertEqual(self.execute(self.request(),free=value_word([])*n+';')[0]['status'],'rejected')
    def test_free_cons_cannot_consume_fixed_assertion_stack(self):
        self.assertEqual(self.execute(self.request(),free='1'+value_word([])*3+';',stop=True)[0]['status'],'rejected')
    def test_padding_is_allowed_only_after_terminator(self):
        _,wire=boundary_words(self.request());self.assertEqual(self.execute(self.request(),free=wire+'BBBB')[0]['status'],'accepted')
        for bad in ('B'+wire,';'+wire,wire+'0',wire[:-1]):self.assertEqual(self.execute(self.request(),free=bad)[0]['status'],'rejected')
    def test_shared_subtrees_are_constructed_once(self):
        request=self.request([['same']]*6);r,out,initial=self.execute(request,stop=True)
        expected,_=expected_constructor(self.micro,initial,request);self.assertEqual(heap_records(out['words'][self.micro['heap']]),expected)
        self.assertEqual(len(expected),len({tuple(x) for x in expected}))
    def test_fixed_problem_does_not_contain_certificate_nodes(self):
        a=boundary_words(self.request([1]));b=boundary_words(self.request([2,3]));self.assertEqual(a[0],b[0]);self.assertNotEqual(a[1],b[1])
    def test_resource_exhaustion_during_constructor_is_unknown(self):
        self.assertEqual(self.execute(self.request(),padding=2)[0]['status'],'unknown_space_budget')
        for limit in (0,1,100):self.assertEqual(self.execute(self.request(),limit=limit)[0]['status'],'unknown_step_budget')
    def syntax_value(self,expression):
        # Isolate the actual wrapper's grammar gate; bypass proof semantics in
        # this fixture so an unrelated wrong proof cannot mask syntax failure.
        source=(HERE/'boundary_syntax.tree').read_text().replace('wire_value(request) and semantic_main(request)','wire_value(request)')
        source+=(HERE/'fol_checker.tree').read_text().replace('def main(request):','def semantic_main(request):',1)
        p=Compiler(source).declaration();h=Heap(p['nodes'])
        def build(x):return h.cons(build(x[0]),build(x[1])) if type(x) is tuple else x
        return run(p,h,build(expression))['status']
    def test_syntax_gate_rejects_duplicate_keys(self):
        word=(97,256);row=(word,(6,256));obj=(0,(row,(row,256)))
        self.assertEqual(self.syntax_value(obj),'rejected')
    def test_syntax_gate_rejects_improper_arrays_and_words(self):
        for expr in ((1,7),(2,(256,256)),(2,(257,256))):
            self.assertEqual(self.syntax_value(expr),'rejected')
    def test_syntax_gate_preserves_integer_boolean_null_distinctions(self):
        for expr in ((3,256),(4,(1,256)),(5,1),(6,256)):self.assertEqual(self.syntax_value(expr),'accepted')
        for expr in ((4,256),(3,(2,256)),(5,2),(6,0),(7,256)):self.assertEqual(self.syntax_value(expr),'rejected')
    def test_syntax_names_are_byte_strings(self):
        self.assertEqual(self.syntax_value((2,(255,256))),'accepted')
    def test_full_semantic_wrapper_keeps_capture_and_eigenvariable_rules(self):
        from serialized_examples import adversarial_cases
        cases=primitive_cases()[:8]+[(n,r) for n,r in adversarial_cases() if n in ('captured-instantiation','generalization-of-open-premise')]
        for name,request in cases:
            request=json.loads(json.dumps(request));h=Heap(self.syntax['nodes']);node=encode_json(h,request)
            self.assertEqual(run(self.syntax,h,node)['status'],'rejected' if name in ('captured-instantiation','generalization-of-open-premise') else 'accepted')
    def test_fixed_target_cannot_be_replaced_by_free_proof(self):
        request=self.request([{'target':'rogue'}]);r,out,initial=self.execute(request,stop=True)
        changed=dict(request,target='rogue')
        with self.assertRaises(ValueError):expected_constructor(self.micro,initial,changed)
    def test_external_certificate_binding_distinguishes_bool_from_integer(self):
        request=self.request([False]);r,out,initial=self.execute(request,stop=True)
        with self.assertRaises(ValueError):expected_constructor(self.micro,initial,dict(request,proof=[0]))
    def test_published_induction_has_no_free_input_heap(self):
        data=json.loads((HERE.parents[1]/'docs/research/gcts-rl-renewal/proof-boundary-001.json').read_text());r=next(r for r in data['cases'] if r['name']=='addition-induction')
        self.assertEqual(r['native']['status'],'accepted');self.assertEqual(r['native']['micro_steps'],r['selected']['micro_steps'])
        self.assertEqual(data['independent_audit']['cases'],len(data['cases']))

if __name__=='__main__':unittest.main()
