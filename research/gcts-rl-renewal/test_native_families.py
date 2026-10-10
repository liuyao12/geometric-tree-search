"""Native receptor binding, guarded expansion, unchanged fallback and rollback."""
import copy,gzip,json,subprocess,tempfile,unittest
from pathlib import Path
from native_wang_search import Oracle,Universe,Graph,search as original
from native_wang_cases import registry,projection_certificate
from native_family_catalog import mine,validate,Matcher
from native_family_search import search,ordered
from native_family_policy import FEATURES,choose,update
from check_native_family_points import check
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
class NativeFamilies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='gcts-native-families-test-');p=Path(cls.tmp.name);cls.raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());(p/'table.bin').write_bytes(cls.raw);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'native_wang_domains.cpp'),'-o',str(p/'domains')],check=True);cls.o=Oracle(cls.raw,p/'domains',p/'table.bin');cls.u=Universe(cls.o);i=cls.o.inventory
        tiles=[dict(x=x,y=y,**i.tile(*(69 if j==1 else 1 for j in (x-1,x,x+1)))) for y in range(3) for x in range(3)]
        cls.library,_=mine([dict(result=dict(status='finite_exact_native_rectangle',tiles=tiles,width=3,height=3))],i)
    @classmethod
    def tearDownClass(cls):cls.o.close();cls.tmp.cleanup()
    def test_typed_symbol_binding_and_original_guard(self):
        i=self.o.inventory;pattern=[[4],[69],[4]];boundary=[v for y in range(3) for v in ([[-1,2*y],[4,4]],[[5,2*y],[4,4]])];g=Graph(self.u,pattern,3,boundary,projected=True);m=Matcher(self.library,g);found=[m.instantiate(t,(0,0)) for t in self.library if t['width']==3 and t['height']==2];valid=[x for x in found if x is not None];self.assertTrue(valid);self.assertTrue(any(4 in x['binding'].values() for x in valid));self.assertTrue(all(self.o.inventory.tile(*k) for x in valid for _,k in x['members']))
        pattern=[[4],[i.head(i.reject,9)],[4]];bad=Graph(self.u,pattern,3,boundary,projected=True);self.assertTrue(all(Matcher(self.library,bad).instantiate(t,(0,0)) is None for t in self.library if t['width']==3))
    def test_hierarchy_and_literal_source_corruptions(self):
        self.assertTrue(validate(self.library,self.o.inventory));bad=copy.deepcopy(self.library);bad[0]['source']['tiles'][0]['N']+=1
        with self.assertRaises(ValueError):validate(bad,self.o.inventory)
        bad=copy.deepcopy(self.library);bad[0]['hierarchy']['children'][1]=bad[0]['hierarchy']['children'][0]
        with self.assertRaises(ValueError):validate(bad,self.o.inventory)
    def test_zero_and_base_preserve_original_tree(self):
        spec=registry(self.o.inventory,DOC)[0];b=spec['boundary']+projection_certificate(spec,self.o.inventory)['pins'];a=original(self.u,spec['pattern'],spec['height'],b,projected=True,attempts=50);r=search(self.u,spec['pattern'],spec['height'],b,self.library,'policy',[0.]*len(FEATURES),attempts=50)
        self.assertEqual((a['status'],a['attempts'],a['tiles']),(r['status'],r['attempts'],r['tiles']));self.assertFalse(r['hints']);self.assertTrue(r['root_rollback_verified']);check(self.raw,spec,r)
        def stripped(e):return {k:v for k,v in e.items() if k in ('kind','point','key','count','depth','census')}
        self.assertEqual(json.loads(json.dumps(a['events'])),[stripped(e) for e in r['events']])
    def test_original_fallback_exactly_once(self):
        symbols=(1,9,69);d=self.u.domain(symbols,symbols,symbols);keys=list(d.options());preferred=keys[-2:];result=list(ordered(d,preferred));self.assertEqual(result[:2],sorted(preferred));self.assertEqual(set(result),set(keys));self.assertEqual(len(result),len(keys))
    def test_dead_and_zero_budget_keep_tristate(self):
        s=registry(self.o.inventory,DOC)[4];b=s['boundary']+projection_certificate(s,self.o.inventory)['pins'];r=search(self.u,s['pattern'],s['height'],b,self.library,'fixed',attempts=50);self.assertEqual(r['events'][0]['kind'],'dead');self.assertEqual(r['attempts'],0);self.assertEqual(r['status'],'exhausted_finite_native_rectangle')
        s=registry(self.o.inventory,DOC)[0];b=s['boundary']+projection_certificate(s,self.o.inventory)['pins'];r=search(self.u,s['pattern'],s['height'],b,self.library,'fixed',attempts=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertFalse(r['tiles'])
if __name__=='__main__':unittest.main()
