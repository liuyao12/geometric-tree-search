import copy,json,unittest
from pathlib import Path
import propositional_receptors as R
import propositional_wang_compiler as C
import check_propositional_receptors as A
from serialized_kernel import canonical,check
from audit_semantic_proofs import whole_replay

DOC=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'
class CompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=json.loads((DOC/'propositional-receptors-001.json').read_text())
    def case(self,name):return next(c for c in self.source['cases'] if c['id']==name)
    def compile(self,name):
        c=self.case(name);return C.compile_request(c['runs']['point']['proof'],c['target'],c['hypotheses'])
    def test_all_previous_discoveries_compile(self):
        for c in self.source['cases']:
            if c['runs']['point']['proof']:
                r=C.compile_request(c['runs']['point']['proof'],c['target'],c['hypotheses'])
                self.assertEqual(whole_replay(r['request'],r['statement_pin'])['status'],'accepted')
    def test_hypotheses_are_exact_theory_inputs(self):
        c=self.case('two-premise-links');r=self.compile(c['id']);self.assertEqual(len(r['request']['theory']['axioms']),len(c['hypotheses']))
        self.assertEqual([x['rule'] for x in r['request']['proof'][:3]],['axiom']*3)
        self.assertEqual(r['request']['proof'][-1]['antecedent'],3)
        self.assertEqual(r['request']['proof'][-1]['implication'],2)
    def test_family_preserves_every_primitive_line(self):
        r=self.compile('family-composite');b=r['request']['blocks'][0]
        self.assertEqual(len(b['proof']),5);self.assertEqual(r['request']['proof'][0]['name'],b['name'])
        self.assertEqual(b['proof'][-1]['antecedent'],0);self.assertEqual(b['proof'][-1]['implication'],3)
    def test_arithmetic_and_geometry_are_formulas_not_drawings(self):
        template=R.Model(R.catalog(R.basis(),(A.frozen(self.source['discovered_family']),)),R.imp(R.P,R.P),1)
        r=R.search(template);self.assertIsNotNone(r['proof'])
        for kind in ('arithmetic','geometry'):
            e=C.embedding(kind);v=C.compile_request(r['proof'],R.imp(R.P,R.P),**e)
            self.assertEqual(v['request']['target'],['imp',e['atoms']['P'],e['atoms']['P']])
            self.assertEqual(v['request']['theory']['axioms'],{})
            self.assertEqual(whole_replay(v['request'],v['statement_pin'])['status'],'accepted')
    def test_invalid_prefix_of_family_is_rejected(self):
        r=self.compile('family-composite')['request'];r['blocks'][0]['proof'][0]['formula']=['pred','P',[]]
        self.assertEqual(check(canonical(r))['status'],'rejected');self.assertEqual(whole_replay(r)['status'],'rejected')
    def test_changed_parameter_and_forward_reference_are_rejected(self):
        c=self.case('family-composite');proof=copy.deepcopy(c['runs']['point']['proof']);proof[0]['parameter']=['Q']
        with self.assertRaises(ValueError):C.compile_request(proof,c['target'])
        c=self.case('identity-P');proof=copy.deepcopy(c['runs']['point']['proof']);proof[-1]['refs']=[4,4]
        with self.assertRaises(ValueError):C.compile_request(proof,c['target'])
    def test_missing_signature_is_rejected(self):
        c=self.case('identity-P')
        with self.assertRaises(ValueError):C.compile_request(c['runs']['point']['proof'],c['target'],signature=dict(functions={},predicates={}))
    def test_source_kind_and_metadata_are_bound(self):
        c=self.case('identity-P');proof=copy.deepcopy(c['runs']['point']['proof']);proof[0]['kind']='H3'
        with self.assertRaises(ValueError):C.compile_request(proof,c['target'])
    def test_same_definition_used_twice_is_deduplicated(self):
        c=self.case('family-composite');one=c['runs']['point']['proof'][0];r=C.compile_request([one,one],c['target'])
        self.assertEqual(len(r['request']['blocks']),1);self.assertEqual(r['request']['proof'][0]['name'],r['request']['proof'][1]['name'])

if __name__=='__main__':unittest.main()
