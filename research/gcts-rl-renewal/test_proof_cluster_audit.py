import copy,unittest
import proof_clusters as H,proof_cluster_problems as P
import semantic_proof_catalogs as C
import audit_semantic_proofs as A,audit_proof_clusters as B

class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=[]
        for p in P.donors():
            c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],cls.library);cls.library+=H.promote(c,r,p['length'],cls.library,p['id'])['templates']
        cls.p=P.evaluation()[0];cls.c=C.equational(cls.p['theory'],cls.p['target'],cls.p['term_bound']);cls.r=H.search(cls.c,cls.p['length'],cls.library);cls.h=H.hierarchical_certificate(cls.c,cls.r,cls.p['length'],cls.library)
    def test_all_independently_compiled_instances_match(self):
        a=H.Index(self.c,self.p['length'],self.library);b,complete=B.index(A.freeze(self.c),self.p['length'],A.freeze(self.library),50000);self.assertTrue(complete);self.assertEqual(A.freeze(a.instances),tuple(b))
    def test_complete_tree_and_hierarchical_certificate(self):
        c,r,library=A.freeze(self.c),A.freeze(self.r),A.freeze(self.library);B.run_audit(c,self.p['length'],r,library);B.hierarchy_audit(c,self.p['length'],r,A.freeze(self.h),library)
    def test_altered_member_and_transaction_rejected(self):
        bad=copy.deepcopy(self.r);bad['transaction_samples'][0]['trace']['steps'][0]['role']='invented'
        with self.assertRaises(ValueError):B.run_audit(A.freeze(self.c),self.p['length'],A.freeze(bad),A.freeze(self.library))
    def test_dropped_singleton_fallback_rejected(self):
        p=P.evaluation()[7];c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],self.library)
        def erase(tree):
            if tree.get('children'):tree['children']=[];return True
            return any(erase(x['tree']) for x in tree.get('proposals',()) if x.get('tree'))
        self.assertTrue(erase(r['search_tree']))
        with self.assertRaises(ValueError):B.run_audit(A.freeze(c),p['length'],A.freeze(r),A.freeze(self.library))
    def test_external_statement_reconstruction(self):
        donors,evaluation=B.external()
        for p in P.donors()+P.evaluation():
            expected=donors.get(p['id'],evaluation.get(p['id']));self.assertEqual({k:A.freeze(p[k]) for k in expected},A.freeze(expected))

if __name__=='__main__':unittest.main()
