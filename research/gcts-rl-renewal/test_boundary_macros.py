import copy,json,unittest
from pathlib import Path
from turtle import Graph,Policy
from resident_regions import Universe
from region_tiles import unpack_state
from boundary_macros import singleton,problems,mine,Proposer,search
from audit_boundary_macros import Oracle

class BoundaryMacroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=problems(True)[0];cls.u=Universe((singleton(),),cls.b.allowed)
        cls.donor=search(cls.b,cls.u,91000,seconds=None)
        cls.library,_=mine([cls.donor],cls.u.model);cls.proposer=Proposer(cls.library)
        cls.oracle=Oracle(cls.b.allowed)
    def test_singleton_inventory_is_complete_literal_inventory(self):
        self.assertEqual(set(self.u.keys),set(self.oracle.values))
        for k in self.u.keys:self.assertEqual(dict(self.u.model.placement(k).occupancy),dict(self.oracle.values[k]))
    def test_mining_uses_successful_local_data_and_variable_sizes(self):
        self.assertTrue(self.library);self.assertGreater(len({len(m['expansion']) for m in self.library}),1)
        bad=dict(self.donor,status='unknown_budget')
        self.assertEqual(mine([bad],self.u.model)[0],[])
        self.assertTrue(all(m['donor_seeds']==[91000] for m in self.library))
    def test_proposals_retain_every_singleton_and_restore_graph(self):
        m=self.u.bind(self.b);s=self.b.initial();g=Graph(m,s);before=s.copy();finger=g.fingerprint()
        kind,p,keys=g.decision(s);self.assertEqual(kind,'branch')
        actions=self.proposer.actions(m,s,g,keys)
        self.assertTrue({(k,) for k in keys}<=set(actions));self.assertEqual(s,before);self.assertEqual(g.fingerprint(),finger)
        self.assertTrue(any(len(a)>1 for a in actions))
        for a in actions:
            child=s.copy();cg=g.copy()
            for k in a:
                self.assertIn(k,cg.decision(child)[2]);cg.update(m,child,child.place(m.placement(k)))
    def test_macro_execution_obeys_each_base_scheduler_decision(self):
        r=search(self.b,self.u,91001,seconds=None,policy=Policy(),proposer=self.proposer)
        self.assertEqual(r['status'],'finite_exact_region');self.assertTrue(self.oracle.replay(r,self.b))
        self.assertGreaterEqual(r['attempted_base_placements'],len(r['execution']))
        self.assertIsNone(r['certificate'])
    def test_existing_context_is_owned_once(self):
        m=self.u.bind(self.b);s=self.b.initial();g=Graph(m,s);k=g.decision(s)[2][0]
        g.update(m,s,s.place(m.placement(k)));before=s.copy()
        actions=self.proposer.actions(m,s,g,g.decision(s)[2])
        self.assertEqual(s,before)
        self.assertTrue(all(not s.owned_base.intersection(m.placement(k).expansion) for a in actions for k in a))
    def test_unknown_has_no_negative_certificate_and_budget_is_base_moves(self):
        r=search(self.b,self.u,91000,attempt_limit=1,seconds=None,proposer=self.proposer)
        self.assertEqual(r['status'],'unknown_budget');self.assertIsNone(r['certificate'])
        self.assertEqual(r['attempted_base_placements'],1);self.assertTrue(self.oracle.replay(r,self.b))
    def test_saved_schedule_pose_and_expansion_tampering_reject(self):
        self.assertTrue(self.oracle.replay(self.donor,self.b))
        for field in ('execution','state'):
            bad=copy.deepcopy(self.donor)
            if field=='execution':bad[field][0]['point']=[90,-45,-45]
            else:bad[field]['base_expansion']=[]
            self.assertFalse(self.oracle.replay(bad,self.b))
    def test_new_boundary_starts_from_fresh_state(self):
        r=search(problems(True)[1],self.u,91001,seconds=None)
        self.assertTrue(self.oracle.replay(r,problems(True)[1]))
        m=self.u.bind(self.b);s=unpack_state(m,self.b,self.donor['state'])
        self.assertNotEqual(s.roots,problems(True)[1].initial().roots)
    def test_boolean_capacity_and_generation_are_not_exact_integers(self):
        for field in ('tile_generations','totals'):
            bad=copy.deepcopy(self.donor)
            bad['state']=json.loads(json.dumps(bad['state']))
            if field=='tile_generations':bad['state'][field][0]=True
            else:bad['state'][field][0][1]=True
            self.assertFalse(self.oracle.replay(bad,self.b))

if __name__=='__main__':unittest.main()
