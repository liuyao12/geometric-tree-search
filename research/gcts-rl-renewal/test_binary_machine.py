import itertools,unittest
import wang,lazy_wang
from stack_program import run,equality_program
from binary_program import encode,decode,workspace
from binary_stack_machine import BinaryMachine
from uniform_examples import words,operation_cases,source_controls
from audit_binary_machine import literal,program,stack_reference
from audit_uniform_machine import source_reference,source_checkpoints

class BinaryMachineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.machine=BinaryMachine()
    def assert_run(self,p,l=(),r=(),c=(4,4),next_links=True,limit=1000000):
        actual=self.machine.run(p,l,r,c,next_links=next_links,limit=limit);reference=run(p,l,r,capacities=c)
        observed=[{k:v for k,v in b.items() if k!='tm_step'} for b in actual['boundaries']]
        self.assertEqual(observed,reference['trace'][:len(observed)])
        if not actual['status'].startswith('unknown'):self.assertEqual(actual['status'],reference['status'])
        independent=literal(self.machine.declaration(),actual['initial'],limit,encode(p,next_links),c,actual['workspace_capacity'])
        for field in ('status','steps','final','boundaries'):self.assertEqual(independent[field],actual[field])
        return actual
    def test_encoding_roundtrip(self):
        for _,p,l,r,c,limit in operation_cases():
            for n in (False,True):self.assertEqual(decode(encode(p,n)),p)
        self.assertEqual(decode('H;g<1111;'),(('accept',),('jump',-14)))
    def test_noncanonical_programs(self):
        for code in ('','H','g;','g1;','g>01;','g<0;','gn0;','f>0,>1;','Hp;','H;;','H;g>01;'):
            with self.assertRaises(ValueError):decode(code)
            with self.assertRaises(ValueError):program(code)
    def test_strict_data(self):
        for p in ((('jump',True),),(('jump',-1),),[('accept',)],(('unknown',),)):
            with self.assertRaises(ValueError):encode(p)
        for n in (0,1,None,'yes'):
            with self.assertRaises(ValueError):encode((('accept',),),n)
        for w in (True,-1,.5):
            with self.assertRaises(ValueError):self.machine.initial((('accept',),),workspace_capacity=w)
        for l in ((True,),(2,),[1]):
            with self.assertRaises(ValueError):self.machine.initial((('accept',),),left=l)
        for n in (True,-1):
            with self.assertRaises(ValueError):self.machine.run((('accept',),),limit=n)
    def test_operation_branches(self):
        for next_links in (False,True):
            for name,p,l,r,c,limit in operation_cases():
                with self.subTest(name=name,next_links=next_links):self.assert_run(p,l,r,c,next_links,limit)
    def test_short_word_equality(self):
        for l,r in itertools.product(words(2),repeat=2):
            for n in (False,True):self.assertEqual(self.assert_run(equality_program(),l,r,(2,2),n)['status'],'accept' if l==r else 'reject')
    def test_full_source_configurations(self):
        for name,source,t,l,r in source_controls():
            expected=source_reference(source)
            for n in (False,True):
                with self.subTest(name=name,next_links=n):
                    z=self.machine.run(t['program'],l,r,(max(32,len(l))+16,max(32,len(r))+16),next_links=n,limit=20000000)
                    self.assertEqual(z['status'],expected['status']);self.assertEqual(source_checkpoints(t,z['boundaries']),expected['trace'])
    def test_workspace_cutoff_and_next_link(self):
        p=(('pushL1',1),('accept',))
        self.assertEqual(workspace(p,True),0);self.assertEqual(workspace(p,False),1)
        a=self.machine.run(p,capacities=(1,0),workspace_capacity=0,next_links=True)
        b=self.machine.run(p,capacities=(1,0),workspace_capacity=0,next_links=False)
        self.assertEqual(a['status'],'accept');self.assertEqual(b['status'],'unknown_workspace_bound')
        self.assertEqual(a['boundaries'][-1]['left'],(1,))
    def test_raw_programs_and_layout(self):
        d=self.machine.declaration();row=self.machine.initial((('accept',),),capacities=(0,0),workspace_capacity=4);suffix=row[row.index('A'):]
        for code,status in [('H;g<1111;','accept'),('g<1;','reject'),('gn;','reject'),('H;g>01;','reject')]:
            initial=row[:3]+tuple(code)+suffix
            self.assertEqual(literal(d,initial,10000)['status'],status)
        bad=list(self.machine.initial((('accept',),),capacities=(0,0),workspace_capacity=1));bad[bad.index('A')+1]='0'
        self.assertEqual(literal(d,bad,10000)['status'],'reject')
        short=row[:3]+tuple('g<1;')+('A','#','|','$','B','B')
        self.assertEqual(literal(d,short,10000)['status'],'unknown_workspace_bound')
    def test_large_forward_backward_and_borrow(self):
        for size in (31,32,128,256):
            p=(('jump',size),)+(('accept',),)*(size-1)+(('jump',0),)
            for n in (False,True):
                z=self.assert_run(p,c=(0,0),next_links=n,limit=100000)
                self.assertEqual(z['status'],'unknown_step_budget')
                self.assertTrue(all(b['pc'] in (0,size) for b in z['boundaries']))
    def test_self_loop_and_unused_target(self):
        self.assertEqual(self.assert_run((('jump',0),),c=(0,0),limit=1000)['status'],'unknown_step_budget')
        self.assertEqual(self.assert_run((('accept',),('jump',10000)),c=(0,0))['status'],'accept')
    def test_fixed_table(self):
        before=self.machine.fingerprint()
        for n in (False,True):self.machine.run((('pushR1',1),('accept',)),next_links=n)
        self.assertEqual(self.machine.fingerprint(),before);self.assertEqual(BinaryMachine().fingerprint(),before)
    def test_literal_radius_one_rows(self):
        for n in (False,True):
            z=self.machine.run((('pushR1',1),('accept',)),keep_rows=True,next_links=n)
            for a,b in zip(z['rows'],z['rows'][1:]):self.assertEqual(wang.direct_step(self.machine.compiler,a),b)
    def test_symbolic_domains(self):
        u=lazy_wang.Universe(self.machine.compiler);allowed=('B','0','n',wang.head(self.machine.start,'L'),wang.head('workspace-bound','#'))
        expected=[t for t in itertools.product(allowed,repeat=3) if self.machine.compiler.rule(*t) is not None]
        d=u.domain(allowed,allowed,allowed);self.assertEqual(d.count,len(expected));self.assertEqual(set(d.options()),set(expected))
    def test_graph_transaction(self):
        m=self.machine;z=m.run((('accept',),),capacities=(0,0),keep_rows=True);u=lazy_wang.Universe(m.compiler);g=lazy_wang.Graph(u,[(s,) for s in z['initial']],z['steps'],m.accepting_row(z['width']),extended=True)
        before=(g.marks.copy(),g.selected.copy(),g.order.copy(),g.tile_generations.copy(),{p:(d.blocks,d.a,d.b,d.c,d.north,d.count) for p,d in g.domains.items()},g.dead.copy(),g.forced.copy(),g.trail.copy())
        _,p,d=g.decision();checkpoint=len(g.trail);g.place(p,next(d.options()));g.rollback(checkpoint)
        after=(g.marks.copy(),g.selected.copy(),g.order.copy(),g.tile_generations.copy(),{p:(d.blocks,d.a,d.b,d.c,d.north,d.count) for p,d in g.domains.items()},g.dead.copy(),g.forced.copy(),g.trail.copy())
        self.assertEqual(before,after)

if __name__=='__main__':unittest.main()
