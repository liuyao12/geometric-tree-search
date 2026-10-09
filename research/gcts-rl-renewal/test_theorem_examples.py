"""Search/axiom separation, Euclidean guard gaps and boundary mutations."""
import copy,unittest
import logic as L
import peano_problems as PA
import euclid_problems as E
import proof_block_search as arithmetic
import horn_proof_search as geometry
from serialized_kernel import canonical,problem_hash,check
from audit_serialized_kernel import replay

class Arithmetic(unittest.TestCase):
    def test_all_twelve_cold_proofs_and_promotions(self):
        library=[];theory=PA.theory()
        for p in PA.statements():
            result=arithmetic.prove(theory,p['target'],library,node_limit=5000)
            self.assertEqual(result['status'],'accepted_proposal',p['id']);self.assertEqual(replay(canonical(result['request']),problem_hash(result['request']))['status'],'accepted');arithmetic.promote(result,library)
        self.assertEqual(len(library),12)
    def test_axioms_are_not_gallery_theorems(self):
        self.assertEqual(len(PA.theory()['axioms']),6)
        self.assertFalse({canonical(a) for a in PA.theory()['axioms'].values()} & {canonical(p['target']) for p in PA.statements()})
    def test_false_successor_claim_stays_unknown(self):
        a=L.V('a');r=arithmetic.prove(PA.theory(),L.All('a',L.Eq(PA.S(a),a)),node_limit=40,max_inductions=0)
        self.assertTrue(r['status'].startswith('unknown'))
    def test_schema_is_not_an_unrestricted_target_axiom(self):
        p=PA.statements()[1];r=arithmetic.prove(PA.theory(),p['target']);d=copy.deepcopy(r['request']);d['proof'][-1]=dict(rule='induction',formula=p['target'],variable='a',template=L.Eq(PA.Z(),PA.Z()))
        self.assertEqual(check(canonical(d),expected_problem_sha256=problem_hash(d))['status'],'rejected')

class Geometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.theory=E.theory();cls.results=[];cls.library=[]
        for p in E.statements():
            r=geometry.prove(cls.theory,p['target'],cls.library);cls.results.append(r)
            if r['status']=='accepted_proposal':geometry.promote(r,cls.library)
    def test_actual_derivations_check_independently(self):
        for r in self.results:self.assertEqual(r['status'],'accepted_proposal');self.assertEqual(replay(canonical(r['request']),problem_hash(r['request']))['status'],'accepted')
    def test_composite_reuses_two_searched_blocks(self):
        r=self.results[2];self.assertEqual({b['name'] for b in r['request']['blocks']},{self.library[0]['name'],self.library[1]['name']})
    def test_circle_drawing_does_not_establish_intersection(self):
        t=copy.deepcopy(self.theory);t['axioms']={n:a for n,a in t['axioms'].items() if not n.startswith('intersection-')}
        self.assertTrue(geometry.prove(t,E.statements()[0]['target'])['status'].startswith('unknown'))
    def test_base_angles_need_congruence(self):
        t=copy.deepcopy(self.theory);t['axioms']={n:a for n,a in t['axioms'].items() if not n.startswith('SAS-')}
        self.assertTrue(geometry.prove(t,E.statements()[1]['target'])['status'].startswith('unknown'))
    def test_search_budget_never_means_unprovable(self):
        r=geometry.prove(self.theory,E.statements()[0]['target'],max_matches=1);self.assertEqual(r['status'],'unknown_search_budget')
    def test_wrong_construction_cannot_replace_witness(self):
        d=copy.deepcopy(self.results[0]['request']);d['proof'][-1]['formula']=E.close(L.Imp(E.Seg(L.V('a'),L.V('b')),E.T(L.V('a'),L.V('b'),L.V('a'))),('a','b'))
        self.assertEqual(replay(canonical(d),problem_hash(self.results[0]['request']))['status'],'rejected')
    def test_triangle_guard_definitions_are_explicit(self):
        self.assertEqual(sum(n.startswith('triangle-guard-') for n in self.theory['axioms']),4)
        self.assertIn('triangle-introduction',self.theory['axioms']);self.assertEqual(self.theory['schemas'],[])
    def test_no_coordinates_or_statement_as_axiom(self):
        self.assertFalse({canonical(a) for a in self.theory['axioms'].values()} & {canonical(p['target']) for p in E.statements()});self.assertNotIn('coordinate',self.theory['functions'])

if __name__=='__main__':unittest.main()
