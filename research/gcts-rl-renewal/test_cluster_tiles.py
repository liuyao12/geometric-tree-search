"""First-class cluster types, inherited channels, incidence and flattening."""
import dataclasses,unittest
from turtle import Model,State,Graph,BASE,SYMMETRIES,transform
import cluster_tiles as c

class ClusterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Model();s=State();s.place(cls.base.placement((0,(0,0,0))),seed=True)
        cls.contact=next(k for p in BASE for k in cls.base.alignments(p) if s.legal(cls.base.placement(k)))
        cls.single=c.make_type(cls.base,'base',0,((0,(0,0,0)),))
        cls.pair=c.make_type(cls.base,'pair',1,((0,(0,0,0)),cls.contact),own_marking={(20,-10,-10):0})

    def test_parent_inherits_child_channels_and_adds_own_channel(self):
        model=c.ClusterModel([self.single,self.pair])
        child=('pair',0,(0,0,0))
        parent=c.compose_type(model,'parent',[child,child],own_marking={(20,-10,-10):1})
        self.assertEqual(parent.level,2);self.assertEqual(len(parent.expansion),2)
        self.assertEqual(dict(parent.marks)[((20,-10,-10),'cluster:1')],0)
        self.assertEqual(dict(parent.marks)[((20,-10,-10),'cluster:2')],1)
        self.assertTrue(c.verify_expansion(self.base,parent))
        altered=dataclasses.replace(parent,occupancy=parent.occupancy[:-1])
        with self.assertRaises(ValueError):c.ClusterModel([altered])
        altered=dataclasses.replace(parent,marks=tuple((p,v) for p,v in parent.marks if p[1]!='cluster:1'))
        with self.assertRaises(ValueError):c.ClusterModel([self.single,self.pair,altered])
        altered=dataclasses.replace(parent,children=(('parent',0,(0,0,0)),))
        with self.assertRaises(ValueError):c.ClusterModel([self.single,self.pair,altered])

    def test_scalar_channel_action_all_symmetries_and_expansion_replay(self):
        model=c.ClusterModel([self.single,self.pair])
        for o,g in enumerate(SYMMETRIES):
            state=c.ClusterState();placement=model.placement(('pair',o,(2,-1,-1)));state.place(placement,seed=True)
            point=tuple(a+b for a,b in zip(transform((20,-10,-10),g),(2,-1,-1)))
            self.assertEqual(state.marks[point,'cluster:1'],0)
            self.assertTrue(c.verify_state(model,state))

    def test_complete_aggregate_graph_and_exact_rollback(self):
        model=c.ClusterModel([self.single,self.pair]);state=c.ClusterState()
        state.place(model.placement(('base',0,(0,0,0))),seed=True);graph=Graph(model,state)
        self.assertEqual(graph.domains,c.exhaustive_domains(model,state))
        snapshot=state.copy();snapshot_graph=graph.copy();kind,p,options=graph.decision(state)
        self.assertIn(kind,('branch','forced'));graph.update(model,state,state.place(model.placement(options[0])))
        self.assertEqual(graph.domains,c.exhaustive_domains(model,state));self.assertTrue(c.verify_state(model,state))
        self.assertEqual(snapshot_graph.domains,c.exhaustive_domains(model,snapshot))
        self.assertEqual(snapshot.owned_base,{(0,(0,0,0))})

    def test_distant_assigned_zero_component_dependency(self):
        model=c.ClusterModel([self.single,self.pair]);state=c.ClusterState();state.roots[(0,0,0)]=0
        graph=Graph(model,state);key=('pair',0,(0,0,0))
        self.assertIn(key,graph.edges);state.marks[((20,-10,-10),'cluster:1')]=1
        graph.update(model,state,{((20,-10,-10),'cluster:1')})
        self.assertNotIn(key,graph.edges);self.assertEqual(graph.domains,c.exhaustive_domains(model,state))

    def test_base_fallback_and_constituent_inventory(self):
        model=c.ClusterModel([self.single,self.pair]);state=c.ClusterState()
        state.place(model.placement(('pair',0,(0,0,0))),seed=True)
        self.assertFalse(state.legal(model.placement(('base',0,(0,0,0)))))
        self.assertTrue(c.verify_state(model,state))
        # Every unmarked base placement is represented by a singleton, regardless
        # of the optional higher-level marker restriction.
        empty=c.ClusterState();empty.roots[(0,0,0)]=0;graph=Graph(model,empty)
        singleton={key[1:] for key in graph.domains[(0,0,0)] if key[0]=='base'}
        self.assertEqual(singleton,set(self.base.alignments((0,0,0))))

if __name__=='__main__':unittest.main()
