import copy,sys,unittest
import proof_block_search as s
import proof_block_problems as problems
import logic
from serialized_kernel import canonical,check,problem_hash
from audit_serialized_kernel import replay

class ProofBlockTests(unittest.TestCase):
    def test_discovered_lemmas_expand_in_independent_kernel(self):
        library=[]
        for problem in problems.discovery():
            r=s.prove(problems.theory(),problem['target'],library,node_limit=500,slack=2)
            self.assertEqual(r['status'],'accepted_proposal');self.assertEqual(replay(canonical(r['request']),problem_hash(r['request']))['status'],'accepted');s.promote(r,library)
        self.assertEqual(len(library),6);self.assertTrue(library[-1]['provenance']['dependencies']);self.assertGreater(library[2]['expanded_rules'],len(library[2]['proof']))
    def test_zero_weights_and_empty_library_are_real_initial_state(self):
        p=s.Policy();self.assertFalse(dict(p.weights));self.assertEqual(p.updates,0)
        r=s.prove(problems.theory(),problems.discovery()[0]['target']);self.assertEqual(r['blocks'],0)
    def test_only_bound_pattern_variables_match(self):
        x,y=logic.V('x'),logic.V('y');env={}
        self.assertFalse(s.bind(x,y,set(),env));self.assertTrue(s.bind(x,y,{'x'},env));self.assertFalse(s.bind(x,logic.F('zero'),{'x'},env))
    def test_reverse_direction_is_proved_not_assumed(self):
        a=logic.V('a');z=logic.F('zero');target=logic.All('a',logic.Eq(a,logic.F('add',a,z)))
        r=s.prove(problems.theory(),target);self.assertEqual(r['status'],'accepted_proposal');self.assertEqual(replay(canonical(r['request']))['status'],'accepted');self.assertTrue(any(a['direction']==-1 for rec in r['records'] for a in rec.get('path',[])))
    def test_hole_name_is_fresh_in_context(self):
        x=logic.V('gctsHole0');target=logic.All('gctsHole0',logic.Eq(logic.F('add',x,logic.F('zero')),x))
        r=s.prove(problems.theory(),target);self.assertEqual(replay(canonical(r['request']))['status'],'accepted');self.assertTrue(all(l.get('variable')!='gctsHole0' for l in r['request']['proof'] if l['rule']=='eq_subst'))
    def test_simultaneous_parameter_substitution_avoids_capture(self):
        library=[];goal=problems.discovery()[-2]['target'];r=s.prove(problems.theory(),goal);s.promote(r,library)
        a,b,c=map(logic.V,('a2','a0','a1'));target=problems.close(logic.Eq(logic.F('add',logic.F('add',a,b),c),logic.F('add',a,logic.F('add',b,c))),('a2','a0','a1'))
        r=s.prove(problems.theory(),target,library);self.assertEqual(r['status'],'accepted_proposal');self.assertEqual(replay(canonical(r['request']))['status'],'accepted')
    def test_recursive_base_case_does_not_assume_associativity(self):
        r=s.prove(problems.theory(),problems.discovery()[-1]['target'],node_limit=500,slack=2)
        self.assertEqual(r['status'],'accepted_proposal');self.assertFalse(r['request']['blocks']);self.assertTrue(any(q.get('recursive_base') for q in r['records']));self.assertEqual(replay(canonical(r['request']))['status'],'accepted')
    def test_deduction_preserves_eigenvariable_rule(self):
        p=logic.Eq(logic.V('a'),logic.V('a'));lines=[dict(rule='assumption',formula=p,index=0)]
        lifted=s.deduce(lines,p);self.assertEqual(lifted[-1]['formula'],logic.Imp(p,p))
        with self.assertRaises(ValueError):s.deduce([dict(rule='generalize',formula=logic.All('a',p),variable='a',source=0)],p)
    def test_minimal_dependency_closure_still_checks_every_included_block(self):
        library=[]
        for problem in problems.discovery()[:3]:s.promote(s.prove(problems.theory(),problem['target'],library),library)
        r=s.prove(problems.theory(),problems.discovery()[0]['target'],library);self.assertEqual(len(r['request']['blocks']),1)
        altered=copy.deepcopy(r['request']);altered['blocks'][0]['proof'][-1]['formula']=['bot'];self.assertEqual(check(canonical(altered))['status'],'rejected')
    def test_changed_target_and_theory_are_rejected_by_external_pin(self):
        r=s.prove(problems.theory(),problems.discovery()[0]['target']);d=r['request'];pin=problem_hash(d)
        for changed in (dict(d,target=['bot']),dict(d,theory=dict(d['theory'],schemas=[]))):self.assertEqual(check(canonical(changed),expected_problem_sha256=pin)['status'],'rejected')
    def test_policy_never_changes_matching_candidates_or_fallback(self):
        p=s.Policy();p.weights['finishes']=-100
        target=problems.discovery()[0]['target'];baseline=s.prove(problems.theory(),target,node_limit=100)
        r=s.prove(problems.theory(),target,policy=p,rollouts=2,node_limit=100,seed=9)
        self.assertEqual(baseline['status'],r['status']);self.assertEqual(replay(canonical(r['request']))['status'],'accepted');self.assertEqual(p.updates,0)
    def test_resource_and_missing_induction_remain_unknown(self):
        target=problems.discovery()[3]['target'];r=s.prove(problems.theory(),target,node_limit=0,max_inductions=0)
        self.assertEqual(r['status'],'unknown_search_budget_or_fragment');no_schema=dict(problems.theory(),schemas=[]);self.assertEqual(s.prove(no_schema,target,node_limit=50)['status'],'unknown_search_budget_or_fragment')
    def test_disjoint_training_and_evaluation_statements(self):
        train=problems.family(2701,24);evaluation=problems.family(2702,18,True)
        self.assertFalse({canonical(p['target']) for p in train}&{canonical(p['target']) for p in evaluation})

if __name__=='__main__':unittest.main()
