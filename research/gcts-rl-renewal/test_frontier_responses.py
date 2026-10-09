import unittest
from pathlib import Path
import json
from turtle import Policy,Graph
from resident_regions import Universe
from boundary_macros import singleton
from boundary_responses import declarations,Atlas,Action,search as legacy
from frontier_responses import search,rank_unique,mode_features
from audit_boundary_macros import Oracle
from audit_boundary_responses import domains,matched_execution,normal

class FrontierResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bs=declarations();cls.b=cls.bs[0];cls.u=Universe((singleton(),),cls.b.allowed)
        p=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal/boundary-responses-001.json'
        cls.lib=json.loads(p.read_text())['library'];cls.oracle=Oracle(cls.b.allowed)
        cls.atlases={m:Atlas(cls.lib,cls.u,max_size=n) for m,n in (('small',4),('hierarchy',12))}
    def test_duplicate_actions_share_one_base_child_and_keep_all_fallbacks(self):
        k=('base',0,(0,0,0));q=('base',1,(0,0,0));r=('base',2,(0,0,0))
        a=Action((k,q),'first');b=Action((k,r),'second')
        order,chosen,n=rank_unique([k,q],[a,b,Action((q,)),Action((k,))])
        self.assertEqual(order,[k,q]);self.assertEqual(chosen[k],a);self.assertEqual(n,2)
        self.assertEqual(rank_unique([k,q],[a,Action((q,))],q)[0],[q,k])
    def test_missing_fallback_or_foreign_first_move_rejects(self):
        k=('base',0,(0,0,0));q=('base',1,(0,0,0))
        for actions in ([Action((k,))],[Action((k,)),Action((q,))]):
            with self.assertRaises(ValueError):rank_unique([q],actions)
    def test_base_reformulation_has_same_finite_work_path(self):
        a=legacy(self.b,self.u,132001,attempt_limit=50,seconds=None)
        b=search(self.b,self.u,self.atlases,132001,attempt_limit=50,seconds=None,fixed_mode='base')
        for f in ('status','state','execution','nodes','attempted_base_placements','backtracks'):self.assertEqual(a[f],b[f])
    def test_zero_policy_has_same_seeded_current_mode_and_path(self):
        a=search(self.b,self.u,self.atlases,132002,attempt_limit=50,seconds=None)
        b=search(self.b,self.u,self.atlases,132002,attempt_limit=50,seconds=None,policy=Policy())
        for f in ('status','state','execution','stats'):self.assertEqual(a[f],b[f])
    def test_every_visited_domain_matches_literal_inventory_and_unique_order(self):
        visits=[]
        def observe(s,g,kind,p,keys,order):
            self.assertEqual(g.domains,domains(self.oracle,self.b,s.totals,s.owned_base))
            self.assertEqual(set(keys),set(order));self.assertEqual(len(order),len(set(order)));visits.append(kind)
        r=search(self.b,self.u,self.atlases,132003,attempt_limit=35,seconds=None,fixed_mode='hierarchy',observer=observe)
        self.assertGreater(len(visits),0);self.assertTrue(self.oracle.replay(r,self.b))
        self.assertTrue(matched_execution(normal(r),self.b,self.oracle,normal(self.lib),True))
    def test_one_attempt_cutoff_is_unknown_and_parent_state_untouched(self):
        before=self.b.initial();fp=Graph(self.u.bind(self.b),before).fingerprint()
        r=search(self.b,self.u,self.atlases,132004,attempt_limit=1,seconds=None,fixed_mode='hierarchy')
        self.assertEqual(r['status'],'unknown_budget');self.assertEqual(r['attempted_base_placements'],1)
        self.assertEqual(before,self.b.initial());self.assertEqual(fp,Graph(self.u.bind(self.b),before).fingerprint())
        self.assertIsNone(r['certificate']);self.assertTrue(self.oracle.replay(r,self.b))
    def test_dead_global_point_prevents_any_response_lookup(self):
        from region_tiles import Boundary
        p=(18,-9,-9);b=Boundary('remote-dead',self.b.required|{p},self.b.allowed,((p,11),))
        r=search(b,self.u,self.atlases,132005,seconds=None,fixed_mode='hierarchy')
        self.assertEqual(r['attempted_base_placements'],0);self.assertNotIn('response_trace_tests',r['metrics'])
    def test_current_features_change_with_real_prefix_and_feedback(self):
        from collections import Counter
        m=self.u.bind(self.b);s=self.b.initial();g=Graph(m,s);keys=g.decision(s)[2]
        f=mode_features(s,g,keys,'small',Counter());k=keys[0];g.update(m,s,s.place(m.placement(k)))
        h=mode_features(s,g,g.decision(s)[2],'small',Counter({('small','closed'):2,('small','interrupted'):1}))
        self.assertNotEqual(f,h);self.assertEqual(h['mode:small:interruption'],.5)
    def test_learning_updates_preferences_without_removing_base_alternatives(self):
        p=Policy();orders=[]
        r=search(self.b,self.u,self.atlases,132006,attempt_limit=25,seconds=None,policy=p,learn=True,rollout=True,
                 observer=lambda s,g,k,pt,keys,order:orders.append((keys,order)))
        self.assertEqual(p.updates,1);self.assertTrue(r['learning_choices'])
        self.assertTrue(all(set(a)==set(b) for a,b in orders));self.assertTrue(self.oracle.replay(r,self.b))

if __name__=='__main__':unittest.main()
