import copy,dataclasses,unittest
from turtle import Model,Graph,CAPACITY
from cluster_tiles import make_type
from region_tiles import Boundary,RegionModel,verify_region,independent_domains,search,check_failure,movable_search,packed_state,unpack_state
from coverage import hexagon

class RegionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Model();cls.tile=cls.base.placement((0,(0,0,0)))
        cls.single=make_type(cls.base,'base',0,((0,(0,0,0)),))
        cls.required=frozenset(p for p,v in cls.tile.occupancy)
        cls.ext=tuple((p,CAPACITY-v) for p,v in cls.tile.occupancy)
        cls.boundary=Boundary('one-tile',cls.required,cls.required,cls.ext)

    def test_complete_boundary_inventory_and_point_domains(self):
        m=RegionModel([self.single],self.boundary);s=self.boundary.initial();g=Graph(m,s)
        self.assertEqual(g.domains,independent_domains(m,s));self.assertIn(('base',0,(0,0,0)),g.edges)
        saved=s.copy();snapshot=g.copy();kind,p,keys=g.decision(s)
        self.assertEqual(kind,'forced');g.update(m,s,s.place(m.placement(keys[0])))
        self.assertFalse(g.domains);self.assertTrue(verify_region(m,self.boundary,s,True))
        self.assertEqual(g.domains,independent_domains(m,s));self.assertEqual(snapshot.domains,independent_domains(m,saved))
        self.assertEqual(saved,self.boundary.initial())

    def test_explicit_zero_obligation_and_unrequired_exterior(self):
        distant=(30,-10,-20);ext=self.ext+((distant,3),)
        b=dataclasses.replace(self.boundary,exterior=ext);s=b.initial();m=RegionModel([self.single],b);g=Graph(m,s)
        self.assertNotIn(distant,g.domains)
        untouched=next(p for p,v in self.tile.occupancy if v==12)
        self.assertEqual(s.totals[untouched],0);self.assertIn(untouched,g.domains)
        r=search([self.single],b,seconds=None);self.assertEqual(r['status'],'finite_exact_region')
        self.assertTrue(verify_region(m,b,unpack_state(m,b,r['state']),True))

    def test_distant_assigned_zero_mark_and_dependency_rollback(self):
        marker=(30,-10,-20);marked=make_type(self.base,'marked',1,((0,(0,0,0)),),own_marking={marker:0})
        m=RegionModel([self.single,marked],self.boundary);s=self.boundary.initial();g=Graph(m,s)
        key=('marked',0,(0,0,0));self.assertIn(key,g.edges);snap=s.copy();sg=g.copy()
        s.marks[(marker,'cluster:1')]=1;g.update(m,s,{(marker,'cluster:1')})
        self.assertNotIn(key,g.edges);self.assertEqual(g.domains,independent_domains(m,s))
        self.assertIn(key,sg.edges);self.assertEqual(sg.domains,independent_domains(m,snap))
        b=dataclasses.replace(self.boundary,marks=(((marker,'cluster:1'),1),));m=RegionModel([marked],b)
        self.assertEqual(Graph(m,b.initial()).domains,independent_domains(m,b.initial()))

    def test_checked_failure_unknown_and_movable_boundary_reset(self):
        b=Boundary('too-small',frozenset({(0,0,0)}),frozenset({(0,0,0)}))
        r=search([self.single],b,seconds=None);m=RegionModel([self.single],b)
        self.assertEqual(r['status'],'exhausted_finite_region');self.assertEqual(check_failure(m,b,r['certificate']),(True,1))
        self.assertFalse(check_failure(m,b,{'dead':(9,-9,0)})[0])
        u=search([self.single],self.boundary,node_limit=0,seconds=None);self.assertEqual(u['status'],'unknown_budget');self.assertIsNone(u['certificate'])
        movable=movable_search([self.single],[b,self.boundary],seconds=None)
        self.assertEqual(movable['status'],'finite_exact_movable_region');self.assertEqual(movable['selected'],self.boundary.identity)
        self.assertEqual([a['result']['status'] for a in movable['attempts']],['exhausted_finite_region','finite_exact_region'])
        unknown=movable_search([self.single],[b,self.boundary],node_limit=0,seconds=None)
        self.assertEqual(unknown['status'],'unknown_budget');self.assertIsNone(unknown['selected'])

    def test_independent_flattening_and_export_tamper_rejection(self):
        r=search([self.single],self.boundary,seconds=None);m=RegionModel([self.single],self.boundary)
        s=unpack_state(m,self.boundary,r['state']);self.assertTrue(verify_region(m,self.boundary,s,True))
        for field in ['totals','tile_generations','base_expansion']:
            bad=copy.deepcopy(r['state']);bad[field]=[]
            with self.assertRaises(ValueError):unpack_state(m,self.boundary,bad)
        bad=s.copy();bad.generations.clear();self.assertFalse(verify_region(m,self.boundary,bad,True))
        different=dataclasses.replace(self.boundary,identity='different',marks=((((30,-10,-20),'base'),0),))
        self.assertFalse(verify_region(m,different,s,True))
        with self.assertRaises(ValueError):Boundary('bad',self.required,self.required,(((0,0,0),True),))
        for field in ['totals','tile_generations','base_expansion']:
            bad=copy.deepcopy(r['state'])
            if field=='tile_generations':bad[field][0]=True
            elif field=='totals':bad[field][0]=(bad[field][0][0],True)
            else:bad[field][0]=(True,(0,0,0))
            with self.assertRaises(ValueError):unpack_state(m,self.boundary,bad)

    def test_full_negative_tree_rejects_an_omitted_alternative(self):
        points=frozenset(hexagon(5));b=Boundary('closed-hex',points,points)
        r=search([self.single],b,seconds=None);m=RegionModel([self.single],b)
        self.assertEqual(r['status'],'exhausted_finite_region');self.assertGreater(r['branches'],0)
        self.assertTrue(check_failure(m,b,r['certificate'])[0]);self.assertGreater(len(r['certificate']['children']),1)
        bad=copy.deepcopy(r['certificate']);bad['children'].pop()
        self.assertFalse(check_failure(m,b,bad)[0])

if __name__=='__main__':unittest.main()
