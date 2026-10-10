"""Meaningful context and eigenvariable checks against the existing kernels."""
import copy,unittest
from compact_contexts import compile_request
from compact_context_cases import registry
from run_compact_contexts import execute
from check_compact_contexts import certificate

class Contexts(unittest.TestCase):
    def test_branch_and_zero(self):
        for s in registry():
            if s['id'] not in ('branch-donor','zero-derivation'):continue
            c=execute(s);self.assertEqual(certificate(s,c['result'])['root_assumptions'],0)
            self.assertEqual(c['result']['compact']['commands'],14 if s['id']=='branch-donor' else 4)
            self.assertEqual(c['expanded_comparison']['commands'],c['result']['compact']['old_expanded_commands'])
    def test_empty_context(self):
        s=next(s for s in registry() if s['id']=='arithmetic-context')
        s['theory']['axioms']['congruence']=s['hypotheses'][0];s['hypotheses']=();s['bound']=7
        c=execute(s);self.assertEqual(certificate(s,c['result'])['hypotheses'],0)
        self.assertEqual(len(c['result']['compact']['source_commands']),c['result']['compact']['commands'])
    def test_valid_quantifier_scope_and_closure(self):
        s=next(s for s in registry() if s['id']=='ambient-y');r=execute(s)['result'];c=certificate(s,r)
        self.assertEqual(c['closure_variables'],['y'])
        self.assertTrue(any(a['rule']=='distribute' for a in r['compact']['request']['proof']))
        bad=copy.deepcopy(r);bad['compact']['request']['theory']['axioms']['cheat']=s['target']
        with self.assertRaises(ValueError):certificate(s,bad)
    def test_invalid_generalization(self):
        s=next(s for s in registry() if s['id']=='scope-reject');r=execute(s)['result']
        self.assertEqual(r['status'],'exhausted_finite_region')
        fabricated=[dict(kind='generalize',formula=s['target'],refs=(-1,),parameters=dict(variable='x'))]
        with self.assertRaises(ValueError):compile_request(fabricated,s['target'],s['hypotheses'],s['theory'])

if __name__=='__main__':unittest.main()
