import copy,dataclasses,unittest
from turtle import Model,SYMMETRIES,sub,transform,verify_patch,compose
from spatial import moved
from cluster_tiles import ClusterModel,ClusterState,compose_type,verify_state
from cluster_learning import corona,check_corona_failure
from multiscale_learning import contact_catalog,seeds,Palette,decorate,disagreements,plain
from run_multiscale_regions import initial_types,make_parent

class MultiscaleLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.single,cls.a,cls.b=initial_types();cls.types=(cls.a,cls.b);cls.catalog=contact_catalog(cls.types)
    def test_complete_cross_type_catalog_from_literal_base_semantics(self):
        expected=set();base=Model()
        for a in self.types:
            for b in self.types:
                for o,g in enumerate(SYMMETRIES):
                    for tr in {sub(p,transform(q,g)) for p,v in a.occupancy for q,w in b.occupancy}:
                        right=moved(b.expansion,g,tr)
                        if not set(a.expansion)&set(right) and verify_patch(base,a.expansion+right):expected.add((a.identity,b.identity,o,tr))
        self.assertEqual(set(self.catalog),expected);self.assertEqual(len(expected),1818)
    def test_shared_positive_equalities_and_unknown_nonconstraints(self):
        k=next(k for k in self.catalog if k[0]!=k[1]);p=Palette(self.types)
        p.add({'contact':k,'status':'unresolved'});self.assertEqual(p.history[-1]['classes'],104)
        p.add({'contact':k,'status':'negative'});before=p.finish()[1]['negative_rejected'];self.assertEqual(before,1)
        p.add({'contact':k,'status':'positive'});markings,stats=p.finish()
        self.assertEqual(stats['negative_rejected'],0);self.assertEqual(stats['positive_accepted'],1)
        self.assertTrue(all(not m for m in markings.values()))
    def test_unmarked_catalog_ignores_inherited_and_own_values(self):
        p=self.a.occupancy[0][0];marked=decorate(self.a,{p:0})
        self.assertEqual(contact_catalog((marked,self.b)),self.catalog)
        self.assertFalse(plain(marked).marks);self.assertEqual(plain(marked).expansion,marked.expansion)
    def test_all_disagreements_are_declared_capacity_legal_contacts(self):
        p=Palette(self.types)
        for k in self.catalog[:20]:p.add({'contact':k,'status':'negative'}) # encoder controls only
        markings,stats=p.finish();excluded=disagreements(self.types,markings)
        self.assertTrue(excluded<=set(self.catalog));self.assertTrue(excluded)
        self.assertTrue(any(v==0 for m in markings.values() for v in m.values()))
    def test_parent_owns_a_new_channel_and_preserves_children(self):
        k=next(k for k in self.catalog if k[0]!=k[1]);children=tuple(decorate(t,{t.occupancy[0][0]:0}) for t in self.types)
        # Synthetic hierarchy control uses unmarked child maps; it does not
        # pretend this contact is a positive extension label.
        bare,keys=make_parent(self.types,{'samples':[{'status':'positive','contact':k}]})
        marked=decorate(bare,{bare.occupancy[-1][0]:0});m=ClusterModel([*self.types,marked])
        for o,g in enumerate(SYMMETRIES):
            state=ClusterState();state.place(m.placement((marked.identity,o,(0,0,0))),seed=True)
            self.assertTrue(verify_state(m,state));self.assertIn((transform(bare.occupancy[-1][0],g),'cluster:2'),state.marks)
        inherited=compose_type(ClusterModel([children[0]]),'inherited-parent',[(children[0].identity,0,(0,0,0))])
        bad=dataclasses.replace(inherited,marks=())
        with self.assertRaises(ValueError):ClusterModel([children[0],bad])
    def test_cross_type_negative_has_an_independent_base_failure(self):
        k=next(k for k in self.catalog if k[0]!=k[1]);fixed=seeds(self.types,k)
        r=corona(Model(),fixed,5000,15)
        self.assertEqual(r['status'],'negative');self.assertTrue(check_corona_failure(Model(),fixed,r['certificate'])[0])
        self.assertFalse(check_corona_failure(Model(),fixed,{'dead':(80,-40,-40)})[0])
    def test_symmetry_preserves_shared_scalar_values_and_disagreements(self):
        p=Palette(self.types);p.add({'contact':self.catalog[0],'status':'negative'});marks,stats=p.finish()
        decorated=[decorate(t,marks[t.identity]) for t in self.types];m=ClusterModel(decorated)
        excluded=disagreements(self.types,marks)
        for root_name,other,o,tr in list(excluded)[:5]:
            for i,g in enumerate(SYMMETRIES):
                s=ClusterState();s.place(m.placement((root_name,i,(0,0,0))),seed=True)
                key=other,SYMMETRIES.index(compose(g,SYMMETRIES[o])),transform(tr,g)
                self.assertFalse(s.legal(m.placement(key)))
    def test_level_and_identity_guards(self):
        with self.assertRaises(ValueError):Palette((self.single,self.a))
        with self.assertRaises(ValueError):Palette((self.a,self.a))

if __name__=='__main__':unittest.main()
