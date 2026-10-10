import copy,unittest
import logic as L
import export_wang_proof_notebook as E
import audit_semantic_proofs as A

class ReaderTests(unittest.TestCase):
    def setUp(self):
        a=L.Eq(L.F('zero'),L.F('zero'));theory=dict(functions={'zero':0},predicates={},axioms={},schemas=[])
        self.p=dict(id='fixture',label='Exporter test fixture',theory=theory,target=a,length=1,term_bound=1)
        b=dict(name='reflexivity-fixture',premises=[],conclusion=a,proof=[dict(rule='refl',formula=a)]);request=dict(protocol='gcts-fol-1',theory=theory,target=a,blocks=[b],proof=[dict(rule='block',formula=a,name=b['name'],inputs=[])])
        self.run=dict(lane='fixture',replica=0,cold_seconds=0,native=dict(status='accepted',steps=1,wall_seconds=0),result=dict(status='finite_exact_proof_tiling',nodes=2,branches=0,forced=1,backtracks=0,base_attempts=1),hierarchy=dict(request=request,transactions_used=[]))
    def record(self):return E.proof_record(self.p,self.run,'fixture',dict(file='fixture',sha256='0'*64))
    def test_flattened_root_has_no_opaque_lemma(self):
        r=self.record();self.assertEqual([l['rule'] for l in r['expanded_proof']],['refl']);self.assertEqual(r['expanded_lines'],1)
    def test_exact_certificate_hash(self):
        r=self.record();self.assertEqual(r['certificate_sha256'],E.sha_bytes(A.packed(self.run['hierarchy']['request'])))
    def test_donor_counter_layout_supported(self):
        for field in ('branches','forced','backtracks'):self.run['result'].pop(field)
        self.run['result']['stats']=dict(branches=0,forced=1,backtracks=0);self.run.pop('lane');self.run.pop('replica');r=self.record();self.assertEqual(r['discovered_by'],'donor-gcts');self.assertEqual(r['search']['base_attempts'],1)
    def test_target_binding_rejects_changed_target(self):
        self.p['target']=L.Imp(self.p['target'],self.p['target'])
        with self.assertRaises(ValueError):self.record()
    def test_theory_binding_rejects_changed_axiom(self):
        self.p=copy.deepcopy(self.p);self.p['theory']['axioms']['new']=self.p['target']
        with self.assertRaises(ValueError):self.record()
    def test_unknown_search_cannot_display_positive_theorem(self):
        self.run['result']['status']='unknown_search_budget'
        with self.assertRaises(ValueError):self.record()
    def test_unknown_native_cannot_display_positive_theorem(self):
        self.run['native']['status']='unknown'
        with self.assertRaises(ValueError):self.record()
    def test_invalid_intermediate_line_rejected(self):
        self.run['hierarchy']['request']['blocks'][0]['proof'][0]['formula']=L.Imp(self.p['target'],self.p['target'])
        with self.assertRaises(ValueError):self.record()
    def test_invalid_forward_reference_rejected(self):
        self.run['hierarchy']['request']['blocks'][0]['proof']=[dict(rule='generalize',formula=L.All('x',self.p['target']),variable='x',source=0)]
        with self.assertRaises(ValueError):self.record()
if __name__=='__main__':unittest.main()
