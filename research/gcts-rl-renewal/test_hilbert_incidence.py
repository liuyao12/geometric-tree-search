"""Meaningful incidence compiler, primitive rejection and semantic controls."""
import copy,unittest
import hilbert_incidence_tiles as B
import induction_proof_tiles as T
import audit_hilbert_incidence as A
from serialized_kernel import canonical,check
class Tests(unittest.TestCase):
    def test_all_inventory_types(self):
        for name in ('intersection-unique','incidence-transfer','wrong-intersection'):A.inventory(B.catalog(B.problem(name)))
    def test_foundation_is_incidence_not_congruence(self):
        t,_=B.foundation();self.assertEqual(t['predicates'],dict(Point=1,Line=1,Inc=2));self.assertFalse(t['functions']);self.assertFalse(t['schemas'])
        self.assertEqual(len(t['axioms']),7);self.assertEqual(t['axioms']['I.3-plane-points'][0],'not')
    def test_searched_theorems(self):
        for name,n in [('intersection-unique',2),('incidence-transfer',4)]:
            c=B.catalog(B.problem(name));r=T.search(c,n,support=True,seconds=5)
            self.assertEqual(r['status'],'finite_exact_proof_tiling');A.I.point_run(A.freeze(c),n,A.freeze(r))
            self.assertEqual(check(canonical(r['decoded']['request']))['status'],'accepted')
    def test_missing_axiom_and_changed_proof_rejected(self):
        c=B.catalog(B.problem('incidence-transfer'));r=T.search(c,4,support=True,seconds=5);p=r['decoded']['request']
        q=copy.deepcopy(p);q['theory']['axioms'].pop('I.2-uniqueness');self.assertEqual(check(canonical(q))['status'],'rejected')
        q=copy.deepcopy(p);q['proof'][-1]['source']=len(q['proof']);self.assertEqual(check(canonical(q))['status'],'rejected')
        q=copy.deepcopy(c);q['rules'].pop();self.assertRaises(ValueError,A.inventory,q)
        q=copy.deepcopy(c);q['configuration']['metadata']['I.2-uniqueness']['binders']['l0']='point';self.assertRaises(ValueError,A.inventory,q)
    def test_finite_models_and_countermodels(self):
        t,_=B.foundation();ps={n:B.problem(n) for n in ('intersection-unique','incidence-transfer','wrong-intersection')};A.model_controls(t,ps)
    def test_renaming_preserves_logic(self):
        c=B.catalog(B.problem('intersection-unique'));r=T.search(c,2,support=True,seconds=5);p=copy.deepcopy(r['decoded']['request'])
        names={'Point':'Table','Line':'Chair','Inc':'Relation'}
        def rename(x):
            if isinstance(x,dict):return {k:rename(v) for k,v in x.items()}
            if isinstance(x,(list,tuple)):
                xs=[rename(y) for y in x]
                if xs and xs[0]=='pred':xs[1]=names[xs[1]]
                return xs
            return x
        q=rename(p);q['theory']['predicates']={names[n]:v for n,v in p['theory']['predicates'].items()}
        self.assertEqual(check(canonical(q))['status'],'accepted')
if __name__=='__main__':unittest.main(verbosity=2)
