import copy,json,unittest
from pathlib import Path
from turtle import Model,Graph,SYMMETRIES
from cluster_tiles import make_type,ClusterModel,ClusterState
from coarse_continuation import parent_library,RootModel,LiteralOracle,root_state,search,check_failure,DOCS
from capacity_pruning import reachable,CapacityState,CapacityRootModel,CapacityGraph,CapacityOracle
from spatial import canonical

class CoarseContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage=json.loads((DOCS/'multiscale-level1-001.json').read_text())
        cls.children,cls.parents,cls.provenance=parent_library(cls.stage)
        cls.single=make_type(Model(),'auxiliary',0,((0,(0,0,0)),))
        cls.root=make_type(Model(),'root',1,((0,(0,0,0)),))
        cls.definitions=(cls.single,cls.root);cls.active=('root',)
    def test_all_positive_parent_shapes_and_descending_maps(self):
        self.assertEqual(len(self.parents),13)
        self.assertEqual(len({canonical(t.expansion) for t in self.parents}),13)
        model=ClusterModel(self.children+self.parents)
        self.assertEqual(sum(len(p['equivalent_positive_contacts']) for p in self.provenance),22)
        for t,p in zip(self.parents,self.provenance):
            self.assertEqual(t.expansion,canonical(t.expansion));self.assertEqual(len(t.expansion),4)
            self.assertFalse(t.marks);self.assertTrue(all(model.types[k[0]].level<t.level for k in t.children))
            self.assertEqual(tuple(t.children),tuple((n,o,tuple(tr)) for n,o,tr in p['children']))
    def test_immutable_root_compilation_matches_complete_literal_domains(self):
        s=root_state(self.definitions,'root');m=RootModel(self.definitions,self.active,s);g=Graph(m,s)
        self.assertEqual(g.domains,LiteralOracle(self.definitions,self.active).domains(s))
        self.assertTrue(all(k[0]=='root' for k in g.edges))
        self.assertFalse(m.root_legal(('root',0,(0,0,0))))
        self.assertFalse(any(k[0]=='auxiliary' for keys in m.dependencies.values() for k in keys))
    def test_root_and_graph_rollback_retain_all_candidates(self):
        s=root_state(self.definitions,'root');m=RootModel(self.definitions,self.active,s);g=Graph(m,s)
        before=g.fingerprint();original=s.copy();key=min(g.edges);child=s.copy();cg=g.copy()
        cg.update(m,child,child.place(m.placement(key)))
        self.assertEqual(cg.domains,LiteralOracle(self.definitions,self.active).domains(child))
        self.assertEqual(g.fingerprint(),before);self.assertEqual(s,original)
    def test_contribution_monoid_and_required_boundary_scope(self):
        r=reachable((3,4,6,8,9,12));self.assertEqual(set(range(13))-r,{1,2,5})
        with self.assertRaises(ValueError):reachable((True,3))
        p=(0,0,0);q=(1,-1,0)
        class Tile:
            key=('dummy',0,(0,0,0));occupancy=((p,3),(q,3));marks=();expansion=()
        s=CapacityState(r,frozenset({p}));s.totals={q:4};self.assertTrue(s.legal(Tile()))
        s.totals[p]=4;self.assertFalse(s.legal(Tile()))
        c=s.copy();self.assertEqual(c.deficits,s.deficits);self.assertEqual(c.completion_points,s.completion_points)
        c.totals[p]=0;self.assertTrue(c.legal(Tile()));self.assertEqual(s.totals[p],4)
    def test_capacity_graph_domains_and_snapshots_are_exact(self):
        s=CapacityState(reachable((3,4,6,8,9,12)));m0=ClusterModel(self.definitions)
        s.place(m0.placement(('root',0,(0,0,0))),seed=True)
        m=CapacityRootModel(self.definitions,self.active,s);g=CapacityGraph(m,s);oracle=CapacityOracle(self.definitions,self.active)
        self.assertEqual(g.domains,oracle.domains(s));before=g.fingerprint();key=min(g.edges)
        child=s.copy();cg=g.copy();cg.update(m,child,child.place(m.placement(key)))
        self.assertEqual(cg.domains,oracle.domains(child));self.assertEqual(g.fingerprint(),before)
        self.assertIsInstance(cg,CapacityGraph);self.assertEqual(child.deficits,s.deficits)
    def test_budget_cutoff_is_not_a_failure_certificate(self):
        r=search(self.definitions,self.active,'root',nodes=0,seconds=30)
        self.assertEqual(r['status'],'unresolved');self.assertIsNone(r['certificate'])
    def test_saved_mixed_inventory_failure_and_tampered_leaf(self):
        d=json.loads((DOCS/'coarse-gate-001.json').read_text())['reference']
        r=next(r for r in d['results'] if r['status']=='negative' and r['nodes']==1)
        definitions=self.children+self.parents;active=tuple(t.identity for t in self.parents)
        self.assertTrue(check_failure(definitions,active,r['root'],r['certificate'])[0])
        bad=copy.deepcopy(r['certificate']);bad['dead']=[100,-40,-60]
        self.assertFalse(check_failure(definitions,active,r['root'],bad)[0])

if __name__=='__main__':unittest.main()
