"""Additional post-run certificate checks; do not change cold-run provenance."""
import copy,unittest
from turtle import Model,rooted,Graph,pair_catalog,one_corona,exhaustive_domains,check_failure_certificate
from validate_halo import point_domain,check_failure

class IndependentCertificates(unittest.TestCase):
    def test_point_domains_equal_full_independent_enumeration(self):
        model=Model({(20,-20,0):0}); state=rooted(model)
        state.roots[0,10,-10]=0; state.generations[0,10,-10]=0
        for p,cs in exhaustive_domains(model,state).items(): self.assertEqual(point_domain(model,state,p),cs)

    def test_checked_trees_and_missing_alternative(self):
        model=Model(); sample=None
        for key in pair_catalog(model):
            s=one_corona(model,key,200,2)
            if s["status"]=="negative" and "children" in s["certificate"]: sample=s; break
        self.assertIsNotNone(sample)
        self.assertEqual(check_failure(model,sample["second"],sample["certificate"]),
                         check_failure_certificate(model,sample["second"],sample["certificate"]))
        damaged=copy.deepcopy(sample["certificate"]); damaged["children"].pop()
        self.assertFalse(check_failure(model,sample["second"],damaged)[0])

    def test_fake_or_nonfrontier_dead_leaf_rejected(self):
        model=Model(); second=pair_catalog(model)[0]; state=rooted(model,second)
        for p,cs in exhaustive_domains(model,state).items():
            if cs:
                self.assertFalse(check_failure(model,second,{"dead":p})[0]); break
        self.assertFalse(check_failure(model,second,{"dead":(100,0,-100)})[0])

if __name__=="__main__": unittest.main()
