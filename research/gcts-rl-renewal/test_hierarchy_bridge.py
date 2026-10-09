import copy,json,unittest
from hierarchy_bridge import DOCS,PARENT,definitions,next_family,point_lemma,proof_catalog,search,normal
from audit_hierarchy_bridge import check_point_lemma,replay_coarse
from coarse_continuation import RootModel,LiteralOracle,root_state
from cluster_tiles import ClusterModel
from turtle import Graph
from kernel_machine import KernelMachine
import kernel_search,logic

class HierarchyBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Explicit continuation inputs, never a cold learner's fixture.
        cls.previous=json.loads((DOCS/'failure-interfaces-001.json').read_text())
        cls.stage=json.loads((DOCS/'failure-local-level2-001.json').read_text())
        cls.free=definitions(cls.previous,'aggregate unmarked');cls.marked=definitions(cls.previous,'aggregate GCTS')
        cls.lemma=point_lemma(cls.free,cls.marked,cls.stage)
    def test_full_cover_and_every_base_case_proof(self):
        self.assertEqual(len(self.lemma['cases']),17);self.assertEqual(self.lemma['base_failure_nodes'],153)
        self.assertEqual(check_point_lemma(self.free,self.marked,self.stage,self.lemma),(True,153))
    def test_missing_case_duplicate_case_and_boolean_pose_reject(self):
        for mode in ('omit','duplicate','boolean'):
            bad=copy.deepcopy(self.lemma)
            if mode=='omit':bad['cases'].pop()
            elif mode=='duplicate':bad['cases'][-1]=bad['cases'][0]
            else:bad['cases'][0]['placement']=(PARENT,True,(0,0,0))
            self.assertFalse(check_point_lemma(self.free,self.marked,self.stage,bad)[0])
    def test_positive_premise_and_wrong_point_do_not_prove_obstruction(self):
        bad=copy.deepcopy(self.lemma);bad['cases'][0]['source_sample']=next(i for i,s in enumerate(self.stage['samples']) if s['status']=='positive')
        self.assertFalse(check_point_lemma(self.free,self.marked,self.stage,bad)[0])
        bad=copy.deepcopy(self.lemma);bad['point']=(0,0,0)
        self.assertFalse(check_point_lemma(self.free,self.marked,self.stage,bad)[0])
    def test_corrupted_lower_failure_cannot_be_a_logical_fact(self):
        stage=copy.deepcopy(self.stage);i=self.lemma['cases'][0]['source_sample']
        stage['samples'][i]['certificate']={'dead':[999,-400,-599]}
        self.assertFalse(check_point_lemma(self.free,self.marked,stage,self.lemma)[0])
    def test_all_seven_positive_contacts_have_distinct_refinement_owners(self):
        ts,prov=next_family(self.marked,self.stage);self.assertEqual(len(ts),4)
        self.assertEqual(sum(len(p['samples']) for p in prov),7);cm=ClusterModel(self.marked+ts)
        for t in ts:
            children=[cm.placement(k) for k in t.children]
            self.assertEqual(len(t.expansion),10);self.assertEqual(t.level,3)
            self.assertFalse(set(children[0].expansion)&set(children[1].expansion))
            self.assertEqual(set(t.expansion),set(children[0].expansion+children[1].expansion))
    def test_marked_root_leaf_and_rollback_keep_literal_domains(self):
        s=root_state(self.marked,PARENT);m=RootModel(self.marked,(PARENT,),s);g=Graph(m,s)
        self.assertEqual(g.domains,LiteralOracle(self.marked,(PARENT,)).domains(s));self.assertEqual(g.decision(s)[0],'dead')
        snapshot=s.copy();fingerprint=g.fingerprint();key=min(g.edges);child=s.copy();cg=g.copy()
        cg.update(m,child,child.place(m.placement(key)))
        self.assertEqual(cg.domains,LiteralOracle(self.marked,(PARENT,)).domains(child))
        self.assertEqual(s,snapshot);self.assertEqual(g.fingerprint(),fingerprint)
        self.assertTrue(LiteralOracle(self.free,(PARENT,)).domain(root_state(self.free,PARENT),tuple(self.lemma['point'])))
    def test_budget_zero_remains_unknown_with_the_complete_graph(self):
        r=search(self.marked,(PARENT,),PARENT,node_limit=0)
        self.assertEqual(r['status'],'unresolved');self.assertIsNone(r['certificate']);self.assertTrue(replay_coarse(self.marked,normal(r)))
    def test_logical_fact_boundaries_and_no_base_turtle_conclusion(self):
        c,targets=proof_catalog()
        # Find a reference logical witness from the finite facts, not geometry.
        facts=set();commands=[]
        while c.index[targets['ten']] not in facts:
            i=next(i for i,r in enumerate(c.inferences) if r.conclusion not in facts and set(r.premises)<=facts)
            commands.append(i);facts.add(c.inferences[i].conclusion)
        proof=c.proof(commands,targets['ten']);self.assertTrue(c.kernel.check(proof,targets['ten']))
        changed=dict(c.kernel.axioms);changed.pop('checked_all_base_failures')
        self.assertFalse(logic.Kernel({},c.kernel.predicates,changed).check(proof,targets['ten']))
        self.assertFalse(c.kernel.check(proof,('bot',)))
        self.assertEqual(KernelMachine(c,targets['ten']).run(KernelMachine(c,targets['ten']).tokens(commands))['status'],'accept')

if __name__=='__main__':unittest.main()
