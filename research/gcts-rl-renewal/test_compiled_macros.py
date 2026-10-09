import unittest
from turtle import Graph,Model
from cluster_tiles import make_type
from resident_regions import Universe
from region_tiles import Boundary
from boundary_macros import singleton,problems,Proposer,mine,search
from compiled_macros import CompiledProposer

class CompiledMacroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=problems(True)[0];cls.u=Universe((singleton(),),cls.b.allowed)
        cls.donor=search(cls.b,cls.u,95000,seconds=None)
        cls.library,_=mine([cls.donor],cls.u.model);cls.raw=Proposer(cls.library)
        cls.compiled=CompiledProposer(cls.library,cls.u)
    def setup(self,b=None):
        b=b or self.b;m=self.u.bind(b);s=b.initial();return m,s,Graph(m,s)
    def test_complete_envelope_patches_and_all_member_incidences(self):
        self.assertTrue(self.compiled.patches)
        for i,patch in enumerate(self.compiled.patches):
            self.assertTrue(set(patch)<=set(self.u.keys))
            self.assertEqual(len(set(patch)),len(patch))
            self.assertTrue(all(i in self.compiled.index[k] for k in patch))
        self.assertEqual(sum(map(len,self.compiled.index.values())),sum(map(len,self.compiled.patches)))
    def test_raw_compiled_shared_and_cached_actions_match_every_donor_prefix(self):
        m,s,g=self.setup();p=self.compiled.fork(128);plain=self.compiled.fork(0,False)
        for row in self.donor['execution']:
            keys=g.decision(s)[2];expected=self.raw.actions(m,s,g,keys)
            self.assertEqual(expected,plain.actions(m,s,g,keys));self.assertEqual(expected,p.actions(m,s,g,keys))
            key=tuple(row['placement'][:2])+(tuple(row['placement'][2]),)
            g.update(m,s,s.place(m.placement(key)))
    def test_cached_repeat_restores_all_parent_state_and_graph(self):
        m,s,g=self.setup();p=self.compiled.fork(4);before=s.copy();fg=g.fingerprint();keys=g.decision(s)[2]
        first=p.actions(m,s,g,keys);second=p.actions(m,s,g,keys)
        self.assertEqual(first,second);self.assertEqual(m.metrics['trace_cache_hits'],1)
        self.assertEqual(s,before);self.assertEqual(g.fingerprint(),fg)
    def test_cache_tracks_generations_and_assigned_zero_mark_only_data(self):
        m,s,g=self.setup();p=self.compiled.fork(4);keys=g.decision(s)[2]
        p.actions(m,s,g,keys);s.marks[((90,-45,-45),'base')]=0
        p.actions(m,s,g,keys);self.assertEqual(m.metrics['trace_cache_misses'],2)
        s.generations[min(s.required)]=2;p.actions(m,s,g,keys)
        self.assertEqual(m.metrics['trace_cache_misses'],3)
    def test_envelope_and_marking_versions_reject(self):
        t=make_type(Model(),'base',0,((0,(0,0,0)),),own_marking={(0,0,0):0})
        with self.assertRaises(ValueError):CompiledProposer(self.library,Universe((t,),self.b.allowed))
        m,s,g=self.setup();s.allowed_points=frozenset({min(self.b.allowed)})
        with self.assertRaises(ValueError):self.compiled.actions(m,s,g,g.decision(s)[2])
    def test_lane_forks_share_index_and_isolate_caches_and_boundary_gains(self):
        a=self.compiled.fork(3);b=self.compiled.fork(0,False)
        self.assertIs(a.patches,b.patches);self.assertIs(a.index,b.index)
        m,s,g=self.setup();a.actions(m,s,g,g.decision(s)[2])
        self.assertTrue(a.cache);self.assertFalse(b.cache);self.assertFalse(b.gains)
    def test_exact_base_attempt_trace_matches_with_and_without_compilation(self):
        a=search(self.b,self.u,95101,attempt_limit=15,seconds=None,proposer=self.raw)
        b=search(self.b,self.u,95101,attempt_limit=15,seconds=None,proposer=self.compiled.fork(128))
        for field in ('status','nodes','branches','forced','backtracks','attempted_base_placements','state','execution'):
            self.assertEqual(a[field],b[field],field)
    def test_cancelled_validation_never_installs_a_trace_entry(self):
        m,s,g=self.setup();p=self.compiled.fork(3);before=s.copy();fg=g.fingerprint();calls=0
        def stop():
            nonlocal calls
            calls+=1
            if calls==5:raise RuntimeError('cooperative interruption')
        with self.assertRaises(RuntimeError):p.actions(m,s,g,g.decision(s)[2],stop)
        self.assertFalse(p.cache);self.assertEqual(s,before);self.assertEqual(g.fingerprint(),fg)
    def test_owned_exterior_outside_compiled_envelope_uses_exact_fallback(self):
        outside=(0,(60,-30,-30));occ=Model().placement(outside).occupancy
        b=Boundary('owned-exterior',self.b.required,self.b.allowed,occ,owned=(outside,))
        m,s,g=self.setup(b);p=self.compiled.fork(3);keys=g.decision(s)[2]
        self.assertEqual(self.raw.actions(m,s,g,keys),p.actions(m,s,g,keys))
        self.assertEqual(m.metrics['compiled_exterior_fallbacks'],1);self.assertFalse(p.cache)

if __name__=='__main__':unittest.main()
