import itertools,json,random,unittest
from collections import Counter
from pathlib import Path
from turtle import Graph,Policy
from region_tiles import Boundary
from resident_regions import Universe
from boundary_macros import singleton
from boundary_responses import declarations,validate,relocate
from conditional_clusters import CompiledAtlas,Proposal,Pending,permitted,search,boundaries,moving_families
from audit_boundary_macros import Oracle
from audit_boundary_responses import domains

class ConditionalClusterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=declarations(True)[1];cls.u=Universe((singleton(),),cls.b.allowed)
        p=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal/boundary-responses-001.json'
        cls.lib=json.loads(p.read_text())['library'];cls.atlas=CompiledAtlas(cls.lib,cls.u);cls.oracle=Oracle(cls.b.allowed)
    def test_interval_capacity_law_exhausts_every_single_point_case(self):
        for delta in range(13):
            for incoming in range(13):
                for partial in range(delta+1):
                    if incoming<=12-delta:self.assertLessEqual(incoming+partial,12)
                self.assertEqual(incoming+delta<=12,incoming<=12-delta)
    def test_every_permutation_of_a_small_response_is_legal_for_interval_inputs(self):
        records=validate(self.lib,self.u.model.base);r=next(r for r in records.values() if len(r.sequence)==3)
        dv=dict(r.delta);rng=random.Random(142001)
        inputs=[{p:0 for p in dv},{p:12-v for p,v in dv.items()},{p:rng.randrange(13-v) for p,v in dv.items()}]
        for incoming in inputs:
            for order in itertools.permutations(r.sequence):
                totals=Counter(incoming)
                for k in order:totals.update(dict(self.u.model.base.placement(k).occupancy));self.assertTrue(all(v<=12 for v in totals.values()))
                self.assertEqual(dict(totals),{p:incoming[p]+v for p,v in dv.items()})
    def test_compiled_index_has_every_member_and_only_exact_inventory_keys(self):
        count=0;inventory=set(self.u.keys)
        for i,(ti,tr,members) in enumerate(self.atlas.poses):
            self.assertEqual(len(members),len(set(members)))
            for k in members:self.assertIn(k,inventory);self.assertIn(i,self.atlas.index[k]);count+=1
        self.assertEqual(count,self.atlas.manifest['member_incidences'])
    def test_adaptive_order_can_follow_a_later_member_forced_by_scheduler(self):
        ks=(('base',0,(0,0,0)),('base',1,(0,0,0)),('base',2,(0,0,0)))
        p=Pending(Proposal(ks,'example'),ks,0,'hierarchy')
        self.assertEqual(permitted(p,[ks[2]],True),(ks[2],));self.assertEqual(permitted(p,[ks[2]],False),())
        self.assertEqual(permitted(p,[ks[1],ks[2]],True),ks[1:])
        self.assertEqual(permitted(p,[('base',3,(0,0,0))],True),())
    def test_interval_queries_retain_all_singletons_and_do_not_mutate_graph(self):
        m=self.u.bind(self.b);s=self.b.initial();g=Graph(m,s);fp=g.fingerprint();before=s.copy();ks=g.decision(s)[2]
        actions=self.atlas.actions(m,s,g,ks,scan_limit=64)
        self.assertTrue({(k,) for k in ks}<={a.sequence for a in actions});self.assertEqual(s,before);self.assertEqual(g.fingerprint(),fp)
        self.assertLessEqual(m.metrics['conditional_scans'],64)
        for a in actions:
            delta=Counter()
            for k in a.sequence:delta.update(dict(self.oracle.values[k]))
            self.assertTrue(all(s.totals.get(p,0)+v<=12 for p,v in delta.items()))
    def test_every_visited_domain_and_child_order_is_complete(self):
        calls=[]
        def observe(s,g,kind,p,keys,order,pending):
            self.assertEqual(g.domains,domains(self.oracle,self.b,s.totals,s.owned_base));self.assertEqual(set(keys),set(order));self.assertEqual(len(order),len(set(order)));calls.append(kind)
        r=search(self.b,self.u,self.atlas,142002,attempt_limit=30,seconds=None,fixed_mode='hierarchy',observer=observe)
        self.assertTrue(calls);self.assertTrue(self.oracle.replay(r,self.b))
    def test_unknown_cutoff_and_exact_parent_preservation(self):
        parent=self.b.initial();g=Graph(self.u.bind(self.b),parent);fp=g.fingerprint()
        r=search(self.b,self.u,self.atlas,142003,attempt_limit=1,seconds=None,fixed_mode='hierarchy')
        self.assertEqual(r['status'],'unknown_budget');self.assertEqual(r['attempted_base_placements'],1);self.assertIsNone(r['certificate'])
        self.assertEqual(parent,self.b.initial());self.assertEqual(g.fingerprint(),fp);self.assertTrue(self.oracle.replay(r,self.b))
    def test_global_dead_point_preempts_lookup(self):
        p=(18,-9,-9);b=Boundary('conditional-test-dead',self.b.required|{p},self.b.allowed,((p,11),))
        r=search(b,self.u,self.atlas,142004,seconds=None,fixed_mode='hierarchy')
        self.assertEqual(r['attempted_base_placements'],0);self.assertNotIn('conditional_scans',r['metrics'])
    def test_zero_policy_preserves_seeded_path_and_modes(self):
        a=search(self.b,self.u,self.atlas,142005,attempt_limit=30,seconds=None)
        b=search(self.b,self.u,self.atlas,142005,attempt_limit=30,seconds=None,policy=Policy())
        for f in ('status','state','execution','stats'):self.assertEqual(a[f],b[f])
    def test_learning_updates_preferences_and_keeps_full_domains(self):
        p=Policy();pairs=[]
        r=search(self.b,self.u,self.atlas,142006,attempt_limit=20,seconds=None,policy=p,learn=True,rollout=True,
            observer=lambda s,g,k,pt,keys,order,plan:pairs.append((keys,order)))
        self.assertEqual(p.updates,1);self.assertTrue(r['learning_choices']);self.assertTrue(all(set(a)==set(b) for a,b in pairs));self.assertTrue(self.oracle.replay(r,self.b))
    def test_new_training_evaluation_and_movable_boundaries_are_distinct(self):
        train=boundaries(True);evals=boundaries();families=moving_families()
        self.assertEqual((len(train),len(evals),len(families)),(7,4,2))
        self.assertTrue(set(b.required for b in train).isdisjoint(b.required for b in evals))
        self.assertTrue(set(b.required for b in declarations()).isdisjoint(b.required for b in evals))
        self.assertTrue(all(len({b.required for b in family})==len(family) for family in families))

if __name__=='__main__':unittest.main()
