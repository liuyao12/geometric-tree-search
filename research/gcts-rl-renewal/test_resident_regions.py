import dataclasses,unittest
from turtle import Model,Graph
from cluster_tiles import make_type,exhaustive_domains
from region_tiles import Boundary,RegionModel,search as original_search,verify_region,unpack_state
from resident_regions import Universe,search
from coverage import hexagon

class ResidentRegionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=Model();cls.tile=base.placement((0,(0,0,0)));cls.single=make_type(base,'base',0,((0,(0,0,0)),))
        cls.allowed=frozenset(p for p,v in cls.tile.occupancy);cls.ext=tuple((p,12-v) for p,v in cls.tile.occupancy)
        cls.boundary=Boundary('one',cls.allowed,cls.allowed,cls.ext);cls.u=Universe((cls.single,),cls.allowed)
    def test_resident_and_cold_inventories_and_domains_equal(self):
        for b in (self.boundary,Boundary('other',frozenset({min(self.allowed)}),self.allowed)):
            s=b.initial();cold=RegionModel((self.single,),b);resident=self.u.bind(b)
            self.assertEqual({k for ks in cold.index.values() for k in ks},{k for ks in resident.index.values() for k in ks})
            self.assertEqual(Graph(cold,s).fingerprint(),Graph(resident,s).fingerprint())
            self.assertEqual(Graph(resident,s).domains,exhaustive_domains(resident,s))
    def test_zero_roots_distant_marks_and_exact_snapshot_rollback(self):
        marker=(30,-10,-20);marked=make_type(Model(),'marked',1,((0,(0,0,0)),),own_marking={marker:0})
        u=Universe((self.single,marked),self.allowed);m=u.bind(self.boundary);s=self.boundary.initial();g=Graph(m,s)
        self.assertIn(('marked',0,(0,0,0)),g.edges);before=s.copy();snapshot=g.copy()
        s.marks[marker,'cluster:1']=1;g.update(m,s,{(marker,'cluster:1')})
        self.assertNotIn(('marked',0,(0,0,0)),g.edges);self.assertEqual(g.domains,exhaustive_domains(m,s))
        self.assertEqual(snapshot.domains,exhaustive_domains(m,before));self.assertNotIn((marker,'cluster:1'),before.marks)
    def test_request_boundaries_do_not_share_state_or_exclusions(self):
        bad=Boundary('dead',frozenset({(40,-20,-20)}),self.allowed|{(40,-20,-20)})
        u=Universe((self.single,),bad.allowed)
        r=search((self.single,),bad,seconds=None,universe=u);self.assertEqual(r['status'],'exhausted_finite_region')
        good=dataclasses.replace(self.boundary,allowed=bad.allowed)
        r=search((self.single,),good,seconds=None,universe=u);self.assertEqual(r['status'],'finite_exact_region')
        self.assertTrue(verify_region(u.bind(good),good,unpack_state(u.bind(good),good,r['state']),True))
    def test_guard_against_envelope_and_frozen_marking_version_changes(self):
        with self.assertRaises(ValueError):self.u.bind(dataclasses.replace(self.boundary,allowed=self.allowed|{(30,-10,-20)}))
        marked=make_type(Model(),'base',0,((0,(0,0,0)),),own_marking={(30,-10,-20):0})
        with self.assertRaises(ValueError):search((marked,),self.boundary,universe=self.u)
    def test_representation_controls_match_original_scheduler_trace(self):
        for seed in (0,1):
            original=original_search((self.single,),self.boundary,seed=seed,seconds=None)
            cold=search((self.single,),self.boundary,seed=seed,seconds=None)
            resident=search((self.single,),self.boundary,seed=seed,seconds=None,universe=self.u)
            for field in ('status','nodes','branches','forced','backtracks','state','attempted_base_placements'):
                self.assertEqual(original[field],cold[field]);self.assertEqual(cold[field],resident[field])
    def test_budget_exhaustion_is_unknown_with_no_failure_certificate(self):
        r=search((self.single,),self.boundary,node_limit=0,seconds=None,universe=self.u)
        self.assertEqual(r['status'],'unknown_budget');self.assertIsNone(r['certificate'])

if __name__=='__main__':unittest.main()
