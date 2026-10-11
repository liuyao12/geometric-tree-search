"""Conformance and corruption checks for the new failure-marking layer."""
import copy,gzip,json,unittest
from pathlib import Path
from semantic_receptor_points import Model
from prefix_failure_markings import learn,MarkedModel
from audit_prefix_failure_markings import teacher,check_learning,check_overlay,extended_tree
from semantic_inventory_search import search
from prefix_failure_differential import compare

DOC=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'

class FailureMarks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        training=json.loads(gzip.decompress((DOC/'semantic-inventory-training-001.json.gz').read_bytes()))
        cls.spec=next(s for s in training['cases'] if s['id']=='two-premise')
        cls.compiled=training['catalog']['two-premise'];cls.inventory=training['registries']['two-premise']
        cls.base=Model(cls.spec,cls.compiled,cls.inventory)
        cls.learning=learn(cls.base,1000,30,check=teacher);cls.certificate=check_learning(cls.base,cls.learning)
        cls.marked=MarkedModel(cls.base,cls.learning,cls.certificate)
        spec=next(s for s in training['cases'] if s['id']=='training-short-two')
        cls.consumer_base=Model(spec,training['catalog'][spec['id']],training['registries'][spec['id']])
        cls.consumer_learning=learn(cls.consumer_base,1000,30,check=teacher)
        cls.consumer_certificate=check_learning(cls.consumer_base,cls.consumer_learning)
        cls.consumer_marked=MarkedModel(cls.consumer_base,cls.consumer_learning,cls.consumer_certificate)
    def test_complete_solution_set(self):
        result=compare(self.spec,self.base.record(),self.marked.record(),self.inventory)
        self.assertEqual((result['words'],result['original_regions'],result['marked_regions']),(2592,4,4))
    def test_all_writer_and_consumer_support(self):
        result=check_overlay(self.base,self.learning,self.certificate,self.marked.record())
        self.assertEqual(result['negative_ports'],2);self.assertGreater(result['affected_candidates'],2)
        result=check_overlay(self.consumer_base,self.consumer_learning,self.consumer_certificate,self.consumer_marked.record())
        self.assertGreater(result['negative_ports'],2)
        self.assertTrue(any('lemma_input' in f['by_kind'] for f in self.consumer_marked.failures))
    def test_complete_marked_tree(self):
        model=MarkedModel(Model(self.spec,self.compiled,self.inventory),self.learning,self.certificate)
        out=search(model,'base',attempts=1000,seconds=30)
        checked=extended_tree(self.spec,model.record(),out,self.inventory,None,model.record()['initial_marks'])
        self.assertGreater(checked['nodes'],0)
    def test_unknown_adds_no_marking(self):
        learning=learn(self.base,0,30,check=teacher);certificate=check_learning(self.base,learning)
        self.assertGreater(learning['counts'].get('unknown',0),0)
        marked=MarkedModel(self.base,learning,certificate)
        self.assertEqual(marked.exterior,{})
        self.assertEqual(marked.initial().marks,self.base.initial().marks)
    def test_corrupt_prefix_exhaustion(self):
        bad=copy.deepcopy(self.learning)
        p=next(p for p in bad['probes'] if p['label']=='negative' and p['search']['tree']['children'])
        p['search']['tree']['children'].clear()
        with self.assertRaises(ValueError):check_learning(self.base,bad)
    def test_dropped_consumer_mark(self):
        record=self.consumer_marked.record();p=next(c for c in record['placements'] if c['kind']=='lemma_input'
            and any(q[0]%4==3 for q,v in c['marks']))
        p['marks']=[(q,v) for q,v in p['marks'] if q[0]%4!=3]
        with self.assertRaises(ValueError):check_overlay(self.consumer_base,self.consumer_learning,self.consumer_certificate,record)
    def test_changed_boundary_value(self):
        record=self.marked.record();record['initial_marks']=[(p,1 if p[0]%4==3 else v) for p,v in record['initial_marks']]
        with self.assertRaises(ValueError):check_overlay(self.base,self.learning,self.certificate,record)
    def test_context_change_rejected(self):
        other=copy.deepcopy(self.spec);other['theory']['axioms']['new']=['bot']
        base=Model(other,self.compiled,self.inventory)
        with self.assertRaises(ValueError):MarkedModel(base,self.learning,self.certificate)
    def test_quantified_vocabulary_retained(self):
        raw=json.loads(gzip.decompress((DOC/'semantic-inventory-001-double-universal-semantic-base-r1.json.gz').read_bytes()))
        base=Model(raw['case'],raw['compiled'],raw['inventory']);learning=learn(base,1000,30,check=teacher)
        p=next(p for p in learning['probes'] if p['length']==2 and p['formula'][0]=='eq')
        formulas=[c['formula'] for c in p['model']['domains'][0]]
        self.assertIn(raw['case']['target'],formulas)
        bad=copy.deepcopy(p);bad['model']['domains'][0]=[c for c in bad['model']['domains'][0] if c['formula']!=raw['case']['target']]
        with self.assertRaises(ValueError):teacher(base,bad)

if __name__=='__main__':unittest.main()
