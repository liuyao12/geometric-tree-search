"""Exhaustive finite domains, complete count laws and reference graph invariants."""
import copy,gzip,itertools,random,subprocess,tempfile,unittest
from pathlib import Path
import native_wang_search as S
from native_wang_cases import registry,projection_certificate
from check_native_wang import Reference
from check_native_rectangle import Primitive

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
class NativeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=tempfile.TemporaryDirectory(prefix='gcts-native-test-');p=Path(cls.directory.name);cls.raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());(p/'table.bin').write_bytes(cls.raw)
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'native_wang_domains.cpp'),'-o',str(p/'domains')],check=True)
        cls.oracle=S.Oracle(cls.raw,p/'domains',p/'table.bin');cls.u=S.Universe(cls.oracle);i=cls.oracle.inventory
        cls.reference=Reference(cls.raw,[dict(north=i.head(i.accept,9)),dict(north=i.head(i.start+1,1))]);cls.primitive=Primitive(cls.raw)
    @classmethod
    def tearDownClass(cls):cls.oracle.close();cls.directory.cleanup()
    def test_complete_palette_and_full_head_counts(self):
        i=self.oracle.inventory;self.assertEqual(self.u.inventory_count,264143617200)
        for role,north,allowed in itertools.product(range(3),(None,0,1,-3,i.head(i.accept,9)),(None,range(2*i.A,i.D),range(i.A+1,i.D,i.A))):
            self.assertEqual(self.oracle.count(role,north,allowed),self.reference.count(role,north,allowed))
    def test_finite_domains_against_exhaustive_literal_tiles(self):
        i=self.oracle.inventory;rng=random.Random(58001);symbols=(0,1,9,i.head(i.accept,9),i.head(i.reject,1),i.head(i.start,0),i.head(8642,9))
        for _ in range(120):
            allowed=[tuple(v for v in symbols if rng.randrange(2)) for j in range(3)];north=rng.choice((None,0,1,69));tau=tuple(rng.choice((None,0,1,9)) for _ in range(4));d=self.u.domain(*allowed,north=north,ta=tau[0],tb=tau[1],tc=tau[2],tn=tau[3]);expected=set()
            for key in itertools.product(*allowed):
                try:n=self.primitive.output(key)
                except ValueError:continue
                if north is not None and n!=north:continue
                if all(t is None or (v if v<i.A else (v-i.A)%i.A)==t for v,t in zip((*key,n),tau)):expected.add(key)
            self.assertEqual(set(d.options()),expected);self.assertEqual(d.count,len(expected));self.assertTrue(all(d.contains(key) for key in expected))
    def test_native_projection_and_original_certificate(self):
        spec=registry(self.oracle.inventory,DOC)[0];certificate=projection_certificate(spec,self.oracle.inventory);r=S.search(self.u,spec['pattern'],spec['height'],spec['boundary']+certificate['pins'],projected=True,attempts=100,seconds=30)
        self.assertEqual(r['status'],'finite_exact_native_rectangle');self.assertEqual(r['attempts'],10);self.assertTrue(r['root_rollback_verified'])
        for decorated in (False,True):self.assertEqual(self.primitive.check(spec,r,decorated)['status'],'accepted_original_rectangle')
        bad=copy.deepcopy(r);bad['tiles'][0]['N']+=1
        with self.assertRaises(ValueError):self.primitive.check(spec,bad,False)
    def test_dead_before_forced_and_budget_unknown(self):
        cases=registry(self.oracle.inventory,DOC);spec=cases[4];g=S.Graph(self.u,spec['pattern'],spec['height'],spec['boundary']);self.assertEqual(g.decision()[0],'dead');self.assertTrue(any(d.count==1 for d in g.domains.values()))
        spec=cases[-1];r=S.search(self.u,spec['pattern'],spec['height'],spec['boundary'],attempts=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertFalse(r['tiles'])
    def test_whole_graph_rollback_and_projection_conflicts(self):
        spec=registry(self.oracle.inventory,DOC)[0];c=projection_certificate(spec,self.oracle.inventory);g=S.Graph(self.u,spec['pattern'],spec['height'],spec['boundary']+c['pins'],projected=True);before=g.fingerprint()
        for _ in range(6):
            kind,p,d=g.decision()
            if kind in ('dead','empty'):break
            g.place(p,next(d.options()))
        g.rollback(0);self.assertEqual(g.fingerprint(),before)
        with self.assertRaises(ValueError):S.Graph(self.u,spec['pattern'],spec['height'],spec['boundary']+[[[0,1,1],1],[[0,1,1],0]],projected=True)

if __name__=='__main__':unittest.main()
