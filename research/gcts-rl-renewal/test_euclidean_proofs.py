"""Soundness and negative controls for the geometry compiler."""
import copy,json,unittest
import euclidean_proof_tiles as E
import induction_proof_tiles as T,induction_clusters as H
import audit_euclidean_proofs as A
from serialized_kernel import canonical,check
class Tests(unittest.TestCase):
    def test_complete_inventory(self):
        for name in ('I.5','I.6','triangle-order'):A.inventory(E.catalog(E.problem(name)))
    def test_no_arithmetic_or_rotated_tiles(self):
        c=E.catalog(E.problem('I.5'));self.assertEqual(c['theory']['functions'],{});self.assertEqual(c['theory']['schemas'],[])
        self.assertIn('no rotation/reflection',c['configuration']['orientation'])
    def test_gcts_triangle_order(self):
        c=E.catalog(E.problem('triangle-order'));r=T.search(c,3,support=True,seconds=5)
        self.assertEqual(r['status'],'finite_exact_proof_tiling');A.I.point_run(A.freeze(c),3,A.freeze(r))
    def test_discovered_proof_and_mutations(self):
        c=E.catalog(E.problem('I.5'));r=H.csp_search(c,10,(),marked=True,seconds=5)
        self.assertEqual(r['status'],'finite_exact_proof_tiling');request=r['decoded']['request']
        q=copy.deepcopy(request);q['theory']['axioms'].pop('SAS');self.assertEqual(check(canonical(q))['status'],'rejected')
        q=copy.deepcopy(request);q['proof'][-1]['source']=len(q['proof']);self.assertEqual(check(canonical(q))['status'],'rejected')
        q=copy.deepcopy(c);q['rules'].pop();self.assertRaises(ValueError,A.inventory,q)
    def test_short_and_missing_foundation(self):
        c=E.catalog(E.problem('I.5'),('SAS',));r=T.search(c,10,support=True,seconds=3);self.assertEqual(r['status'],'exhausted_finite_proof_envelope')
if __name__=='__main__':unittest.main(verbosity=2)
