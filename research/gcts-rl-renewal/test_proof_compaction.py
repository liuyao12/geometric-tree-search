import copy,json,unittest
import logic
from proof_compaction import compact
from serialized_kernel import canonical,problem_hash
from audit_serialized_kernel import replay
from pathlib import Path

class ProofCompactionTests(unittest.TestCase):
    def request(self,proof,target=None,blocks=(),theory=None):
        return dict(protocol='gcts-fol-1',theory=theory or dict(functions={'zero':0},predicates={},axioms={},schemas=[]),blocks=list(blocks),proof=proof,target=target or proof[-1]['formula'])
    def compact(self,request):
        result=compact(canonical(request),problem_hash(request));self.assertEqual(result['status'],'accepted_compaction')
        self.assertEqual(replay(canonical(result['request']),problem_hash(request))['status'],'accepted');return result
    def test_identical_root_reuses_earlier_proof_and_drops_dead_lines(self):
        p=logic.Eq(logic.F('zero'),logic.F('zero'));q=logic.Eq(logic.V('x'),logic.V('x'))
        r=self.compact(self.request([dict(rule='refl',formula=p),dict(rule='refl',formula=q),dict(rule='refl',formula=p)]))
        self.assertEqual(len(r['request']['proof']),1);self.assertEqual(r['graphs'][0]['old_to_new'],[0,None,0])
    def test_only_actual_rule_references_are_renumbered(self):
        p=logic.Eq(logic.F('zero'),logic.F('zero'));q=logic.Eq(logic.V('x'),logic.V('x'));u=logic.All('x',p)
        lines=[dict(rule='refl',formula=q),dict(rule='refl',formula=p),dict(rule='generalize',formula=u,variable='x',source=1),dict(rule='distribute',formula=logic.Imp(logic.All('x',logic.Imp(p,p)),logic.Imp(p,logic.All('x',p))),variable='x',antecedent=p,consequent=p)]
        # Distribution's antecedent is a formula, never a line index.
        r=self.compact(self.request(lines));self.assertEqual(len(r['request']['proof']),1);self.assertEqual(r['request']['proof'][0]['antecedent'],json.loads(canonical(p)))
        r=self.compact(self.request(lines[:-1]));self.assertEqual(r['request']['proof'][-1]['source'],0)
    def test_mp_edges_preserve_dependency_order(self):
        p=logic.Eq(logic.F('zero'),logic.F('zero'));q=logic.All('x',p);imp=logic.Imp(p,q)
        theory=dict(functions={'zero':0},predicates={},axioms={'p':p,'pq':imp},schemas=[])
        lines=[dict(rule='refl',formula=p),dict(rule='refl',formula=p),dict(rule='axiom',formula=imp,name='pq'),dict(rule='mp',formula=q,antecedent=1,implication=2)]
        r=self.compact(self.request(lines,theory=theory));self.assertEqual(len(r['request']['proof']),3);self.assertEqual(r['request']['proof'][-1]['antecedent'],0)
    def test_unused_invalid_line_cannot_be_erased_into_acceptance(self):
        p=logic.Eq(logic.F('zero'),logic.F('zero'));d=self.request([dict(rule='refl',formula=['bot']),dict(rule='refl',formula=p)])
        r=compact(canonical(d),problem_hash(d));self.assertEqual(r['status'],'rejected');self.assertNotIn('request',r)
    def test_invalid_duplicate_formula_derivation_cannot_be_hidden(self):
        p=logic.Eq(logic.F('zero'),logic.F('zero'));d=self.request([dict(rule='refl',formula=p),dict(rule='axiom',formula=p,name='invented')])
        self.assertEqual(compact(canonical(d),problem_hash(d))['status'],'rejected')
    def test_unused_invalid_block_is_checked_before_removal(self):
        p=logic.Eq(logic.F('zero'),logic.F('zero'));b=dict(name='bad',premises=[],conclusion=['bot'],proof=[dict(rule='refl',formula=['bot'])]);d=self.request([dict(rule='refl',formula=p)],blocks=[b])
        self.assertEqual(compact(canonical(d),problem_hash(d))['status'],'rejected')
    def test_unused_valid_block_is_removed_after_validation(self):
        p=logic.Eq(logic.F('zero'),logic.F('zero'));b=dict(name='unused',premises=[],conclusion=p,proof=[dict(rule='refl',formula=p)])
        r=self.compact(self.request([dict(rule='refl',formula=p)],blocks=[b]));self.assertEqual(r['removed_blocks'],['unused'])
    def test_block_premises_and_assumption_indices_are_fixed(self):
        p=logic.Eq(logic.V('x'),logic.V('x'));q=logic.Eq(logic.F('zero'),logic.F('zero'));theory=dict(functions={'zero':0},predicates={},axioms={'q':q},schemas=[])
        b=dict(name='premises',premises=[p,q],conclusion=q,proof=[dict(rule='assumption',formula=p,index=0),dict(rule='assumption',formula=q,index=1)])
        d=self.request([dict(rule='refl',formula=p),dict(rule='axiom',formula=q,name='q'),dict(rule='block',formula=q,name='premises',inputs=[0,1])],blocks=[b],theory=theory)
        # Make the block conclusion different from the root's earlier q.
        b['conclusion']=logic.All('y',q);b['proof'].append(dict(rule='generalize',formula=b['conclusion'],source=1,variable='y'));d['proof'][-1]['formula']=b['conclusion'];d['target']=b['conclusion']
        r=self.compact(d);self.assertEqual(r['request']['blocks'][0]['premises'],json.loads(canonical([p,q])));self.assertEqual(r['request']['blocks'][0]['proof'][0]['index'],1)
    def test_unused_premise_still_blocks_generalization(self):
        p=logic.Eq(logic.V('x'),logic.V('x'));q=logic.Eq(logic.F('zero'),logic.F('zero'));u=logic.All('x',q)
        b=dict(name='eigen',premises=[p],conclusion=u,proof=[dict(rule='refl',formula=q),dict(rule='generalize',formula=u,source=0,variable='x')]);d=self.request([dict(rule='refl',formula=q)],blocks=[b])
        self.assertEqual(compact(canonical(d),problem_hash(d))['status'],'rejected')
    def test_external_theorem_pin_and_step_resources_remain_guards(self):
        p=logic.Eq(logic.F('zero'),logic.F('zero'));d=self.request([dict(rule='refl',formula=p)])
        self.assertEqual(compact(canonical(d),'0'*64)['status'],'rejected')
        r=compact(canonical(d),problem_hash(d),max_work=0);self.assertTrue(r['status'].startswith('unknown'));self.assertNotIn('request',r)
    def test_no_alpha_equivalence_or_numeric_coercion_is_assumed(self):
        p=logic.Eq(logic.V('x'),logic.V('x'));q=logic.Eq(logic.V('y'),logic.V('y'))
        d=self.request([dict(rule='refl',formula=p),dict(rule='generalize',formula=logic.All('x',p),source=0,variable='x'),dict(rule='refl',formula=q),dict(rule='generalize',formula=logic.All('y',q),source=2,variable='y')])
        r=self.compact(d);self.assertEqual(r['graphs'][0]['aliases'],[0,1,2,3])
        bad=copy.deepcopy(d);bad['proof'][-1]['source']=True;self.assertEqual(compact(canonical(bad),problem_hash(bad))['status'],'rejected')
    def test_large_learned_case_preserves_its_induction_and_exact_target(self):
        docs=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal';d=json.loads((docs/'learned-proof-tape-cutoff-001.json').read_text())['request'];r=self.compact(d)
        self.assertEqual(len(r['request']['blocks'][0]['proof']),28);self.assertTrue(any(l['rule']=='induction' for l in r['request']['blocks'][0]['proof']));self.assertEqual(r['request']['target'],d['target'])
    def test_idempotence_on_actual_learned_hierarchy(self):
        docs=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal';d=json.loads((docs/'learned-proof-blocks-001.json').read_text())['discovery'][-1]['result']['request'];first=self.compact(d)['request'];second=self.compact(first)['request'];self.assertEqual(first,second)

if __name__=='__main__':unittest.main()
