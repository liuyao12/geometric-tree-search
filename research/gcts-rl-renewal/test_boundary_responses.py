import copy,json,unittest
from turtle import Graph,Policy,SYMMETRIES
from resident_regions import Universe
from boundary_macros import singleton
from boundary_responses import declarations,mine,Atlas,search,unpack,operation,composition,relocate,validate
from audit_boundary_responses import certify,normal,domains,matched_execution
from audit_boundary_macros import Oracle

class BoundaryResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bs=declarations(True);cls.b=cls.bs[1];cls.u=Universe((singleton(),),cls.b.allowed)
        cls.donors=[]
        for i,b in enumerate(cls.bs):
            r=search(b,cls.u,110000+i,seconds=None);r['problem']=b.identity;cls.donors.append(r)
        cls.lib=mine(cls.donors,{b.identity:b for b in cls.bs},cls.u.model)
        cls.atlas=Atlas(cls.lib,cls.u);cls.oracle=Oracle(cls.b.allowed)
    def test_every_response_and_disjoint_child_map_checks_literally(self):
        nodes,maps=certify(normal(self.lib));self.assertGreater(maps,0)
        self.assertEqual(len(nodes),len(self.lib['nodes']));self.assertGreater(len({len(seq) for seq,iv,dv,ov in nodes.values()}),2)
        validate(self.lib,self.u.model.base)
    def test_composition_is_associative_on_compatible_disjoint_operations(self):
        donor=max(self.donors,key=lambda r:len(r['state']['placements']));keys=[(o,tuple(tr)) for n,o,tr in donor['state']['placements'][:3]]
        totals={};rs=[]
        for key in keys:
            r=operation(self.u.model.base,(key,),totals);rs.append(relocate(r,tr=key[1]))
            for p,v in self.u.model.base.placement(key).occupancy:totals[p]=totals.get(p,0)+v
        a,b,c=rs;ab=composition(self.u.model.base,a,b);ab=relocate(ab,tr=a.sequence[0][1])
        bc=composition(self.u.model.base,b,c);bc=relocate(bc,tr=b.sequence[0][1])
        left=composition(self.u.model.base,ab,c);right=composition(self.u.model.base,a,bc)
        for name in ('sequence','incoming','delta','outgoing'):self.assertEqual(getattr(left,name),getattr(right,name))
    def test_missing_or_false_trace_and_overlapping_owners_reject(self):
        for mode in ('omit','bool','output','owners','map'):
            lib=normal(self.lib);r=next(r for r in lib['nodes'] if r['children'])
            if mode=='omit':r['incoming'].pop()
            if mode=='bool':r['incoming'][0][1]=True
            if mode=='output':r['outgoing'][0][1]+=1
            if mode=='owners':r['sequence'].append(r['sequence'][0])
            if mode=='map':r['children'][0][2]=[50,-25,-25]
            with self.assertRaises((ValueError,KeyError)):certify(lib)
    def test_full_singleton_domain_survives_and_proposals_do_not_mutate(self):
        m=self.u.bind(self.b);s=self.b.initial();g=Graph(m,s);before=s.copy();fp=g.fingerprint();keys=g.decision(s)[2]
        actions=self.atlas.actions(m,s,g,keys)
        self.assertTrue({(k,) for k in keys}<={a.sequence for a in actions});self.assertEqual(s,before);self.assertEqual(fp,g.fingerprint())
        self.assertEqual(g.domains,domains(self.oracle,self.b,s.totals,s.owned_base))
    def test_execution_and_interruptions_preserve_reference_scheduler(self):
        r=search(self.b,self.u,112001,atlas=self.atlas,seconds=None)
        self.assertTrue(self.oracle.replay(r,self.b));self.assertTrue(matched_execution(normal(r),self.b,self.oracle,normal(self.lib),True))
        self.assertEqual(r['status'],'finite_exact_region');self.assertIsNone(r['certificate'])
    def test_zero_weight_policy_is_same_semantic_search(self):
        a=search(self.b,self.u,112010,atlas=self.atlas,attempt_limit=50,seconds=None)
        b=search(self.b,self.u,112010,atlas=self.atlas,attempt_limit=50,seconds=None,policy=Policy())
        for f in ('status','state','execution','attempted_base_placements','nodes','backtracks'):self.assertEqual(a[f],b[f])
    def test_budget_exhaustion_is_unknown_and_replayable(self):
        r=search(self.b,self.u,112020,atlas=self.atlas,attempt_limit=1,seconds=None)
        self.assertEqual(r['status'],'unknown_budget');self.assertEqual(r['attempted_base_placements'],1)
        self.assertIsNone(r['certificate']);self.assertTrue(self.oracle.replay(r,self.b))
    def test_all_symmetries_preserve_local_response_and_child_interfaces(self):
        records=validate(self.lib,self.u.model.base);r=max(records.values(),key=lambda r:len(r.sequence))
        for g in SYMMETRIES:
            t=relocate(r,g,(7,-4,-3));a,b=[relocate(records[n],SYMMETRIES[o],tr) for n,o,tr in t.children]
            actual=composition(self.u.model.base,a,b)
            expected=operation(self.u.model.base,t.sequence,dict(t.incoming))
            for f in ('sequence','incoming','delta','outgoing'):self.assertEqual(getattr(actual,f),getattr(expected,f))
    def test_unknown_donors_cannot_supply_response_data(self):
        bad=[dict(r,status='unknown_budget') for r in self.donors]
        self.assertEqual(mine(bad,{b.identity:b for b in self.bs},self.u.model)['selected'],[])
    def test_matching_is_local_but_scheduling_still_sees_remote_obligations(self):
        r=unpack(next(n for n in self.lib['nodes'] if n['identity']==self.lib['selected'][0]));m=self.u.bind(self.b)
        s=self.b.initial();s.totals=dict(r.incoming)
        keys=[('base',r.sequence[0][0],(0,0,0))];g=Graph(m,s)
        actions=self.atlas.actions(m,s,g,keys);self.assertIn(r.sequence,tuple(tuple((o,tr) for n,o,tr in a.sequence) for a in actions))
        s2=s.copy();s2.totals[(50,-25,-25)]=12
        self.assertEqual(actions,self.atlas.actions(m,s2,g,keys))
        # The outside datum is never a cache key or a license to ignore global
        # scheduling. Add a remote required root with no admissible pose.
        from region_tiles import Boundary
        remote=(18,-9,-9)
        b=Boundary('remote-dead',self.b.required|{remote},self.b.allowed,((remote,11),));s3=b.initial();g3=Graph(self.u.bind(b),s3)
        self.assertEqual(g3.decision(s3)[0],'dead')
    def test_child_transaction_does_not_change_parent_and_literal_domains_agree(self):
        m=self.u.bind(self.b);s=self.b.initial();g=Graph(m,s);fp=g.fingerprint();before=s.copy()
        child=s.copy();cg=g.copy();k=cg.decision(child)[2][0];cg.update(m,child,child.place(m.placement(k)))
        self.assertEqual(cg.domains,domains(self.oracle,self.b,child.totals,child.owned_base))
        self.assertEqual(s,before);self.assertEqual(g.fingerprint(),fp);self.assertNotEqual(child,s)

if __name__=='__main__':unittest.main()
