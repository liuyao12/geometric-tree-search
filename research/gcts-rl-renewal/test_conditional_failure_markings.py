"""Meaningful soundness, graph/rollback and corruption tests for conjunctions."""
import copy,gzip,json,unittest
from pathlib import Path
from semantic_receptor_points import Model
from semantic_inventory_search import search
from conditional_failure_markings import learn,MarkedModel,CombinedModel
from audit_conditional_failure_markings import teacher,check_learning,check_overlay,check_combined
from audit_prefix_failure_markings import extended_tree,teacher as unary_teacher,check_learning as check_unary
from prefix_failure_markings import learn as learn_unary,MarkedModel as Unary
from prefix_failure_differential import compare
from turtle import Graph

DOC=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'


class ConditionalMarks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        training=json.loads(gzip.decompress((DOC/'semantic-inventory-training-001.json.gz').read_bytes()))
        cls.spec=next(s for s in training['cases'] if s['id']=='two-premise')
        cls.compiled=training['catalog']['two-premise'];cls.inventory=training['registries']['two-premise']
        cls.base=Model(cls.spec,cls.compiled,cls.inventory)
        cls.learning=learn(cls.base,[(0,1),(1,2)],1000,30,check=teacher)
        cls.certificate=check_learning(cls.base,cls.learning)
        cls.marked=MarkedModel(cls.base,cls.learning,cls.certificate)
        spec=next(s for s in training['cases'] if s['id']=='training-short-two')
        cls.consumer_base=Model(spec,training['catalog'][spec['id']],training['registries'][spec['id']])
        cls.consumer_learning=learn(cls.consumer_base,[(0,1),(1,2)],1000,30,check=teacher)
        cls.consumer_certificate=check_learning(cls.consumer_base,cls.consumer_learning)
        cls.consumer_marked=MarkedModel(cls.consumer_base,cls.consumer_learning,cls.consumer_certificate)

    def test_complete_solution_set(self):
        out=compare(self.spec,self.base.record(),self.marked.record(),self.inventory)
        self.assertEqual((out['words'],out['original_regions'],out['marked_regions']),(2592,4,4))

    def test_combined_layers_preserve_exact_region_set(self):
        learning=learn_unary(self.base,1000,30,check=unary_teacher)
        certificate=check_unary(self.base,learning);unary=Unary(self.base,learning,certificate)
        model=CombinedModel(self.base,unary,self.marked)
        checked=check_combined(self.base,unary.record(),self.marked.record(),model.record())
        self.assertEqual(checked['status'],'passed')
        out=compare(self.spec,self.base.record(),model.record(),self.inventory)
        self.assertEqual((out['words'],out['original_regions'],out['marked_regions']),(2592,4,4))
        result=search(model,'base',attempts=1000,seconds=30)
        extended_tree(self.spec,model.record(),result,self.inventory,None,model.record()['initial_marks'])

    def test_complete_all_writer_overlay(self):
        checked=check_overlay(self.consumer_base,self.consumer_learning,self.consumer_certificate,self.consumer_marked.record())
        self.assertGreater(checked['negative_pairs'],0)
        self.assertGreater(checked['joint_writers'],0)
        self.assertTrue(any(self.consumer_base.metadata[tuple(a['key'])]['kind']=='lemma_input'
                            for f in self.consumer_marked.failures for a in f['assignments']))

    def test_marked_graph_and_rollback(self):
        model=MarkedModel(Model(self.spec,self.compiled,self.inventory),self.learning,self.certificate)
        out=search(model,'base',attempts=1000,seconds=30)
        self.assertGreater(extended_tree(self.spec,model.record(),out,self.inventory,None,
                                        model.record()['initial_marks'])['nodes'],0)
        self.assertTrue(out['root_restored'])

    def test_conditional_point_unassigned_until_attachment(self):
        failure=next(f for f in self.consumer_marked.failures if f['left_keys'] and f['right_keys'])
        point=tuple(failure['pair_point'])
        self.assertNotIn(point,self.consumer_marked.initial().marks)
        a=self.consumer_marked.placement(tuple(failure['left_keys'][0]))
        b=self.consumer_marked.placement(tuple(failure['right_keys'][0]))
        self.assertEqual(dict(a.marks)[point],0)
        self.assertEqual(dict(b.marks)[point],1)
        # The complete independent tree check exercises actual reachable graph
        # updates; these values additionally show the conjunction construction.

    def test_unknown_supplies_no_assignment(self):
        learning=learn(self.base,[(0,1)],0,30,check=teacher)
        certificate=check_learning(self.base,learning)
        marked=MarkedModel(self.base,learning,certificate)
        self.assertEqual(marked.failures,[])
        self.assertEqual(marked.exterior,{})
        self.assertEqual(marked.initial().marks,self.base.initial().marks)

    def test_truncated_exhaustion_rejected(self):
        bad=copy.deepcopy(self.consumer_learning)
        p=next(p for p in bad['probes'] if p['label']=='negative' and p['search']['tree']['children'])
        p['search']['tree']['children'].clear()
        with self.assertRaises(ValueError):check_learning(self.consumer_base,bad)

    def test_changed_fixed_earlier_word_rejected(self):
        bad=copy.deepcopy(self.learning)
        p=bad['probes'][0];p['model']['initial_marks']=p['model']['initial_marks'][1:]
        with self.assertRaises(ValueError):check_learning(self.base,bad)

    def test_missing_pair_or_wrong_formula_rejected(self):
        bad=copy.deepcopy(self.learning);bad['catalog'].pop();bad['probes'].pop()
        with self.assertRaises(ValueError):check_learning(self.base,bad)
        bad=copy.deepcopy(self.learning);bad['probes'][0]['formulas'][0]=['bot']
        with self.assertRaises(ValueError):check_learning(self.base,bad)

    def test_dropped_distant_consumer_mark_rejected(self):
        record=self.consumer_marked.record()
        c=next(c for c in record['placements'] if c['kind']=='lemma_input'
               and any(p[0]==3 and p[1]>=200000 for p,v in c['marks']))
        c['marks']=[(p,v) for p,v in c['marks'] if not(p[0]==3 and p[1]>=200000)]
        with self.assertRaises(ValueError):check_overlay(self.consumer_base,self.consumer_learning,
                                                        self.consumer_certificate,record)

    def test_single_tile_joint_writer_rejected_at_fixed_point(self):
        f=next(f for f in self.consumer_marked.failures if f['joint_keys'])
        p=tuple(f['single_point']);self.assertEqual(self.consumer_marked.initial().marks[p],0)
        c=self.consumer_marked.placement(tuple(f['joint_keys'][0]))
        self.assertEqual(dict(c.marks)[p],1)
        self.assertFalse(self.consumer_marked.initial().legal(c))

    def test_changed_value_or_theory_rejected(self):
        record=self.consumer_marked.record()
        c=next(c for c in record['placements'] if any(p[0]==3 and p[1]>=200000 for p,v in c['marks']))
        c['marks']=[(p,1-v if p[0]==3 and p[1]>=200000 else v) for p,v in c['marks']]
        with self.assertRaises(ValueError):check_overlay(self.consumer_base,self.consumer_learning,
                                                        self.consumer_certificate,record)
        other=copy.deepcopy(self.spec);other['theory']['axioms']['extra']=['bot']
        with self.assertRaises(ValueError):MarkedModel(Model(other,self.compiled,self.inventory),
                                                      self.learning,self.certificate)


if __name__=='__main__':unittest.main()
