"""Meaningful small exhaustive and corrupt-dictionary checks for the quotient."""
import copy,itertools,unittest
from catalog_receptor_points import Catalog,Model
from first_order_family_points import Model as WordModel
from first_order_receptors import syntax
from catalog_receptor_search import search
from audit_catalog_receptors import correspondence,model_binding,check_tree,parse_fields
from turtle import Graph

def fixture():
    a=['fun','a',[]];p=['pred','P',[a]]
    spec=dict(id='tiny',length=2,target=p,theory=dict(functions=dict(a=0),predicates=dict(P=1),axioms=dict(given=p)))
    catalog=syntax(spec)
    compiled=dict(status='complete',basis=catalog['basis'],variables=catalog['variables'],tautologies=[],admitted_schemes=[],catalog=catalog)
    inventory=dict(status='native_accepted',definitions=[],interfaces=[],native_blocks=[])
    return spec,compiled,inventory

class Checks(unittest.TestCase):
    def test_injective_words(self):
        values=[['pred','P',[]],['pred','PP',[]],['pred','é',[]]]
        c=Catalog(values,[])
        self.assertEqual(len(c.words['formula']),3)
        self.assertEqual(len({c.assignment(0,'formula',v)[0][1] for v in values}),3)
    def test_all_legal_partial_states(self):
        spec,c,i=fixture();w=WordModel(spec,c,i,arity=1);q=Model(spec,c,i,arity=1)
        correspondence(w.record(),q.record());model_binding(spec,c,i,q.record())
        visited=set();count=0
        def visit(a,b):
            nonlocal count
            identity=tuple(sorted(a.selected))
            if identity in visited:return
            visited.add(identity);count+=1
            legal_a={k for k,t in w.cache.items() if a.legal(t)}
            legal_b={k for k,t in q.cache.items() if b.legal(t)}
            self.assertEqual(legal_a,legal_b)
            self.assertEqual(Graph(w,a).decision(a),Graph(q,b).decision(b))
            for k in sorted(legal_a):
                aa=a.copy();bb=b.copy();aa.place(w.placement(k));bb.place(q.placement(k));visit(aa,bb)
        visit(w.initial(),q.initial());self.assertGreater(count,100)
    def test_complete_trees(self):
        spec,c,i=fixture()
        for cls in (WordModel,Model):
            m=cls(spec,c,i,arity=1)
            for mode in ('base','fixed','learned'):
                r=search(m,mode,weights=[.1]*10 if mode=='learned' else None,feature_semantics='expanded-word',attempts=1000,seconds=30)
                check_tree(spec,m.record(),r,i,[.1]*10 if mode=='learned' else None)
                self.assertTrue(r['root_restored']);self.assertIsNotNone(r['proof'])
    def test_collision_and_changed_word_rejected(self):
        spec,c,i=fixture();full=WordModel(spec,c,i,arity=1).record();compact=Model(spec,c,i,arity=1).record()
        bad=copy.deepcopy(compact);bad['catalog']['command'][1]['id']=0
        with self.assertRaises(ValueError):correspondence(full,bad)
        bad=copy.deepcopy(compact);bad['catalog']['formula'][0]['word_hex']='00'
        with self.assertRaises(ValueError):correspondence(full,bad)
        bad=copy.deepcopy(compact);bad['placements'][0]['marks']=bad['placements'][0]['marks'][:-1]
        with self.assertRaises(ValueError):correspondence(full,bad)
    def test_partial_words_are_not_compressible(self):
        for marks in ([((0,100),65)],[((0,101),256)],[((0,100),256),((0,101),65)]):
            with self.assertRaises(ValueError):parse_fields(marks)

if __name__=='__main__':unittest.main()
