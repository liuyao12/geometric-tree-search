"""Soundness/regression fixtures for the independent external proof checker."""
import copy,json,pathlib,sys,unittest
from external_prover_check import formula_text,entails,check_output,refute,replay_refutation,grounding
from external_prover_inputs import make_input,Symbols

F=formula_text

class Checks(unittest.TestCase):
    def checked(self,p,c):self.assertEqual(entails([F(x) for x in p],F(c))['status'],'checked')
    def unknown(self,p,c):self.assertEqual(entails([F(x) for x in p],F(c))['status'],'unknown')
    def test_equality_and_function_congruence(self):
        self.checked(['a=b','p(a)'],'p(b)')
        self.checked(['a=b','p(h(a))'],'p(h(b))')
        self.checked(['a=b','b=c'],'a=c')
        self.unknown(['a=b','p(c)'],'p(b)')
        self.unknown(['h(a)=h(b)'],'a=b')
    def test_quantifiers_and_scope(self):
        self.checked(['![X]:(p(X)=>q(X))','p(a)'],'q(a)')
        self.unknown(['?[X]:p(X)'],'p(a)')
        self.unknown(['p(a)'],'![X]:p(X)')
        self.checked(['![X]:p(X)'],'?[Y]:p(Y)')
        self.unknown(['![X]:?[Y]:(X!=Y)'],'$false')
        self.checked(['?[X]:![Y]:(X!=Y)'],'$false')
        self.unknown(['?[X]:p(X)'],'![X]:p(X)')
        self.checked([], '((![X]:(p(X)=>q(X)))=>(p(a)=>q(a)))')
    def test_classical_connectives(self):
        self.checked(['(p(a)|q(a))','~p(a)'],'q(a)')
        self.checked([], '(p(a)=>p(a))')
        self.checked(['p(a)','~p(a)'],'q(b)')
        self.unknown(['(p(a)|q(a))'],'p(a)')
    def test_replay_rejects_corruption(self):
        cs,_=grounding([F('a=b'),F('p(a)'),F('~p(b)')]);p=refute(cs)
        self.assertTrue(replay_refutation(cs,p))
        bad=copy.deepcopy(p);bad['tree']=['euf']
        with self.assertRaises(ValueError):replay_refutation(cs,bad)
        bad=copy.deepcopy(p);bad['tree']=['clause',0]
        with self.assertRaises(ValueError):replay_refutation(cs,bad)
    def test_injective_symbol_mapping(self):
        s=Symbols({'functions':{'a':0,'f0':0},'predicates':{'A':1,'a':1}})
        self.assertEqual(len(set(s.functions.values())),2)
        self.assertEqual(len(set(s.predicates.values())),2)
        self.assertFalse(set(s.functions.values())&set(s.predicates.values()))
    def test_calibration_trace_corruptions(self):
        r=pathlib.Path(__file__).resolve().parents[2]
        x=json.loads((r/'docs/research/gcts-rl-renewal/first-order-families-reader-001.json').read_text())
        c=x['training']['cases'][0];m=make_input({'spec':c['case'],'inventory':c['inventory']},False)
        p='.gcts-active/external-prover-20261011/calibration.p'
        text=(r/'.gcts-active/external-prover-20261011/calibration.tstp').read_text()
        self.assertEqual(check_output(text,m,p)['status'],'checked_complete_derivation')
        mutations=[text.replace('fof(a0, axiom, f0=f1','fof(a0, axiom, f0=f0'),
                   text.replace('~(p0(f1))','p0(f1)',1),
                   text.replace('c_0_6, c_0_7','c_0_6, missing'),
                   text.replace('(~p0(f1)), inference(split_conjunct','(p0(f1)), inference(split_conjunct'),
                   text.replace('($false), inference(cn','(p0(f2)), inference(cn'),
                   text.replace("calibration.p', a0","other.p', a0"),
                   text.replace('cnf(c_0_9','cnf(c_0_8'),
                   text.replace('($false), inference(cn','(p0(f0(f0))), inference(cn'),
                   text.replace('% SZS output end CNFRefutation','')]
        for i,t in enumerate(mutations):
            with self.subTest(i=i):
                with self.assertRaises(ValueError):check_output(t,m,p)
    def test_quantified_trace_and_printer_independence(self):
        r=pathlib.Path(__file__).resolve().parents[2]
        x=json.loads((r/'docs/research/gcts-rl-renewal/first-order-families-reader-001.json').read_text());c=x['training']['cases'][1]
        m=make_input({'spec':c['case'],'inventory':c['inventory']},False)
        p='.gcts-active/external-prover-20261011/calibration-1-False.p'
        text=(r/'.gcts-active/external-prover-20261011/calibration-1-False.tstp').read_text()
        self.assertEqual(check_output(text,m,p)['status'],'checked_complete_derivation')
        with self.assertRaises(ValueError):check_output(text.replace('p0(X1)=>p1(X1)','p0(f0)=>p1(X1)',1),m,p)
        # If a producer prints a different quantifier/body, direct AST checking
        # still rejects it rather than trusting a second call to the printer.
        bad=copy.deepcopy(m);bad['entries'][0]['formula']=['bot']
        with self.assertRaises(ValueError):check_output(text,bad,p)

if __name__=='__main__':unittest.main()
