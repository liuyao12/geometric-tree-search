import collections,copy,types,unittest
from unittest.mock import patch
import coarse_proof_tiles as M,audit_coarse_proofs as V
import semantic_proof_tiles as S,semantic_proof_catalogs as C,proof_cluster_problems as P,proof_clusters as H
from turtle import Graph,Placement,State
from audit_serialized_kernel import freeze
from run_semantic_proofs import declaration

def toy(target=1):return dict(target_id=target,rules=[dict(output=0,inputs=[]),dict(output=1,inputs=[]),dict(output=1,inputs=[0]),dict(output=0,inputs=[1])])
def solutions(model):
    out=set();visited=set()
    def visit(s):
        ids=tuple(sorted(s.selected))
        if ids in visited:return
        visited.add(ids)
        if not s.frontier():out.add(tuple(model.expansion(ids)));return
        for cid,t in model.cache.items():
            if s.legal(t):child=s.copy();child.place(t);visit(child)
    visit(model.initial());return out
def primitive_solutions(c,n):
    model=S.Model(c,n);out=set()
    def visit(s):
        slot=len(s.order)
        if slot==n:out.add(tuple(s.order));return
        for k in model.alignments(S.cell(slot)):
            if s.legal(model.placement(k)):child=s.copy();child.place(model.placement(k));visit(child)
    visit(model.initial());return out

class CoarseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=P.evaluation()[0];cls.c=C.equational(cls.p['theory'],cls.p['target'],cls.p['term_bound']);cls.lib=[]
        for p in P.donors():
            c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],cls.lib);cls.lib+=H.promote(c,r,p['length'],cls.lib,p['id'])['templates']
    def audit(self,r,lib=()):return V.point_run(freeze(declaration(self.c)),self.p['length'],freeze(r),freeze(lib))
    def test_solution_equivalence_all_widths(self):
        for target in (0,1):
            c=toy(target);expected=primitive_solutions(c,3)
            for w in (1,2,3):self.assertEqual(solutions(M.Model(c,3,w)),expected)
    def test_solution_equivalence_with_metatile(self):
        c=toy();members=((0,0,()),(1,2,(0,)));item=dict(members=members,level=1,template='test',instance={})
        with patch.object(H,'Index',return_value=types.SimpleNamespace(instances=[item],complete=True,seconds=0)):
            for w in (1,2,3):self.assertEqual(solutions(M.Model(c,3,w,['test'])),primitive_solutions(c,3))
    def test_exact_group_weights(self):
        for n in range(1,8):
            for w in (1,2,3):
                m=M.Model(toy(),n,w);self.assertEqual(set(m.slot_group),set(range(n)))
                for slots in m.groups:self.assertEqual(sum(12//len(slots) for _ in slots),12)
    def test_invalid_width(self):
        with self.assertRaises(ValueError):M.Model(toy(),3,5)
    def test_ownership_is_essential(self):
        m=M.Model(toy(),2,2);ids=[cid for cid,d in m.descriptions.items() if d['members'][0] in ((0,0,()),(0,1,()))]
        # Different logical outputs already disagree; use two identical rule
        # descriptions to isolate the missing-owner counterexample instead.
        c=dict(target_id=0,rules=[dict(output=0,inputs=[]),dict(output=0,inputs=[])]);m=M.Model(c,2,2);s=m.initial();s.place(m.cache[0]);self.assertFalse(s.legal(m.cache[1]))
        a=m.cache[0];b=m.cache[1];s=m.initial();s.place(Placement(a.key,a.occupancy,tuple((p,v) for p,v in a.marks if p[1]!=2),()))
        s.place(Placement(b.key,b.occupancy,tuple((p,v) for p,v in b.marks if p[1]!=2),()));self.assertFalse(s.frontier());self.assertEqual(len({k[0] for k in m.expansion(s.order)}),1)
    def test_fractional_residual_and_mark_only_ports(self):
        m=M.Model(toy(),3,2);s=m.initial();cid=next(cid for cid,d in m.descriptions.items() if d['members'][0]==(0,0,()));s.place(m.cache[cid]);self.assertEqual(s.totals[(0,0)],6);self.assertIn((0,0),s.frontier());self.assertTrue(all(p[1]==0 for p in s.frontier()))
    def test_distant_premise_mark(self):
        m=M.Model(toy(),3,2);cid=next(cid for cid,d in m.descriptions.items() if d['members'][0]==(2,2,(0,)));self.assertEqual(dict(m.cache[cid].marks)[(0,1)],0)
    def test_duplicate_constituent_rejected(self):
        m=M.Model(toy(),3)
        with self.assertRaises(ValueError):m.add(((0,0,()),(0,1,())),{})
    def test_internal_formula_conflict_rejected(self):
        m=M.Model(toy(),3)
        with self.assertRaises(ValueError):m.add(((0,1,()),(1,2,(0,))),{})
    def test_truncated_macro_inventory_rejected(self):
        with patch.object(H,'Index',return_value=types.SimpleNamespace(complete=False)):
            with self.assertRaises(ValueError):M.Model(toy(),3)
    def test_incremental_full_graph_and_rollback(self):
        for w in (1,2,3):
            m=M.Model(self.c,3,w,self.lib);points=V.Points(freeze(declaration(self.c)),3,w,freeze(self.lib));s=m.initial();g=Graph(m,s);old=(s.copy(),g.fingerprint())
            for cid in list(g.edges)[:10]:
                child=s.copy();cg=g.copy();cg.update(m,child,child.place(m.cache[cid]));ds=points.domains(child.order);self.assertEqual(cg.domains,ds);self.assertEqual(cg.edges,{k:{p for p,vs in ds.items() if k in vs} for k in set().union(*ds.values())})
            self.assertEqual(s,old[0]);self.assertEqual(g.fingerprint(),old[1])
    def test_all_macro_weights_marks_independently_reconstruct(self):
        for w in (1,2,3):
            m=M.Model(self.c,3,w,self.lib);v=V.Points(freeze(declaration(self.c)),3,w,freeze(self.lib));self.assertEqual(m.index_instances,len(v.items))
            for cid,t in m.cache.items():self.assertEqual(dict(t.occupancy),v.tiles[cid]['weights']);self.assertEqual(dict(t.marks),v.tiles[cid]['marks']);self.assertEqual(freeze(m.descriptions[cid]['members']),v.tiles[cid]['members'])
    def test_dead_before_forced(self):
        g=object.__new__(Graph);g.domains={(0,0):{1},(2,0):set()};self.assertEqual(g.decision(State())[0],'dead')
    def test_generation_before_degree(self):
        g=object.__new__(Graph);g.domains={(0,0):{1,2,3},(2,0):{4,5}};s=State(generations={(0,0):0,(2,0):1});self.assertEqual(g.decision(s)[1],(0,0))
    def test_fine_base_matches_original_work(self):
        a=S.search(self.c,3);b=M.search(self.c,3);self.assertEqual(a['placements'],b['placements']);self.assertEqual(a['attempts'],b['base_attempts']);self.audit(b)
    def test_coarse_positive_expands_and_audits(self):
        for w in (2,3):self.assertTrue(self.audit(M.search(self.c,3,w,self.lib),self.lib)['exact_solution'])
    def test_graph_pin_mutation_rejected(self):
        r=M.search(self.c,3);r['search_tree']['graph_sha256']='0'*64
        with self.assertRaises(ValueError):self.audit(r)
    def test_coarse_attempt_cutoff_replays(self):
        r=M.search(self.c,3,2,self.lib,attempt_limit=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertNotIn('decoded',r);self.assertEqual(self.audit(r,self.lib)['cutoffs'],1)
    def test_coarse_wall_entry_replays(self):
        r=M.search(self.c,3,seconds=0);self.assertEqual(self.audit(r)['cutoffs'],1)
    def test_finite_controls_all_point_models(self):
        p=P.evaluation()[-2];c=C.equational(p['theory'],p['target'],p['term_bound'])
        for w in (1,2,3):
            r=M.search(c,p['length'],w,self.lib);self.assertEqual(r['status'],'exhausted_finite_proof_envelope');V.point_run(freeze(declaration(c)),p['length'],freeze(r),freeze(self.lib))

class CSPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=P.evaluation()[0];cls.c=C.equational(cls.p['theory'],cls.p['target'],cls.p['term_bound']);cls.nested=P.evaluation()[5];cls.nc=C.equational(cls.nested['theory'],cls.nested['target'],cls.nested['term_bound'])
    def audit(self,r):return V.csp_run(freeze(declaration(self.c)),3,freeze(r))
    def test_support_bitsets_equal_direct_pairs(self):
        b=M.Binary(toy(),3)
        for i in range(3):
            for j in range(3):
                if i==j:continue
                for k,m in enumerate(b.marks[i]):
                    expected=sum(1<<q for q,other in enumerate(b.marks[j]) if all(p not in other or other[p]==v for p,v in m.items()));self.assertEqual(b.support(i,k,j),expected)
    def test_positive_ac_propagation_and_replay(self):
        r=M.csp_search(self.c,3);self.assertEqual(r['base_attempts'],0);self.assertGreater(r['removed_values'],0);self.assertTrue(self.audit(r)['exact_solution'])
    def test_single_variable_empty_initial_domain(self):
        c=toy(9);r=M.csp_search(c,1);self.assertEqual(r['status'],'exhausted_finite_proof_envelope');V.csp_run(freeze(c),1,freeze(r))
    def test_classical_finite_failure_not_global_nonprovability(self):
        p=P.evaluation()[-2];c=C.equational(p['theory'],p['target'],p['term_bound']);r=M.csp_search(c,p['length']);self.assertEqual(r['status'],'exhausted_finite_proof_envelope');V.csp_run(freeze(declaration(c)),p['length'],freeze(r))
    def test_classical_wall_open_queue(self):
        r=M.csp_search(self.c,3,seconds=0);self.assertEqual(self.audit(r)['cutoffs'],1);self.assertNotIn('decoded',r)
    def test_unsupported_deletion_mutation_rejected(self):
        r=M.csp_search(self.c,3);rev=r['search_tree']['revisions'];i,j,x=rev[0];rev[0]=(i,j,hex(int(x,16)^1))
        with self.assertRaises(ValueError):self.audit(r)
    def test_classical_missing_queue_suffix_rejected(self):
        r=M.csp_search(self.c,3);r['search_tree']['revisions'].pop()
        with self.assertRaises(ValueError):self.audit(r)
    def test_classical_final_assignment_mutation_rejected(self):
        r=M.csp_search(self.c,3);r['placements']=[]
        with self.assertRaises(ValueError):self.audit(r)
    def test_classical_mrv_branch_replays(self):
        r=M.csp_search(self.nc,5);self.assertGreater(r['base_attempts'],0);self.assertTrue(V.csp_run(freeze(declaration(self.nc)),5,freeze(r))['exact_solution']);r['search_tree']['slot']=4
        with self.assertRaises(ValueError):V.csp_run(freeze(declaration(self.nc)),5,freeze(r))
    def test_classical_trial_cutoff_replays(self):
        r=M.csp_search(self.nc,5,attempt_limit=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertEqual(V.csp_run(freeze(declaration(self.nc)),5,freeze(r))['cutoffs'],1)
    def test_classical_partial_tree_cannot_be_called_complete(self):
        r=M.csp_search(self.nc,5,attempt_limit=0);r['search_tree']=r['partial_tree'];r['partial_tree']=None
        with self.assertRaises(ValueError):V.csp_run(freeze(declaration(self.nc)),5,freeze(r))

if __name__=='__main__':unittest.main()
