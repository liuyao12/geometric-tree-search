import copy,itertools,json,unittest
import logic as L
import semantic_proof_catalogs as C,semantic_proof_problems as P,semantic_proof_tiles as S
import audit_semantic_proofs as A
from turtle import Graph
from serialized_kernel import canonical,problem_hash

class SemanticTests(unittest.TestCase):
    def chain(self):return C.fol(P.statements()[0]['theory'],P.statements()[0]['target'])
    def graph_equal(self,m,s,g):
        ds=A.domains(A.candidates(A.freeze(m.catalog),m.length),m.length,m.catalog['target_id'],s.order)
        expected={S.cell(i):keys for i,keys in ds.items()};self.assertEqual(g.domains,expected)
        edges={}
        for p,keys in expected.items():
            for key in keys:edges.setdefault(key,set()).add(p)
        self.assertEqual(g.edges,edges)
    def test_direct_proof_and_nonchronological_order(self):
        c=self.chain();r=S.search(c,5);self.assertEqual(r['status'],'finite_exact_proof_tiling');self.assertNotEqual([k[0] for k in r['placements']],list(range(5)))
        self.assertEqual(A.whole_replay(json.loads(canonical(r['decoded']['request'])),problem_hash(r['decoded']['request']))['status'],'accepted')
        A.audit_point_run(A.freeze(c),5,A.freeze(r));A.check_decoded(A.freeze(c),5,A.freeze(r))
    def test_complete_small_failure_tree(self):
        c=self.chain();r=S.search(c,4);self.assertEqual(r['status'],'exhausted_finite_proof_envelope');a=A.audit_point_run(A.freeze(c),4,A.freeze(r));self.assertEqual(a['full_tree_nodes'],r['nodes'])
    def test_budget_is_unknown(self):
        r=S.search(self.chain(),5,node_limit=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertIsNone(r['search_tree']);self.assertNotIn('decoded',r)
    def test_every_domain_update_and_exact_rollback(self):
        m=S.Model(self.chain(),4);s=m.initial();g=Graph(m,s);seen=0
        def visit(s,g,depth):
            nonlocal seen
            self.graph_equal(m,s,g);seen+=1
            if not depth:return
            before=(copy.deepcopy(s),g.fingerprint());kind,p,keys=g.decision(s)
            for key in keys:
                child=s.copy();cg=g.copy();cg.update(m,child,child.place(m.placement(key)));visit(child,cg,depth-1)
                self.assertEqual(s,before[0]);self.assertEqual(g.fingerprint(),before[1]);self.graph_equal(m,s,g)
        visit(s,g,4);self.assertGreater(seen,20)
    def test_marking_zero_is_assigned_and_missing_is_free(self):
        c=dict(formulas=(('pred','P',()),('pred','Q',())),rules=[dict(inputs=[],output=0),dict(inputs=[],output=1)],target_id=0)
        m=S.Model(c,2);s=m.initial();self.assertTrue(s.legal(m.placement((0,1,()))));self.assertFalse(s.legal(m.placement((1,1,()))))
        s.marks[S.output(0)]=0;self.assertFalse(s.legal(m.placement((0,1,()))));self.assertTrue(s.legal(m.placement((0,0,()))))
    def test_distant_mark_only_dependency_updates(self):
        m=S.Model(self.chain(),5);s=m.initial();g=Graph(m,s)
        candidate=next(k for k in m.cache if k[0]==4 and 0 in k[2] and s.legal(m.placement(k)))
        before=g.domains[S.cell(0)].copy();g.update(m,s,s.place(m.placement(candidate)));self.graph_equal(m,s,g);self.assertNotEqual(before,g.domains[S.cell(0)])
        self.assertIn(candidate,m.dependencies[S.output(0)]);self.assertNotIn(S.output(0),g.domains)
    def test_repeated_references_require_single_valued_marking(self):
        c=dict(rules=[dict(inputs=[0,1],output=2),dict(inputs=[0,0],output=2)],target_id=2);m=S.Model(c,3)
        self.assertNotIn((2,0,(0,0)),m.cache);self.assertIn((2,1,(0,0)),m.cache)
    def test_dead_before_forced(self):
        m=S.Model(dict(rules=[dict(inputs=[],output=0)],target_id=0),2);s=m.initial();g=Graph(m,s);s.marks[S.output(1)]=1;g.update(m,s,{S.output(1)});self.assertEqual(g.decision(s)[:2],('dead',S.cell(1)))
    def test_global_forced_before_branch(self):
        m=S.Model(dict(rules=[dict(inputs=[],output=0),dict(inputs=[],output=1)],target_id=0),3);s=m.initial();g=Graph(m,s);self.assertEqual(g.decision(s)[:2],('forced',S.cell(2)))
    def test_generation_precedes_domain_count(self):
        m=S.Model(dict(rules=[dict(inputs=[],output=0),dict(inputs=[],output=1),dict(inputs=[0],output=0)],target_id=0),3);s=m.initial();g=Graph(m,s)
        s.generations={S.cell(0):3,S.cell(1):0,S.cell(2):2};self.assertEqual(g.decision(s)[:2],('branch',S.cell(1)))
    def test_finite_logical_and_point_certificate_sets_agree(self):
        c=C.fol(dict(functions={},predicates=dict(P=0,Q=0),axioms=dict(p=('pred','P',()),pq=L.Imp(('pred','P',()),('pred','Q',()))),schemas=[]),('pred','Q',()),rounds=0);m=S.Model(c,3);point=set()
        def visit(s,g):
            kind,p,keys=g.decision(s)
            if kind=='empty':point.add(tuple(sorted(s.order)));return
            for key in keys:
                child=s.copy();cg=g.copy();cg.update(m,child,child.place(m.placement(key)));visit(child,cg)
        visit(m.initial(),Graph(m,m.initial()));logical=set()
        for keys in itertools.product(*(m.alignments(S.cell(i)) for i in range(3))):
            if c['rules'][keys[-1][1]]['output']!=c['target_id']:continue
            if all(tuple(c['rules'][keys[j][1]]['output'] for j in key[2])==tuple(c['rules'][key[1]]['inputs']) for key in keys):logical.add(keys)
        self.assertEqual(point,logical);self.assertTrue(point)
    def test_tampered_earlier_reference_rejected(self):
        c=self.chain();r=S.search(c,5);keys=copy.deepcopy(r['placements']);j=next(i for i,k in enumerate(keys) if k[2]);slot,rid,refs=keys[j];keys[j]=(slot,rid,(slot,)*len(refs))
        with self.assertRaises(ValueError):S.decode(c,keys,5)
    def test_tampered_marking_and_tree_rejected(self):
        c=self.chain();r=S.search(c,5);bad=copy.deepcopy(r);bad['samples'][0]['degrees'][str(S.cell(0))]+=1
        with self.assertRaises(ValueError):A.audit_point_run(A.freeze(c),5,A.freeze(bad))
        bad=copy.deepcopy(r);bad['search_tree']['children']=bad['search_tree']['children'][1:]
        with self.assertRaises(ValueError):A.audit_point_run(A.freeze(c),5,A.freeze(bad))
    def test_tampered_decoding_rejected(self):
        c=self.chain();r=S.search(c,5);bad=copy.deepcopy(r);bad['decoded']['request']['proof'][-1]['formula']=('pred','P',())
        with self.assertRaises(ValueError):A.check_decoded(A.freeze(c),5,A.freeze(bad))
    def test_complete_primitive_catalog_audit(self):
        for p in P.statements()[:7]:A.primitive_inventory(A.freeze(C.fol(p['theory'],p['target'],**p['configuration'])))
    def test_term_grammar_and_all_rewrite_edges(self):
        p=P.statements()[7];c=C.equational(p['theory'],p['target'],**p['configuration']);A.equation_inventory(A.freeze(c));r=S.search(c,p['length']);self.assertEqual(r['status'],'finite_exact_proof_tiling');A.check_decoded(A.freeze(c),p['length'],A.freeze(r))
    def test_variable_erasing_reverse_is_not_dropped(self):
        z=L.F('zero');x=L.V('x');theory=dict(functions=dict(zero=0,mul=2),predicates={},axioms=dict(MZ=L.All('x',L.Eq(L.F('mul',x,z),z))),schemas=[])
        c=C.equational(theory,L.Eq(z,L.F('mul',z,z)),3);a=A.equation_inventory(A.freeze(c));self.assertGreater(a['contextual_edges'],0)
        self.assertTrue(any(r['recipe'].get('move',{}).get('direction')==-1 for r in c['rules']));self.assertEqual(S.search(c,2)['status'],'finite_exact_proof_tiling')
    def test_unused_invalid_prefix_ending_assumption_is_checked(self):
        p=('pred','P',());q=('pred','Q',());d=dict(protocol='gcts-fol-1',theory=dict(functions={},predicates=dict(P=0,Q=0),axioms=dict(p=p),schemas=[]),target=p,blocks=[dict(name='bad',premises=[p],conclusion=p,proof=[dict(rule='tautology',formula=q),dict(rule='assumption',formula=p,index=0)])],proof=[dict(rule='axiom',formula=p,name='p')])
        raw=json.loads(canonical(d));self.assertEqual(A.whole_replay(raw,problem_hash(d))['status'],'rejected')
    def test_unused_invalid_root_prefix_ending_block_is_checked(self):
        p=('pred','P',());q=('pred','Q',());d=dict(protocol='gcts-fol-1',theory=dict(functions={},predicates=dict(P=0,Q=0),axioms=dict(p=p),schemas=[]),target=p,blocks=[dict(name='copy',premises=[p],conclusion=p,proof=[dict(rule='assumption',formula=p,index=0)])],proof=[dict(rule='axiom',formula=p,name='p'),dict(rule='tautology',formula=q),dict(rule='block',formula=p,name='copy',inputs=[0])])
        self.assertEqual(A.whole_replay(json.loads(canonical(d)),problem_hash(d))['status'],'rejected')
    def test_independent_external_statements_match(self):
        external=A.external_problems()
        for p in P.statements():self.assertEqual({k:A.freeze(p[k]) for k in external[p['id']]},A.freeze(external[p['id']]))
    def test_symbolic_same_grammar_valid_proof(self):
        c=self.chain();r=S.symbolic_search(c,5);self.assertEqual(r['status'],'symbolic_proof_found');A.check_decoded(A.freeze(c),5,A.freeze(r))

if __name__=='__main__':unittest.main()
