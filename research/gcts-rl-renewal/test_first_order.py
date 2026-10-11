"""Full tiny command language, independent domains, hygiene and authority gates."""
import copy,itertools,json,unittest
from first_order_cases import cases,case,V,F,P,A
from first_order_receptors import syntax,compile_guards,Model
from semantic_inventory_search import search
from audit_first_order import syntax as literal_syntax,model_binding,subst
from audit_semantic_inventory import LiteralDomains,initial,advance,legal
from audit_prefix_failure_markings import extended_tree
from audit_semantic_proofs import whole_replay
from turtle import Graph

class LogicalFixture:
    """Only unit fixtures use the separate logical replay; pilot uses native I/O."""
    def __init__(self,unknown=None):self.records=[];self.unknown=unknown
    def request(self,r,limit,purpose):
        try:status=whole_replay(r)['status']
        except ValueError:status='rejected'
        if len(self.records)==self.unknown:status='unknown_test_budget'
        q=dict(id=len(self.records),request=copy.deepcopy(r),purpose=purpose,result=dict(status=status));self.records.append(q);return q

class FirstOrder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=case('tiny','Tiny universal instance',dict(a=0),dict(P=1),dict(given=A('x',P('P',V('x')))),P('P',F('a')),3,'Exhaustive unit grammar.')
        cls.oracle=LogicalFixture();cls.compiled=compile_guards(cls.spec,cls.oracle);cls.model=Model(cls.spec,cls.compiled)
    def test_uniform_syntax_all_declared_targets(self):
        for s in cases():self.assertEqual(syntax(s),literal_syntax(s),s['id'])
    def test_complete_tiny_words_and_exact_region_equivalence(self):
        record=self.model.record();model_binding(self.spec,self.compiled,record);inventory={tuple(c['key']):c for c in record['placements']};guards={}
        for c in inventory.values():
            if c['kind']=='guard':guards.setdefault((c['slot'],c['key'][2]),[]).append(c)
        total=accepted=0
        for indexes in itertools.product(*[range(len(d)) for d in self.model.domains]):
            state=initial(self.spec,record);proof=[]
            for j,k in enumerate(indexes):
                tile=inventory[j,0,k,0];self.assertTrue(legal(tile,state));state=advance(tile,state);proof.append(tile['command'])
            geometric=all(any(legal(g,state) for g in guards.get((j,k),[])) for j,k in enumerate(indexes))
            request=dict(protocol='gcts-fol-1',theory=self.spec['theory'],blocks=[],proof=proof,target=self.spec['target'])
            try:logical=whole_replay(request)['status']=='accepted'
            except ValueError:logical=False
            self.assertEqual(geometric,logical);total+=1;accepted+=geometric
        # The hypothesis and the independent instantiation scheme may occur
        # in either order before the final modus ponens.
        self.assertEqual((total,accepted),(2457,2))
    def test_all_selected_subsets_and_distant_graph_updates(self):
        result=search(self.model,'base',attempts=500,seconds=30);self.assertIsNotNone(result['proof']);record=self.model.record();inventory={tuple(c['key']):c for c in record['placements']};literal=LiteralDomains(inventory)
        keys=result['placements'];self.assertEqual(len(keys),6)
        for mask in range(1<<len(keys)):
            s=self.model.initial();g=Graph(self.model,s);a=initial(self.spec,record)
            for i,k in enumerate(keys):
                if mask&(1<<i):
                    self.assertEqual(s.legal(self.model.placement(k)),legal(inventory[tuple(k)],a))
                    g.update(self.model,s,s.place(self.model.placement(k)));a=advance(inventory[tuple(k)],a)
                    self.assertEqual(g.domains,{p:set(v) for p,v in literal(a).items()})
            self.assertEqual(g.domains,{p:set(v) for p,v in literal(a).items()})
        checked=extended_tree(self.spec,record,result,[],None,record['initial_marks']);self.assertGreater(checked['nodes'],0);self.assertTrue(result['root_restored'])
    def test_capture_avoiding_instance_and_wrong_capture_rejected(self):
        s=next(s for s in cases() if s['id']=='capture-avoiding');compiled=compile_guards(s,LogicalFixture());model=Model(s,compiled);result=search(model,'base',attempts=2000,seconds=30)
        self.assertIsNotNone(result['proof']);r=dict(protocol='gcts-fol-1',theory=s['theory'],blocks=[],proof=result['proof'],target=s['target']);self.assertEqual(whole_replay(r)['status'],'accepted')
        good=next(c for c in compiled['admitted_schemes'] if c['universal']==s['theory']['axioms']['universal'] and c['term']==V('y'))
        bad=copy.deepcopy(good);bad['formula']=['imp',good['universal'],A('y',P('R',V('y'),V('y')))]
        q=LogicalFixture().request(dict(protocol='gcts-fol-1',theory=s['theory'],blocks=[],proof=[bad],target=bad['formula']),1,'unit_wrong_capture');self.assertEqual(q['result']['status'],'rejected')
        self.assertEqual(subst(good['universal'][2],'x',V('y')),s['target'])
    def test_equality_search_and_changed_template_rejected(self):
        s=next(s for s in cases() if s['id']=='equality-predicate');compiled=compile_guards(s,LogicalFixture());model=Model(s,compiled);result=search(model,'base',attempts=2000,seconds=30);self.assertIsNotNone(result['proof'])
        r=dict(protocol='gcts-fol-1',theory=s['theory'],blocks=[],proof=result['proof'],target=s['target']);self.assertEqual(whole_replay(r)['status'],'accepted')
        row=next(c for c in r['proof'] if c['rule']=='eq_subst');row['left']=F('b');self.assertEqual(whole_replay(r)['status'],'rejected')
    def test_unknown_compilation_cannot_construct_a_model(self):
        c=compile_guards(self.spec,LogicalFixture(unknown=2));self.assertEqual(c['status'],'unknown_native_compilation');self.assertRaises(ValueError,Model,self.spec,c)
    def test_missing_domain_guard_word_and_false_authority_rejected(self):
        for edit in [lambda r:r['domains'][0].pop(),lambda r:r['placements'][-1]['marks'].pop(),lambda r:r['initial_marks'].pop()]:
            r=json.loads(json.dumps(self.model.record()));edit(r);self.assertRaises(ValueError,model_binding,self.spec,self.compiled,r)
        c=copy.deepcopy(self.compiled);c['admitted_schemes'].pop();self.assertRaises(ValueError,model_binding,self.spec,c,self.model.record())

if __name__=='__main__':unittest.main()
