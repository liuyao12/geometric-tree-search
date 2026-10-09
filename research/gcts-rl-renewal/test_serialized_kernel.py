import copy
import json
import unittest
import logic
from serialized_kernel import check,canonical,problem_hash
from serialized_examples import (addition_induction,primitive_cases,propositional_cases,
                                 adversarial_cases,flatten_blocks,request,line,induction_formula)
from audit_serialized_kernel import replay

class SerializedKernelTests(unittest.TestCase):
    def test_proposer_cannot_change_the_externally_pinned_problem(self):
        original=addition_induction(); pin=problem_hash(original)
        flat=flatten_blocks(original)
        self.assertEqual(problem_hash(flat),pin)
        self.assertEqual(check(canonical(flat),expected_problem_sha256=pin)['status'],'accepted')
        forged=copy.deepcopy(original); forged['theory']['axioms']['invented']=forged['target']
        forged.update(blocks=[],proof=[line('axiom',forged['target'],name='invented')])
        self.assertEqual(check(canonical(forged))['status'],'accepted')
        self.assertEqual(check(canonical(forged),expected_problem_sha256=pin)['status'],'rejected')
        self.assertEqual(replay(canonical(forged),pin)['status'],'rejected')
    def test_all_old_rules_and_large_input_syntax(self):
        for name,d in primitive_cases():
            with self.subTest(name=name):
                self.assertEqual(check(canonical(d))['status'],'accepted')
                self.assertEqual(replay(canonical(d))['status'],'accepted')

    def test_induction_proves_left_zero_without_enumerated_formulas(self):
        d=addition_induction(); result=check(canonical(d)); oracle=replay(canonical(d))
        self.assertEqual(result['status'],'accepted'); self.assertEqual(result['blocks_checked'],3)
        self.assertEqual(oracle['status'],'accepted'); self.assertEqual(oracle['expanded_lines'],18)
        self.assertEqual(d['target'],logic.All('x',logic.Eq(logic.F('add',logic.F('zero'),logic.V('x')),logic.V('x'))))

    def test_complete_propositional_grammar_through_five_nodes(self):
        examples=propositional_cases(); self.assertEqual(len(examples),771)
        for d in examples:
            expected='accepted' if logic.tautology(d['target']) else 'rejected'
            self.assertEqual(check(canonical(d))['status'],expected)

    def test_hierarchical_and_flat_derive_identical_statement(self):
        for n in (1,8,32):
            d=addition_induction(n); flat=flatten_blocks(d)
            self.assertEqual(flat['theory'],d['theory']); self.assertEqual(flat['target'],d['target'])
            self.assertEqual(check(canonical(flat))['status'],'accepted')
            a=replay(canonical(d)); b=replay(canonical(flat))
            self.assertEqual(a['proof'],b['proof']); self.assertEqual(a['expanded_lines'],4+14*n)

    def test_adversarial_interfaces_rules_and_capture(self):
        for name,d in adversarial_cases():
            with self.subTest(name=name):
                self.assertEqual(check(canonical(d))['status'],'rejected')
                self.assertEqual(replay(canonical(d))['status'],'rejected')

    def test_duplicate_fields_floats_and_nonfinite_json(self):
        payload=canonical(addition_induction())
        probes=[payload.replace(b'"protocol":',b'"protocol":"gcts-fol-1","protocol":',1),
                payload.replace(b'"zero":0',b'"zero":0.0',1),
                payload.replace(b'"zero":0',b'"zero":NaN',1)]
        for p in probes:
            self.assertEqual(check(p)['status'],'rejected'); self.assertEqual(replay(p)['status'],'rejected')

    def test_work_and_byte_limits_are_unknown_for_valid_proofs(self):
        payload=canonical(addition_induction())
        self.assertEqual(check(payload,max_work=1)['status'],'unknown_resource_budget')
        self.assertEqual(check(payload,max_bytes=1)['status'],'unknown_resource_budget')
        self.assertEqual(check(payload,max_work=None,max_bytes=None)['status'],'accepted')

    def test_unused_blocks_are_checked(self):
        d=addition_induction(); d['proof']=d['proof'][:1]; d['target']=d['proof'][0]['formula']
        d['blocks'][0]['proof'][-1]['formula']=('bot',)
        self.assertEqual(check(canonical(d))['status'],'rejected')
        self.assertEqual(replay(canonical(d))['status'],'rejected')

    def test_induction_parameters_must_be_universally_closed(self):
        p=logic.Eq(logic.V('x'),logic.V('parameter')); formula=induction_formula('x',p)
        d=request(functions={'zero':0,'succ':1},schemas=['nat-induction'],
                  proof=[line('induction',formula,variable='x',template=p)],target=formula)
        self.assertEqual(check(canonical(d))['status'],'accepted')
        d['target']=formula[2]; d['proof'][0]['formula']=formula[2]
        self.assertEqual(check(canonical(d))['status'],'rejected')

    def test_distribution_has_free_variable_side_condition(self):
        x=logic.V('x'); p=('pred','P',(x,)); q=('pred','Q',())
        a=logic.Imp(logic.All('x',logic.Imp(p,q)),logic.Imp(p,logic.All('x',q)))
        d=request(predicates={'P':1,'Q':0},proof=[line('distribute',a,variable='x',antecedent=p,consequent=q)],target=a)
        self.assertEqual(check(canonical(d))['status'],'rejected')

    def test_native_depth_exhaustion_is_unknown(self):
        # Construct bytes iteratively, avoiding the generator's recursion limit.
        term=b'["var","x"]'
        for _ in range(1500): term=b'["fun","f",['+term+b']]'
        payload=b'{"protocol":"gcts-fol-1","theory":{"functions":{"f":1},"predicates":{},"axioms":{},"schemas":[]},"blocks":[],"proof":[{"rule":"refl","formula":["eq",'+term+b','+term+b']}],"target":["eq",'+term+b','+term+b']}'
        self.assertEqual(check(payload)['status'],'unknown_resource_budget')

    def test_bad_primitive_inside_a_valid_interface_is_rejected(self):
        d=addition_induction(); d['blocks'][0]['proof'][2]['formula']=logic.Imp(('bot',),('bot',))
        self.assertEqual(check(canonical(d))['status'],'rejected')
        self.assertEqual(replay(canonical(d))['status'],'rejected')

if __name__=='__main__': unittest.main()
