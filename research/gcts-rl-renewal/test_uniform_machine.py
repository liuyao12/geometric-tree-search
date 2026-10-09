import unittest,itertools
import wang,lazy_wang
from stack_program import encode,decode,run,compile_tm,equality_program
from uniform_stack_machine import UniformMachine
from uniform_examples import operation_cases,words,source_controls
from audit_uniform_machine import stack_reference,literal,source_reference,source_checkpoints,local_rule

class UniformMachineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.machine=UniformMachine()

    def test_all_short_binary_word_equalities(self):
        m=self.machine
        for left,right in itertools.product(words(2),repeat=2):
            expected='accept' if left==right else 'reject'
            actual=m.run(equality_program(),left,right,(2,2))
            self.assertEqual(actual['status'],expected)
            ref=stack_reference(encode(equality_program()),left,right,(2,2))
            self.assertEqual([{k:v for k,v in b.items() if k!='tm_step'} for b in actual['boundaries']],ref['trace'])

    def test_all_opcodes_pop_outcomes_directions_and_limits(self):
        for name,p,left,right,capacity,limit in operation_cases():
            with self.subTest(name=name):
                r=self.machine.run(p,left,right,capacity,limit=limit)
                ref=stack_reference(encode(p),left,right,capacity)
                observed=[{k:v for k,v in b.items() if k!='tm_step'} for b in r['boundaries']]
                self.assertEqual(observed,ref['trace'][:len(observed)])
                if r['status']!='unknown_step_budget': self.assertEqual(r['status'],ref['status'])
                self.assertEqual(literal(self.machine.declaration(),r['initial'],limit,encode(p),capacity)['final'],r['final'])

    def test_fixed_transition_table_for_different_programs(self):
        before=self.machine.fingerprint()
        self.machine.run((('accept',),),capacities=(0,0))
        self.machine.run(equality_program(),(1,),(0,),capacities=(1,1))
        self.assertEqual(before,self.machine.fingerprint())
        self.assertEqual(before,UniformMachine().fingerprint())

    def test_every_literal_row_matches_old_direct_tm_semantics(self):
        r=self.machine.run((('pushR1',1),('popR',3,3,2),('accept',),('reject',)),capacities=(0,1),keep_rows=True)
        self.assertEqual(r['status'],'accept')
        for a,b in zip(r['rows'],r['rows'][1:]): self.assertEqual(wang.direct_step(self.machine.compiler,a),b)

    def test_general_tm_translation_preserves_every_source_configuration(self):
        for name,source,translation,left,right in source_controls():
            reference=run(translation['program'],left,right)
            actual=source_reference(source)
            self.assertEqual(reference['status'],actual['status'])
            self.assertEqual(source_checkpoints(translation,reference['trace']),actual['trace'])

    def test_invalid_unused_symbol_code_rejects(self):
        c=wang.Compiler(('B','a','b'),('q','done'),{('q','B'):('done','B',0)},'done')
        t=compile_tm(c,'q')
        # 11 is outside this three-symbol code even though each bit is legal.
        r=run(t.program,(),(1,1))
        self.assertEqual(r['status'],'reject')

    def test_program_and_binary_data_are_strict(self):
        for program in ((('jump',True),),(('pushL0',-1),),(),(('oracle',),)):
            with self.assertRaises(ValueError): encode(program)
        for code in ('','Hp;','e;','e,,','gq;','H;;'):
            with self.assertRaises(ValueError): decode(code)
        with self.assertRaises(ValueError): self.machine.initial((('accept',),),(False,),capacities=(1,0))
        with self.assertRaises(ValueError): self.machine.initial((('accept',),),capacities=(True,0))
        with self.assertRaises(ValueError): self.machine.run((('accept',),),limit=-1)

    def test_decoder_roundtrip_and_unbounded_operands(self):
        for _,p,*_ in operation_cases(): self.assertEqual(decode(encode(p)),p)
        p=(('jump',10000),('accept',)); self.assertEqual(decode(encode(p)),p)

    def test_literal_validation_checks_unused_records_and_padding(self):
        m=self.machine; row=m.initial((('accept',),),(0,),capacities=(2,0))
        bad=list(row); start=4+len(encode((('accept',),))); bad[start:start+2]=['P','1']
        self.assertEqual(literal(m.declaration(),bad,10000)['status'],'reject')
        row=m.initial((('accept',),),capacities=(0,0)); bad=row[:3]+tuple('H;f;')+row[5:]
        self.assertEqual(literal(m.declaration(),bad,10000)['status'],'reject')

    def test_source_table_rejects_boolean_movement_and_duplicate_alphabet(self):
        for c in (wang.Compiler(('B','B'),('q','done'),{},'done'),
                  wang.Compiler(('B',),('q','done'),{('q','B'):('done','B',False)},'done')):
            with self.assertRaises(ValueError): compile_tm(c,'q')

    def test_symbolic_domains_equal_independent_complete_restrictions(self):
        m=self.machine; u=lazy_wang.Universe(m.compiler)
        allowed=('B','1',wang.head(m.fetch,'H'),wang.head('reject','0'))
        for north in (None,'B','1',wang.head('accept','L')):
            expected={t for t in itertools.product(allowed,repeat=3) if (n:=local_rule(m.declaration(),*t)) is not None and (north is None or n==north)}
            d=u.domain(allowed,allowed,allowed,north=north)
            self.assertEqual(d.count,len(expected)); self.assertEqual(set(d.options()),expected)

    def test_wang_transactions_restore_the_full_graph(self):
        m=self.machine; r=m.run((('accept',),),capacities=(0,0),keep_rows=True)
        graph=lazy_wang.Graph(lazy_wang.Universe(m.compiler),tuple((s,) for s in r['initial']),r['steps'],r['final'])
        before=graph.fingerprint(); mode,p,d=graph.decision(); self.assertIn(mode,('forced','branch'))
        graph.place(p,next(d.options())); graph.rollback(0)
        self.assertEqual(graph.fingerprint(),before)

if __name__=='__main__': unittest.main()
