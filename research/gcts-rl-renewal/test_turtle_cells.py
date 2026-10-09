import copy,itertools,json,unittest
from collections import Counter
from fractions import Fraction
from pathlib import Path
from turtle import BASE,SYMMETRIES,VERTICES,compose
from turtle_cells import prototype,orientations,mapped,triangle,cell_flags,patch_flags,verify_region,exact_pose
from audit_turtle_cells import face_flags,boundary_check,scanline_overlap,check_pairs,canonical_hash,replay_regions

class TurtleCellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.atoms,cls.stats=prototype();cls.oriented=orientations(cls.atoms)
        cls.path=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal/turtle-cells-001.json'
        cls.data=json.loads(cls.path.read_text())
    def test_independent_boundary_cancellation_catches_omitted_and_extra_atoms(self):
        atoms=face_flags(VERTICES);self.assertEqual(set(atoms),set(self.atoms));self.assertEqual(boundary_check(VERTICES,atoms),44)
        bad=atoms.copy();bad.pop(next(iter(bad)))
        with self.assertRaises(ValueError):boundary_check(VERTICES,bad)
        bad=atoms.copy();bad[20,20,0,0]=triangle((20,20,0,0))
        with self.assertRaises(ValueError):boundary_check(VERTICES,bad)
    def test_all_symmetry_compositions_preserve_flag_owners_and_geometry(self):
        for g,h in itertools.product(SYMMETRIES,repeat=2):
            self.assertIn(compose(g,h),SYMMETRIES)
            for i,s in itertools.product(range(6),range(2)):
                k=(2,-1,i,s);self.assertEqual(mapped(mapped(k,h),g),mapped(k,compose(g,h)))
    def test_clipping_handles_fractional_intersections_and_exact_area(self):
        from turtle_cells import intersection_area
        a=((0,0),(2,0),(0,2));b=((1,0),(3,0),(1,2))
        self.assertEqual(intersection_area(a,b),Fraction(1,2));self.assertEqual(intersection_area(a,a),2)
        self.assertEqual(self.stats['occupied_flags'],240);self.assertEqual(self.stats['coordinate_area'],'20')
    def test_scanlines_distinguish_positive_overlap_from_edge_and_point_contact(self):
        a=((0,0),(2,0),(0,2))
        for b in (a,((0,0),(1,0),(0,1))):self.assertTrue(scanline_overlap(a,b)[0])
        for b in (((2,0),(3,0),(2,1)),((0,0),(0,-2),(2,0)),((4,0),(5,0),(4,1))):self.assertFalse(scanline_overlap(a,b)[0])
    def test_scanlines_include_crossing_heights_and_detect_a_thin_overlap(self):
        # The midpoint of the vertex-height band (0,1) misses this overlap.
        a=((0,0),(10,0),(0,10));b=((7,-1),(11,-1),(11,1))
        yes,witness,_=scanline_overlap(a,b);self.assertTrue(yes);self.assertLess(Fraction(witness[1]),Fraction(1,3))
    def test_full_cell_coverage_requires_all_twelve_flags(self):
        interior=next(p for p,v in BASE.items() if v==12);boundary=next(p for p,v in BASE.items() if v<12)
        yes=verify_region([(0,(0,0,0))],[interior],set(BASE),self.oriented)
        no=verify_region([(0,(0,0,0))],[boundary],set(BASE),self.oriented)
        self.assertTrue(yes['point_complete']);self.assertEqual(yes['missing_required_flags'],0)
        self.assertFalse(no['point_complete']);self.assertGreater(no['missing_required_flags'],0)
        self.assertEqual(len(cell_flags([interior,boundary])),24)
    def test_envelope_containment_counts_every_positive_support_owner(self):
        p=next(iter(BASE));r=verify_region([(0,(0,0,0))],[],set(BASE)-{p},self.oriented)
        self.assertEqual(r['flags_outside_allowed'],BASE[p])
    def test_point_legal_contact_has_disjoint_polygon_flags_and_additive_totals(self):
        row=next(r for r in self.data['pairs'] if not r['overloaded_points'] and r['shared_positive_points'])
        occupied,totals=patch_flags([(0,(0,0,0)),row['pose']],self.oriented)
        self.assertEqual(len(occupied),480);self.assertEqual(sum(totals.values()),480);self.assertLessEqual(max(totals.values()),12)
        row=next(r for r in self.data['pairs'] if r['overloaded_points'])
        with self.assertRaises(ValueError):patch_flags([(0,(0,0,0)),row['pose']],self.oriented)
    def test_declared_domain_rejects_nonlattice_and_duplicate_placements(self):
        for pose in ((True,(0,0,0)),(12,(0,0,0)),(0,(.5,0,-.5)),(0,(1,0,0))):
            with self.assertRaises(ValueError):exact_pose(pose)
        with self.assertRaises(ValueError):patch_flags([(0,(0,0,0))]*2,self.oriented)
        with self.assertRaises(ValueError):cell_flags([(1,0,0)])
    def test_complete_catalog_rejects_omission_even_with_recomputed_fingerprint(self):
        expected=self.data['pairs'];check_pairs(expected,expected,self.data['pair_sha256'])
        for bad in (expected[:-1],list(reversed(expected))):
            with self.assertRaises(ValueError):check_pairs(bad,expected,canonical_hash(bad))
        with self.assertRaises(ValueError):check_pairs(expected,expected,'0'*64)
    def test_equal_looking_float_and_boolean_coordinates_are_rejected(self):
        for value in (0.0,False):
            bad=copy.deepcopy(self.data['pairs']);row=next(r for r in bad if 0 in r['pose'][1]);i=row['pose'][1].index(0);row['pose'][1][i]=value
            with self.assertRaises(ValueError):check_pairs(bad,self.data['pairs'],self.data['pair_sha256'])
    def test_historical_region_replay_rejects_forged_continuous_coverage(self):
        points=[Counter({tuple(p):v for p,v in o['occupancy']}) for o in self.data['orientations']]
        r=replay_regions(self.data,self.oriented,points);self.assertEqual(r['completed_regions'],70)
        bad=copy.deepcopy(self.data);bad['regions'][0]['missing_required_flags']=1
        with self.assertRaises(ValueError):replay_regions(bad,self.oriented,points)

if __name__=='__main__':unittest.main()
