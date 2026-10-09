import copy,itertools,random,unittest
import logic,wang,lazy_wang
from kernel_machine import Catalog,KernelMachine,language_stage,variable_name
import kernel_search as s
from audit_kernel_machine import audit_catalog
from turtle import Policy

class KernelMachineTests(unittest.TestCase):
    def test_all_kernel_rule_kinds_independently_enumerated(self):
        kinds=set()
        for p in s.problems():kinds.update(audit_catalog(p['catalog'])['kinds'])
        self.assertEqual(kinds,{'axiom','tautology','refl','instantiate','distribute','eq_subst','mp','generalize'})

    def test_all_short_commands_match_literal_machine_and_kernel(self):
        for p in s.problems():
            c=p['catalog'];m=KernelMachine(c,p['target'])
            rng=random.Random(998)
            commands=[x for n in range(3) for x in itertools.product(range(len(c.inferences)),repeat=n)]
            commands.extend(tuple(rng.randrange(len(c.inferences)) for _ in range(rng.randrange(3,9))) for _ in range(35))
            for sequence in commands:
                try:c.proof(sequence,p['target']);valid=True
                except ValueError:valid=False
                r=m.run(m.tokens(sequence),10000)
                self.assertNotEqual(r['status'],'unknown_step_budget')
                self.assertEqual(r['status']=='accept',valid,(p['id'],sequence))

    def test_proof_to_commands_and_nonfinal_target(self):
        p=s.problems(2)[1];c=p['catalog'];q=s.propose(c,p['target'],Policy(),11,8)
        proof=c.proof(q['commands'],p['target']);commands=c.commands_for_proof(proof,p['target'])
        self.assertEqual(KernelMachine(c,p['target']).run(KernelMachine(c,p['target']).tokens(commands))['status'],'accept')
        extra=next(i for i,r in enumerate(c.inferences) if r.witness.get('name')=='distractor_0')
        longer=c.proof(q['commands']+(extra,),p['target'])
        self.assertEqual(longer[-1]['formula'],p['target']);self.assertTrue(c.kernel.check(longer,p['target']))

    def test_capture_avoiding_instantiation_and_distribution_side_condition(self):
        x,y=logic.V('x'),logic.V('y');u=logic.All('x',logic.All('y',logic.Eq(x,y)))
        t=logic.Imp(u,logic.substitute(u[2],'x',y));k=logic.Kernel({}, {}, {})
        c=Catalog(k,(t,), (y,), ('x','y'),())
        self.assertIn('instantiate',audit_catalog(c)['kinds'])
        bad=logic.Imp(logic.All('x',logic.Imp(logic.Eq(x,y),logic.Eq(x,x))),logic.Imp(logic.Eq(x,y),logic.All('x',logic.Eq(x,x))))
        c=Catalog(k,(bad,),(),('x',),())
        self.assertFalse(any(r.witness['rule']=='distribute' for r in c.inferences));audit_catalog(c)

    def test_finite_syntax_enumeration_and_unicode_fairness(self):
        k=logic.Kernel({'c':0},{'P':0},{})
        goal=logic.Eq(logic.F('c'),logic.F('c'));c=language_stage(k,goal,3)
        self.assertIn(goal,c.index);self.assertIn(logic.Not(('pred','P',())),c.index)
        self.assertEqual(variable_name(0),'');self.assertEqual(variable_name(0x110000),'\U0010ffff')
        self.assertEqual(variable_name(0x110001),'\0\0')
        with self.assertRaises(ValueError):language_stage(k,goal,0)
        result=s.fair_search(k,goal,max_stage=1)
        self.assertEqual(result['status'],'unknown_outer_stage_budget')
        for syntax,length,height,nodes in s.bounds(7):self.assertGreaterEqual(nodes,128)

    def test_external_theory_and_tampered_inferences_are_rejected(self):
        p=s.problems()[0];c=p['catalog'];q=s.propose(c,p['target'],Policy(),0,8)
        self.assertTrue(c.kernel.check(c.proof(q['commands'],p['target']),p['target']))
        d=c.declaration();d=copy.deepcopy(d);d['axioms']={};untrusted=Catalog.from_declaration(d)
        with self.assertRaises(ValueError):untrusted.proof(q['commands'],p['target'])
        item=c.inferences[0];item.witness['formula']=('bot',)
        with self.assertRaises(ValueError):audit_catalog(c)

    def test_unknown_budget_padding_and_unavailable_premise(self):
        p=s.problems()[0];c=p['catalog'];m=KernelMachine(c,p['target'])
        mp=next(i for i,r in enumerate(c.inferences) if r.witness['rule']=='mp')
        self.assertEqual(m.run(m.tokens((mp,)))['status'],'reject')
        proposal=s.propose(c,p['target'],Policy(),0,8)
        self.assertEqual(m.run(m.tokens(proposal['commands'])+('_','_'))['status'],'accept')
        self.assertEqual(m.run(m.tokens(proposal['commands']),1)['status'],'unknown_step_budget')
        with self.assertRaises(ValueError):m.tokens((True,))

    def test_wang_unseeded_proof_and_preference_with_base_fallback(self):
        p=s.problems()[3];c=p['catalog'];m=KernelMachine(c,p['target']);length=2;height=64
        for extended in (False,True):
            r=lazy_wang.search(m.compiler,m.pattern(length),height,m.accepting_row(len(m.pattern(length))),node_limit=100000,seconds=10,extended=extended)
            self.assertTrue(r.get('verified'),r['status'])
            certificate=__import__('proof_search').pack(r)
            self.assertTrue(s.replay(c,p['target'],length,height,certificate))
            self.assertFalse(s.replay(c,logic.Eq(logic.V('x'),logic.V('x')),length,height,certificate))

if __name__=='__main__':unittest.main()
