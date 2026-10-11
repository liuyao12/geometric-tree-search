"""Native reset, unknown semantics and proof discovery without a supplied trace."""
import gzip,json,sys,tempfile,unittest
from pathlib import Path
from certificate_boundary_cases import cases
from certificate_boundary_search import Oracle,search
from audit_proof_boundary import code_bytes
D=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'
class NativeBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(dir='/private/tmp');cls.p=Path(cls.tmp.name);cls.micro=json.loads(gzip.decompress((D/'proof-boundary-microcode-001.json.gz').read_bytes()));cls.initial=json.loads((D/'proof-boundary-001.json').read_text())['cases'][0]['initial'];(cls.p/'code.bin').write_bytes(code_bytes(cls.micro))
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def oracle(self):return Oracle(self.micro,self.initial,sys.argv[1] if len(sys.argv)>1 else '/private/tmp/gcts-boundary-oracle',self.p/'code.bin',self.p)
    def test_unknown_is_not_rejection(self):
        o=self.oracle()
        try:
            r=search(cases()[0],o,micro_steps=1);self.assertEqual(r['status'],'unknown_search_budget');self.assertEqual(r['queries'],1);self.assertEqual(r['prefix_rejections'],0);self.assertTrue(r['root_path_restored']);self.assertIsNone(r['found'])
        finally:o.close()
    def test_zero_budget_has_no_native_queries(self):
        o=self.oracle()
        try:r=search(cases()[-1],o);self.assertEqual(r['queries'],0);self.assertEqual(r['nodes'],0);self.assertEqual(r['status'],'unknown_search_budget');self.assertTrue(r['root_path_restored'])
        finally:o.close()
    def test_full_reset_after_unknown(self):
        o=self.oracle();s=cases()[0];proof=[dict(rule='refl',formula=s['target'])]
        try:
            a=o.query(s,proof,True,10**9);o.query(s,proof,True,1);b=o.query(s,proof,True,10**9)
            for k in ('output_sha256','input_sha256'):self.assertEqual(a[k],b[k])
            for k in ('micro_steps','physical_steps','micro_fnv64','state'):self.assertEqual(a['result'][k],b['result'][k])
        finally:o.close()
    def test_quantified_proof_is_chosen(self):
        o=self.oracle()
        try:
            r=search(cases()[1],o);self.assertEqual(r['status'],'native_proof_discovered');self.assertEqual([l['rule'] for l in r['found']['proof']],['refl','generalize']);self.assertTrue(r['root_path_restored']);self.assertGreater(len(o.records),2)
        finally:o.close()
if __name__=='__main__':unittest.main(argv=[sys.argv[0]])
