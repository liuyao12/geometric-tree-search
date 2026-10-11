"""Transfer scope, shared/distant writers, exact direct graph and corruption."""
import copy,gzip,itertools,json,unittest
from pathlib import Path
from semantic_receptor_points import Model
from semantic_inventory_search import search
from conditional_failure_markings import learn,MarkedModel
from audit_conditional_failure_markings import teacher,check_learning,check_overlay
from boundary_reuse_constraints import packet,PointModel,DirectModel,original_record
from audit_boundary_reuse import admit,direct_record,direct_tree,semantic_tree
from audit_semantic_inventory import LiteralDomains,initial,legal,advance,need,same
from prefix_failure_differential import compare
from turtle import Graph

DOC=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'


class BoundaryReuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        training=json.loads(gzip.decompress((DOC/'semantic-inventory-training-001.json.gz').read_bytes()))
        spec=next(s for s in training['cases'] if s['id']=='two-premise')
        cls.base=Model(spec,training['catalog'][spec['id']],training['registries'][spec['id']])
        cls.learning=learn(cls.base,[(0,1),(1,2)],1000,30,check=teacher)
        cls.pair=check_learning(cls.base,cls.learning)
        cls.raw=dict(case=spec,compiled=cls.base.compiled,inventory=cls.base.inventory,
                     learning=cls.learning,certificate=cls.pair)
        cls.source=dict(path='unit-fixture',sha256='unit-fixture')
        cls.packet=packet(cls.learning,cls.source);cls.packet['pair_certificate']=cls.pair
        cls.admission=admit(cls.raw,spec,cls.packet,cls.source)
        cls.point=PointModel(cls.base,cls.packet,cls.admission)
        cls.direct=DirectModel(cls.base,cls.packet,cls.admission)
        spec=next(s for s in training['cases'] if s['id']=='training-short-two')
        cls.consumer=Model(spec,training['catalog'][spec['id']],training['registries'][spec['id']])
        learning=learn(cls.consumer,[(0,1),(1,2)],1000,30,check=teacher)
        pair=check_learning(cls.consumer,learning)
        raw=dict(case=spec,compiled=cls.consumer.compiled,inventory=cls.consumer.inventory,
                 learning=learning,certificate=pair)
        p=packet(learning,cls.source);p['pair_certificate']=pair
        certificate=admit(raw,spec,p,cls.source)
        cls.consumer_point=PointModel(cls.consumer,p,certificate)
        cls.consumer_direct=DirectModel(cls.consumer,p,certificate)

    def test_same_exact_overlay_and_complete_solution_set(self):
        old=MarkedModel(self.base,self.learning,self.pair)
        check_overlay(self.base,self.learning,self.pair,self.point.record())
        self.assertEqual(old.failures,self.point.failures)
        result=compare(self.base.spec,original_record(self.base),self.point.record(),self.base.inventory)
        self.assertEqual((result['words'],result['original_regions'],result['marked_regions']),(2592,4,4))
        self.assertEqual(direct_record(original_record(self.base),self.point.record(),self.direct.record())['status'],'passed')

    def test_reachable_subset_graphs_and_independent_full_domains(self):
        # Ten distinct obligations, including premise fields: enumerate all
        # 1,024 subsets. Incompatible subsets are rejected by both models.
        chosen=[];centers=set()
        relevant=[tuple(k) for f in self.point.failures for field in ('left_keys','right_keys','joint_keys') for k in f[field]]
        for k in relevant+sorted(self.base.cache):
            p=self.base.cache[k].occupancy[0][0]
            if p not in centers:chosen.append(k);centers.add(p)
            if len(chosen)==10:break
        self.assertEqual(len(chosen),10)
        point_record=self.point.record();lookup={tuple(c['key']):c for c in point_record['placements']}
        independent=LiteralDomains(lookup);checked=0
        for mask in range(1<<10):
            ps=self.point.initial();ds=self.direct.initial();pg=Graph(self.point,ps);dg=Graph(self.direct,ds)
            literal=initial(self.base.spec,point_record);literal['marks']={tuple(p):v for p,v in point_record['initial_marks']}
            for i,k in enumerate(chosen):
                if not mask&(1<<i):continue
                self.assertEqual(ps.legal(self.point.placement(k)),ds.legal(self.direct.placement(k)))
                if not ps.legal(self.point.placement(k)):break
                pg.update(self.point,ps,ps.place(self.point.placement(k)))
                dg.update(self.direct,ds,ds.place(self.direct.placement(k)))
                literal=advance(lookup[k],literal)
                self.assertEqual(pg.fingerprint(),dg.fingerprint())
                expected={p:set(ks) for p,ks in independent(literal).items()}
                self.assertEqual(dg.domains,expected)
                self.assertEqual(pg.decision(ps),dg.decision(ds))
                checked+=1
            else:
                self.assertEqual(pg.fingerprint(),dg.fingerprint())
        self.assertGreater(checked,100)

    def test_actual_trees_and_rollback(self):
        a=search(self.point,'base',attempts=1000,seconds=30)
        b=search(self.direct,'base',attempts=1000,seconds=30)
        checked=direct_tree(self.base.spec,original_record(self.base),self.point.record(),b,self.base.inventory)
        self.assertGreater(checked['nodes'],0);self.assertTrue(b['root_restored'])
        self.assertEqual(semantic_tree(a),semantic_tree(b))
        state=self.direct.initial();child=state.copy()
        k=next(k for k in self.direct.cache if child.legal(self.direct.placement(k)))
        child.place(self.direct.placement(k))
        self.assertEqual(state.selected,set());self.assertEqual((state.active_left,state.active_right),(0,0))

    def test_boundary_transfer_and_old_false_scope_rejection(self):
        # Use a target whose old pair catalog does not involve its final row,
        # so extending the boundary leaves the entire declared catalog intact.
        spec=copy.deepcopy(self.base.spec);spec['length']=5;spec['id']='unit-longer-boundary'
        learning=learn(self.base,[(0,1)],1000,30,check=teacher);pair=check_learning(self.base,learning)
        raw=dict(self.raw,learning=learning,certificate=pair);p=packet(learning,self.source);p['pair_certificate']=pair
        certificate=admit(raw,spec,p,self.source)
        PointModel(Model(spec,self.base.compiled,self.base.inventory),p,certificate)
        with self.assertRaises(ValueError):PointModel(self.base,p,certificate)
        short=copy.deepcopy(spec);short['length']=1
        with self.assertRaises(ValueError):admit(raw,short,p,self.source)

    def test_changed_theory_registry_or_omitted_constraint_rejected(self):
        p=copy.deepcopy(self.packet);p['negatives'].pop()
        with self.assertRaises(ValueError):admit(self.raw,self.base.spec,p,self.source)
        p=copy.deepcopy(self.packet);p['negatives'][0]['formulas'][0]=['bot']
        with self.assertRaises(ValueError):admit(self.raw,self.base.spec,p,self.source)
        spec=copy.deepcopy(self.base.spec);spec['theory']['axioms']['extra']=['bot']
        with self.assertRaises(ValueError):admit(self.raw,spec,self.packet,self.source)
        with self.assertRaises(ValueError):DirectModel(self.base,self.packet,dict(self.admission,packet_sha256='wrong'))

    def test_shared_writer_has_no_inconsistent_tile_mark(self):
        f=next(f for f in self.consumer_point.failures if f['joint_keys'])
        for k in f['joint_keys']:
            self.assertFalse(self.consumer_point.initial().legal(self.consumer_point.placement(k)))
            self.assertFalse(self.consumer_direct.initial().legal(self.consumer_direct.placement(k)))
            marks=self.consumer_point.placement(k).marks
            self.assertEqual(len(dict(marks)),len(marks))
            self.assertEqual(self.consumer.placement(k).marks,self.consumer_direct.placement(k).marks)

    def test_dropped_direct_distant_dependency_and_membership_rejected(self):
        record=self.consumer_direct.record()
        token=next(t for t in record['direct_constraints']['dependency_tokens']
                   if any(self.consumer.metadata[tuple(k)]['kind']=='lemma_input' for k in t['keys']))
        k=next(k for k in token['keys'] if self.consumer.metadata[tuple(k)]['kind']=='lemma_input');token['keys'].remove(k)
        with self.assertRaises(ValueError):direct_record(original_record(self.consumer),self.consumer_point.record(),record)
        record=self.direct.record();record['direct_constraints']['membership'][0]['left']^=1
        with self.assertRaises(ValueError):direct_record(original_record(self.base),self.point.record(),record)

    def test_corrupt_direct_state_or_domain_rejected(self):
        out=search(self.direct,'base',attempts=1000,seconds=30)
        bad=copy.deepcopy(out);bad['tree']['state_sha256']='wrong'
        with self.assertRaises(ValueError):direct_tree(self.base.spec,original_record(self.base),self.point.record(),bad,self.base.inventory)
        bad=copy.deepcopy(out);bad['tree']['census'][0]['keys'].clear()
        with self.assertRaises(ValueError):direct_tree(self.base.spec,original_record(self.base),self.point.record(),bad,self.base.inventory)


if __name__=='__main__':unittest.main()
