import copy,json,unittest
from pathlib import Path
from turtle import Graph,Policy
from region_tiles import Boundary,unpack_state
from boundary_macros import singleton,problems,search
from resident_regions import Universe
from compiled_macros import CompiledProposer
from viable_macros import ViableProposer
from audit_boundary_macros import Oracle
from audit_compiled_macros import literal_domains
from audit_failure_interfaces import check_dead_sample

class ViableMacroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Published prior-run regression fixture; never discovery/training data.
        docs=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'
        cls.old=json.loads((docs/'compiled-macros-001.json').read_text())
        cls.example=next(e for e in cls.old['proposal_pool_examples'] if any(o['kind']=='dead' for o in e['macro_outcomes']))
        cls.b=next(b for b in problems() if b.identity==cls.example['problem'])
        cls.u=Universe((singleton(),),cls.b.allowed);cls.compiled=CompiledProposer(cls.old['library'],cls.u)
        cls.oracle=Oracle(cls.b.allowed)
    def setup(self):
        m=self.u.bind(self.b);s=self.b.initial()
        for n,o,tr in self.example['context']:s.place(m.placement((n,o,tuple(tr))))
        return m,s,Graph(m,s)
    def test_known_dead_macro_drops_while_every_singleton_survives(self):
        m,s,g=self.setup();p=ViableProposer(self.compiled.fork(128));keys=g.decision(s)[2]
        raw=p.compiled.actions(m,s,g,keys);result=p.actions(m,s,g,keys)
        self.assertTrue({(k,) for k in keys}<=set(result));self.assertLess(len(result),len(raw))
        self.assertTrue(p.samples)
        for action in result:
            if len(action)==1:continue
            child=s.copy();cg=g.copy()
            for k in action:cg.update(m,child,child.place(m.placement(k)))
            self.assertNotEqual(cg.decision(child)[0],'dead')
    def test_contextual_empty_domain_certificate_is_independently_complete(self):
        m,s,g=self.setup();p=ViableProposer(self.compiled.fork(0));p.actions(m,s,g,g.decision(s)[2])
        sample=p.samples[0];self.assertTrue(check_dead_sample(sample,self.b,self.u,self.oracle))
        endpoint=unpack_state(m,self.b,sample['endpoint']);point=tuple(sample['certificate']['dead'])
        self.assertEqual(literal_domains(self.oracle,endpoint)[point],set())
    def test_proposal_checks_leave_parent_values_and_incidence_unchanged(self):
        m,s,g=self.setup();before=s.copy();fg=g.fingerprint();p=ViableProposer(self.compiled.fork(128))
        p.actions(m,s,g,g.decision(s)[2]);self.assertEqual(s,before);self.assertEqual(g.fingerprint(),fg)
    def test_cached_endpoint_result_is_versioned_by_full_state(self):
        m,s,g=self.setup();p=ViableProposer(self.compiled.fork(128));keys=g.decision(s)[2]
        a=p.actions(m,s,g,keys);b=p.actions(m,s,g,keys);self.assertEqual(a,b)
        self.assertEqual(m.metrics['viability_cache_hits'],1)
        s.marks[((90,-45,-45),'base')]=0;p.actions(m,s,g,keys)
        self.assertEqual(m.metrics['viability_cache_hits'],1)
    def test_certificate_changed_point_pose_or_envelope_rejects(self):
        m,s,g=self.setup();p=ViableProposer(self.compiled.fork(0));p.actions(m,s,g,g.decision(s)[2]);sample=p.samples[0]
        for field in ('point','pose','envelope'):
            bad=copy.deepcopy(sample)
            if field=='point':bad['certificate']['dead']=[90,-45,-45]
            elif field=='pose':bad['action']=(('base',True,(0,0,0)),*bad['action'][1:])
            else:bad['boundary']['allowed']=[]
            self.assertFalse(check_dead_sample(bad,self.b,self.u,self.oracle))
    def test_partial_certificate_does_not_refute_another_boundary(self):
        m,s,g=self.setup();p=ViableProposer(self.compiled.fork(0));p.actions(m,s,g,g.decision(s)[2])
        other=Boundary('different-required-set',frozenset({min(self.b.required)}),self.b.allowed)
        self.assertFalse(check_dead_sample(p.samples[0],other,self.u,self.oracle))
    def test_budget_interruption_cannot_install_an_endpoint_entry(self):
        m,s,g=self.setup();p=ViableProposer(self.compiled.fork(0));before=s.copy();fg=g.fingerprint()
        def stop():raise RuntimeError('cooperative cutoff')
        with self.assertRaises(RuntimeError):p.actions(m,s,g,g.decision(s)[2],stop)
        self.assertFalse(p.cache);self.assertEqual(s,before);self.assertEqual(g.fingerprint(),fg)
    def test_singleton_search_semantics_and_unknown_budget_remain(self):
        p=ViableProposer(self.compiled.fork(128));b=problems(True)[0]
        r=search(b,self.u,100000,attempt_limit=1,seconds=None,policy=Policy(),proposer=p)
        self.assertEqual(r['status'],'unknown_budget');self.assertIsNone(r['certificate'])
        self.assertEqual(r['attempted_base_placements'],1);self.assertTrue(self.oracle.replay(r,b))

if __name__=='__main__':unittest.main()
