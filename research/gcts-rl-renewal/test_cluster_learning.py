"""Cluster marking controls, independent oracles and certificate semantics."""
import copy,dataclasses,unittest
from turtle import Model,State,Graph,BASE,SYMMETRIES,sub,transform,verify_patch,exhaustive_domains
from cluster_tiles import ClusterModel,ClusterState,compose_type
from cluster_learning import catalog,pair_expansion,corona,Encoder,decorated,all_disagreements,IndependentOracle,seeded,check_corona_failure,check_corona_positive,exact_keys
from run_cluster_marking import selected_types

class ClusterLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.single,cls.proto=selected_types();cls.contacts=catalog(cls.proto);cls.model=ClusterModel([cls.proto])

    def test_catalog_matches_independent_flattened_base_capacity(self):
        p=self.proto;root=set(p.expansion);independent=set();base=Model()
        from spatial import moved
        for o,g in enumerate(SYMMETRIES):
            translations={sub(a,transform(b,g)) for a,v in p.occupancy for b,w in p.occupancy}
            for tr in translations:
                expansion=moved(p.expansion,g,tr)
                if not root.intersection(expansion) and verify_patch(base,p.expansion+expansion):independent.add((p.identity,o,tr))
        self.assertEqual(set(self.contacts),independent)

    def test_replay_value_cache_matches_full_original_domains(self):
        base=Model();s=State();s.place(base.placement((0,(0,0,0))),seed=True);oracle=IndependentOracle()
        for i in range(3):
            self.assertEqual(oracle.domains(s),exhaustive_domains(base,s))
            kind,p,keys=Graph(base,s).decision(s)
            if not keys:break
            s.place(base.placement(keys[-1]))

    def test_negative_tree_and_omitted_branch_rejected(self):
        seeds=pair_expansion(self.model,self.contacts[10]);r=corona(Model(),seeds,5000,15)
        self.assertEqual(r['status'],'negative');self.assertGreater(r['branches'],0)
        self.assertTrue(check_corona_failure(Model(),seeds,r['certificate'])[0])
        bad=copy.deepcopy(r['certificate']);bad['children'].pop()
        self.assertFalse(check_corona_failure(Model(),seeds,bad)[0])

    def test_online_controls_positive_equalities_unknowns_and_free_entries(self):
        # These are labeled encoder controls, not claimed extension labels.
        encoder=Encoder(self.proto);k=self.contacts[0]
        encoder.add({'status':'negative','second':k});before=encoder.history[-1]['components']
        encoder.add({'status':'unresolved','second':self.contacts[1]});self.assertEqual(before,encoder.history[-1]['components'])
        encoder.add({'status':'positive','second':k});marking,stats=encoder.finish()
        self.assertEqual(stats['positive_accepted'],1);self.assertEqual(stats['negative_rejected'],0)
        self.assertEqual(marking,{}) # contradictory negative cannot invent inequality inside an equality class
        self.assertEqual(stats['free'],len(self.proto.occupancy))

    def test_own_channel_scalar_action_parent_inheritance_and_disagreements(self):
        points=list(dict(self.proto.occupancy));control={points[0]:0,points[-1]:1};marked=decorated(self.proto,control)
        model=ClusterModel([marked]);parent=compose_type(model,'control-parent',[(marked.identity,0,(0,0,0))],own_marking={points[0]:2})
        self.assertEqual(dict(parent.marks)[(points[0],'cluster:1')],0)
        self.assertEqual(dict(parent.marks)[(points[0],'cluster:2')],2)
        self.assertTrue(all(k in self.contacts for k in all_disagreements(self.proto,control)))
        for o,g in enumerate(SYMMETRIES):
            c=model.placement((marked.identity,o,(0,0,0)));self.assertEqual(dict(c.marks)[(transform(points[0],g),'cluster:1')],0)

    def test_exact_certificate_types_and_rejected_positive_claim(self):
        with self.assertRaises(ValueError):exact_keys([(True,(0,0,0))])
        with self.assertRaises(ValueError):exact_keys([(0,(True,-1,0))])
        seeds=pair_expansion(self.model,self.contacts[0])
        self.assertFalse(check_corona_positive(Model(),seeds,seeds))
        bad=[[True,list(tr)] for o,tr in seeds];self.assertFalse(check_corona_positive(Model(),seeds,bad))
        self.assertFalse(check_corona_failure(Model(),seeds,{'dead':(True,-1,0)})[0])

if __name__=='__main__':unittest.main()
