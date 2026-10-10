"""Induction soundness, complete inventories and redundant point-mark checks."""
import copy,itertools,unittest
import logic as L
import induction_proof_catalogs as C,induction_proof_problems as P,induction_proof_tiles as T
import audit_induction_proofs as A
from audit_serialized_kernel import freeze
from run_semantic_proofs import declaration
from turtle import Graph

def abstract(rules,count=4,target=2):
    return dict(theory=dict(functions={},predicates={str(i):0 for i in range(count)},axioms={},schemas=[]),target=('pred',str(target),()),target_id=target,formulas=tuple(('pred',str(i),()) for i in range(count)),rules=[dict(inputs=list(i),output=o,recipe=dict(kind='abstract')) for i,o in rules],close_variables=[],configuration={})

class SupportTests(unittest.TestCase):
    def check_all_derivations(self,c,n):
        bound=T.supports(c);depth=T.depths(c);seen=0
        def visit(lines):
            nonlocal seen
            if len(lines)==n:return
            for r in c['rules']:
                domains=[[i for i,(fid,_) in enumerate(lines) if fid==f] for f in r['inputs']]
                for refs in itertools.product(*domains):
                    ancestors={len(lines)}
                    for i in refs:ancestors.update(lines[i][1])
                    f=r['output'];self.assertIsNotNone(bound['bound'][f]);self.assertLessEqual(bound['bound'][f],len(ancestors));self.assertLessEqual(depth['rank'][f],len(lines));seen+=1;visit(lines+[(f,ancestors)])
        visit([]);self.assertGreater(seen,0)
        A.support_certificate(freeze(c),freeze(bound));A.depth_certificate(freeze(c),freeze(depth))

    def test_shared_premises_must_not_be_added(self):
        c=abstract([((),0),((0,),1),((0,1),2),((0,0),3)])
        self.assertEqual(T.supports(c)['bound'],[1,2,3,2]);self.check_all_derivations(c,4)

    def test_disjoint_premises_count_separate_cells(self):
        c=abstract([((),0),((),1),((0,1),2),((2,),3)])
        self.assertEqual(T.supports(c)['bound'],[1,1,3,4]);self.check_all_derivations(c,4)

    def test_unreachable_cycles_and_repeated_formulas(self):
        c=abstract([((),0),((0,),0),((1,),2),((2,),1)],target=0)
        self.assertEqual(T.supports(c)['bound'],[1,None,None,None]);self.check_all_derivations(c,4)

    def test_mutated_cone_or_bound_is_rejected(self):
        c=abstract([((),0),((),1),((0,1),2)]);b=T.supports(c)
        bad=copy.deepcopy(b);bad['bound'][2]=4
        with self.assertRaisesRegex(ValueError,'ancestral-cell bound'):A.support_certificate(freeze(c),freeze(bad))
        bad=copy.deepcopy(b);bad['cones'][2]='0x0'
        with self.assertRaisesRegex(ValueError,'backward formula cones'):A.support_certificate(freeze(c),freeze(bad))

    def test_all_original_tiny_solutions_survive_markings(self):
        cases=[abstract([((),0),((),1),((0,1),2),((2,),2)],target=2),abstract([((),0),((0,),1),((0,1),2),((0,0),3)],target=2)]
        for c,n in itertools.product(cases,(3,4)):
            original=A.Points(c,n);marked=A.Points(c,n,'support');count=0
            def visit(ids):
                nonlocal count
                ds=original.domains(ids)
                if not ds:
                    count+=1;self.assertFalse(marked.domains(ids));return
                p=min(ds)
                for cid in sorted(ds[p]):visit(ids+[cid])
            visit([]);self.assertGreater(count,0)

    def test_incremental_graph_all_mark_only_updates_and_rollback(self):
        c=abstract([((),0),((),1),((0,1),2),((2,),2)],target=2)
        model=T.Model(c,4,support_certificate=T.supports(c));s=model.initial();g=Graph(model,s);oracle=A.Points(c,4,'support');before=g.fingerprint();snapshot=s.copy()
        def visit(state,graph,ids,depth):
            self.assertEqual(graph.domains,oracle.domains(ids))
            if depth==2:return
            for cid in sorted(graph.edges):
                child=state.copy();cg=graph.copy();cg.update(model,child,child.place(model.placement(cid)));visit(child,cg,ids+[cid],depth+1)
                self.assertEqual(graph.domains,oracle.domains(ids))
        visit(s,g,[],0);self.assertEqual(g.fingerprint(),before);self.assertEqual(s.__dict__,snapshot.__dict__)

class InductionGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem=P.problems()[0];cls.c=C.catalog(cls.problem['theory'],cls.problem['target'],4)

    def test_external_statements_match_independent_declaration(self):
        expected=A.external_cases()
        for p in P.problems():self.assertEqual(freeze({k:p[k] for k in expected[p['id']]}),expected[p['id']])

    def test_entire_catalog_is_independently_complete_and_sound(self):
        r=A.inventory(freeze(declaration(self.c)));self.assertEqual(r['induction_variables'],['n']);self.assertEqual(T.supports(self.c)['bound'][self.c['target_id']],7)

    def test_missing_rewrite_or_context_is_rejected(self):
        bad=copy.deepcopy(declaration(self.c));bad['rules'].pop(4)
        with self.assertRaisesRegex(ValueError,'every bounded'):A.inventory(freeze(bad))
        bad=copy.deepcopy(declaration(self.c));bad['configuration']['contexts'].pop()
        with self.assertRaisesRegex(ValueError,'entire grammar'):A.inventory(freeze(bad))

    def test_hypothesis_is_fixed_not_freely_instantiable(self):
        rules=[r for r in self.c['rules'] if r['recipe'].get('axiom')=='fixed-induction-hypothesis'];self.assertTrue(rules)
        for r in rules:self.assertFalse(r['recipe']['move']['bindings']);self.assertEqual(r['recipe']['context']['hypothesis'],('eq',L.F('add',L.F('zero'),L.V('n')),L.V('n')))

    def test_induction_requires_registered_schema(self):
        p=P.problems()[4];c=C.catalog(p['theory'],p['target'],4)
        self.assertFalse(any(r['recipe'].get('operation')=='induction' for r in c['rules']));self.assertIsNone(T.supports(c)['bound'][c['target_id']])

    def test_short_envelope_exhaustion_and_full_prefix_audit(self):
        r=T.search(self.c,6,support=True,seconds=15);self.assertEqual(r['status'],'exhausted_finite_proof_envelope');A.point_run(freeze(declaration(self.c)),6,freeze(r))

    def test_budget_cutoff_remains_unknown(self):
        r=T.search(self.c,7,support=True,seconds=15,attempt_limit=0);self.assertEqual(r['status'],'unknown_search_budget');A.point_run(freeze(declaration(self.c)),7,freeze(r))

if __name__=='__main__':unittest.main(verbosity=2)
