import copy,itertools,json,unittest
import logic as L
import proof_clusters as H,proof_cluster_problems as P
import semantic_proof_catalogs as C,semantic_proof_tiles as S
import audit_semantic_proofs as A
from turtle import Graph
from serialized_kernel import canonical,problem_hash

class ClusterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.donors=[];cls.library=[]
        for p in P.donors():
            c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],cls.library);promotion=H.promote(c,r,p['length'],cls.library,p['id']);cls.donors.append((p,c,r,promotion));cls.library+=promotion['templates']
    def evaluation(self,i=0):
        p=P.evaluation()[i];return p,C.equational(p['theory'],p['target'],p['term_bound'])
    def test_empty_library_fresh_donor_and_checked_hierarchy(self):
        self.assertFalse(self.donors[0][2]['solution_transactions']);self.assertTrue(self.donors[1][2]['solution_transactions']);self.assertTrue(any(t['level']==2 for t in self.library));self.assertEqual(H.validate_library(P.donors()[0]['theory'],self.library)['status'],'accepted')
    def test_all_mined_windows_have_recorded_source_members(self):
        for p,c,r,promotion in self.donors:
            path=H.chain(c,r['placements'],p['length']);moves=[k for k in path if c['rules'][k[1]]['recipe']['kind']=='block']
            for template in promotion['templates']:
                a,b=template['source']['window'];self.assertEqual(template['source']['members'],moves[a:b]);self.assertEqual(template['source']['certificate_sha256'],H.digest(r['decoded']['request']))
    def test_every_library_definition_independently_expands(self):
        target=L.Imp(('bot',),('bot',));request=dict(protocol='gcts-fol-1',theory=P.donors()[0]['theory'],target=target,proof=[dict(rule='tautology',formula=target)],blocks=H.definitions(self.library));self.assertEqual(A.whole_replay(json.loads(canonical(request)),problem_hash(request))['status'],'accepted')
    def test_cluster_expansion_keys_are_existing_base_types(self):
        p,c=self.evaluation();m=S.Model(c,p['length']);index=H.Index(c,p['length'],self.library)
        self.assertTrue(index.instances)
        for item in index.instances:
            self.assertEqual(len(item['members']),len(set(item['members'])))
            for key in item['members']:self.assertIn(key,m.cache)
    def test_same_base_universe_with_or_without_library(self):
        p,c=self.evaluation();a=H.search(c,p['length']);b=H.search(c,p['length'],self.library)
        self.assertEqual(a['candidate_universe'],b['candidate_universe']);self.assertEqual(a['samples'][0],b['samples'][0]);self.assertLess(b['nodes'],a['nodes'])
    def test_transaction_obeys_global_decisions_and_domains(self):
        p,c=self.evaluation();m=S.Model(c,p['length']);s=m.initial();g=Graph(m,s);kind,point,keys=g.decision(s);g.update(m,s,s.place(m.placement(keys[0])));index=H.Index(c,p['length'],self.library);kind,point,keys=g.decision(s);offered,count=index.offered(m,s,g,point);trace,child,cg=H.execute(m,s,g,offered[0]);self.assertEqual(trace['status'],'accepted_cluster')
        universe=A.candidates(A.freeze(c),p['length']);order=list(s.order)
        for step in trace['steps']:
            ds=A.domains(universe,p['length'],c['target_id'],order);kind,slot,keys=A.decision(ds);self.assertEqual(step['kind'],kind);self.assertEqual(step['point'],S.cell(slot));self.assertIn(step['key'],keys);order.append(step['key'])
        self.assertEqual(order,child.order);self.assertEqual(cg.domains,{S.cell(i):keys for i,keys in A.domains(universe,p['length'],c['target_id'],order).items()})
    def test_transaction_does_not_mutate_parent_on_success_or_failure(self):
        p,c=self.evaluation();m=S.Model(c,p['length']);s=m.initial();g=Graph(m,s);before=(copy.deepcopy(s),g.fingerprint());index=H.Index(c,p['length'],self.library)
        for item in index.instances:
            H.execute(m,s,g,item);self.assertEqual(s,before[0]);self.assertEqual(g.fingerprint(),before[1])
    def test_duplicate_constituent_rejected(self):
        p,c=self.evaluation();m=S.Model(c,p['length']);s=m.initial();g=Graph(m,s);key=(0,0,());trace,child,cg=H.execute(m,s,g,dict(members=[key,key]));self.assertEqual(trace['status'],'rejected_duplicate_constituent');self.assertIsNone(child)
    def test_budget_during_transaction_is_unknown_and_rolls_back(self):
        p,c=self.evaluation();m=S.Model(c,p['length']);s=m.initial();g=Graph(m,s);index=H.Index(c,p['length'],self.library);before=(copy.deepcopy(s),g.fingerprint())
        def tick():raise H.Budget()
        trace,child,cg=H.execute(m,s,g,index.instances[0],tick);self.assertEqual(trace['status'],'unknown_transaction_budget');self.assertEqual(s,before[0]);self.assertEqual(g.fingerprint(),before[1])
    def test_attempt_limit_zero_is_unknown(self):
        p,c=self.evaluation();r=H.search(c,p['length'],self.library,attempt_limit=0);self.assertEqual(r['status'],'unknown_search_budget');self.assertEqual(r['base_attempts'],0);self.assertIsNone(r['search_tree'])
    def test_truncated_proposal_index_keeps_singleton_fallback(self):
        p,c=self.evaluation();r=H.search(c,p['length'],self.library,index_limit=0);self.assertEqual(r['status'],'finite_exact_proof_tiling');self.assertFalse(r['index_complete']);self.assertEqual(r['index_instances'],0);self.assertFalse(r['solution_transactions'])
    def test_zero_proposal_pool_keeps_all_base_paths(self):
        p,c=self.evaluation();plain=H.search(c,p['length']);r=H.search(c,p['length'],self.library,proposal_limit=0);self.assertEqual(r['placements'],plain['placements']);self.assertEqual(r['nodes'],plain['nodes'])
    def test_short_envelope_does_not_gain_extra_proof_cells(self):
        p,c=self.evaluation(7)
        for library in ([],self.library):self.assertEqual(H.search(c,p['length'],library)['status'],'exhausted_finite_proof_envelope')
    def test_rank_only_keeps_singleton_semantics(self):
        p,c=self.evaluation();r=H.search(c,p['length'],self.library,mode='rank');self.assertEqual(r['status'],'finite_exact_proof_tiling');self.assertFalse(r['solution_transactions']);self.assertEqual(r['stats'].get('proposal_trials',0),0)
    def test_nested_certificate_independent_replay(self):
        p,c=self.evaluation(5);r=H.search(c,p['length'],self.library);h=H.hierarchical_certificate(c,r,p['length'],self.library);self.assertTrue(h['transactions_used']);self.assertEqual(A.whole_replay(json.loads(canonical(h['request'])),problem_hash(r['decoded']['request']))['status'],'accepted')
    def test_hierarchy_interface_and_target_tampers_reject(self):
        p,c=self.evaluation();r=H.search(c,p['length'],self.library);h=H.hierarchical_certificate(c,r,p['length'],self.library);bad=copy.deepcopy(h['request']);bad['blocks'][-1]['premises']=[];self.assertEqual(A.whole_replay(json.loads(canonical(bad)),problem_hash(r['decoded']['request']))['status'],'rejected')
    def test_base_engine_agrees_with_previous_direct_solver(self):
        p,c=self.evaluation();a=H.search(c,p['length']);b=S.search(c,p['length']);self.assertEqual(a['placements'],b['placements']);self.assertEqual(a['nodes'],b['nodes']);self.assertEqual(a['samples'],b['samples'])
    def test_context_and_reverse_instantiations(self):
        p,c=self.evaluation(4);index=H.Index(c,p['length'],self.library);self.assertTrue(any(item['instance']['context'] for item in index.instances));self.assertTrue(any(item['instance']['direction']==-1 for item in index.instances))
    def test_proposal_description_must_not_supply_graph_degrees(self):
        p,c=self.evaluation();m=S.Model(c,p['length']);s=m.initial();g=Graph(m,s);before=g.fingerprint();index=H.Index(c,p['length'],self.library);index.offered(m,s,g,S.cell(1));self.assertEqual(g.fingerprint(),before);self.assertEqual(set(g.edges),set().union(*g.domains.values()))

if __name__=='__main__':unittest.main()
