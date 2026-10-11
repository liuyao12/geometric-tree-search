"""Typed finite joins, native-authority gates and literal point correspondence."""
import copy,itertools,json,unittest
from first_order_cases import cases,case,F,V,P,A
from first_order_receptors import compile_guards,Model as Primitive
from first_order_family_cases import promotion,transport
from first_order_families import mine,specialize,admit,bindings,replace,argument
from first_order_family_points import Model
from semantic_inventory_search import search
from semantic_lemma_inventory import used_definitions
from audit_first_order_families import abstract,ground_inventory,registry_binding,model_binding
from audit_semantic_inventory import LiteralDomains,initial,advance,legal
from audit_prefix_failure_markings import extended_tree
from audit_semantic_proofs import whole_replay
from test_first_order import LogicalFixture
from turtle import Graph

def discovered(spec):
    compiled=compile_guards(spec,LogicalFixture());out=search(Primitive(spec,compiled),'base',attempts=2000,seconds=30)
    if out['proof'] is None:raise ValueError('unit donor was not discovered')
    request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=out['proof'],target=spec['target'])
    if whole_replay(request)['status']!='accepted':raise ValueError('unit donor not checked')
    return mine(request,None,dict(unit_discovered=True)),request

def family_model(spec,library,arity=3,families=True,oracle=None):
    oracle=oracle or LogicalFixture();compiled=compile_guards(spec,oracle)
    inv=admit(spec,specialize(library,spec,compiled['catalog']),oracle)
    registry_binding(library,spec,compiled,inv,oracle.records)
    model=Model(spec,compiled,inv,arity,families);model_binding(spec,compiled,inv,model.record(),arity,families)
    return compiled,inv,model

class Families(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        eq=next(s for s in cases() if s['id']=='equality-predicate');cls.eq,cls.eq_request=discovered(eq)
        universal=case('unit-universal','Unit universal instance',dict(a=0),dict(P=1),dict(given=A('x',P('P',V('x')))),P('P',F('a')),3,'Unit source assertion only.')
        cls.universal,cls.universal_request=discovered(universal)
        cls.tiny=dict(universal,length=2);cls.compiled,cls.inventory,cls.model=family_model(cls.tiny,[cls.universal],1)
    def test_independent_extraction_and_complete_typed_join(self):
        for family,request in [(self.eq,self.eq_request),(self.universal,self.universal_request)]:
            literal=abstract(request,None,family['provenance'])
            for k,v in literal.items():self.assertEqual(v,family[k])
        spec=transport('join','Join universe',['a','b','c'],5,'R');compiled=compile_guards(spec,LogicalFixture());cat=compiled['catalog']
        candidate=specialize([self.eq],spec,cat);literal=ground_inventory([self.eq],spec,cat)
        for k in ('definitions','interfaces','native_blocks'):self.assertEqual(candidate[k],literal[k])
        pools=[([argument('term',t) for t in cat['equality_terms']] if p['kind']=='term' else [argument('predicate',n,a) for n,a in sorted(spec['theory']['predicates'].items()) if a==p['arity']]) for p in self.eq['parameters']]
        brute=[]
        for args in itertools.product(*pools):
            g=replace(self.eq['template'],args)
            if all(f in cat['basis'] for f in g['premises']+[g['conclusion']]):brute.append(list(args))
        self.assertEqual(sorted(bindings(self.eq,spec,cat),key=str),sorted(brute,key=str))
    def test_compound_closed_terms_and_predicate_arity(self):
        spec=transport('compound','Compound instance',['k0','k1'],3,'Ready',True)
        compiled,inventory,model=family_model(spec,[self.eq]);self.assertGreater(len(inventory['interfaces']),0)
        self.assertTrue(any(a[0]=='term_argument' and a[1][1]=='wrap' for d in inventory['definitions'] for a in d['arguments']))
        wrong=copy.deepcopy(self.eq);next(p for p in wrong['parameters'] if p['kind']=='predicate')['arity']=2
        # No declared binary predicate can satisfy the changed descriptor.
        self.assertEqual(bindings(wrong,spec,compiled['catalog']),[])
        bad=copy.deepcopy(inventory);bad['status']='unknown_native_inventory';self.assertRaises(ValueError,Model,spec,compiled,bad,3,True)
    def test_all_tiny_command_words_geometric_iff_logical(self):
        record=self.model.record();lookup={tuple(c['key']):c for c in record['placements']};guards={};inputs={}
        for c in lookup.values():
            if c['kind']=='guard':guards.setdefault((c['slot'],c['key'][2]),[]).append(c)
            elif c['key'][1]==2:inputs.setdefault(c['slot'],[]).append(c)
        accepted=total=0
        for indexes in itertools.product(*[range(len(d)) for d in self.model.domains]):
            state=initial(self.tiny,record);proof=[]
            for j,k in enumerate(indexes):
                c=lookup[j,0,k,0];self.assertTrue(legal(c,state));state=advance(c,state)
                row=copy.deepcopy(c['command'])
                if row['rule']=='block':row['inputs']=[0] if j else []
                proof.append(row)
            geometric=all(any(legal(g,state) for g in guards.get((j,k),[])) and any(legal(c,state) for c in inputs[j]) for j,k in enumerate(indexes))
            request=dict(protocol='gcts-fol-1',theory=self.tiny['theory'],blocks=used_definitions(self.inventory,proof),proof=proof,target=self.tiny['target'])
            try:logical=whole_replay(request)['status']=='accepted'
            except ValueError:logical=False
            self.assertEqual(geometric,logical);accepted+=geometric;total+=1
        self.assertGreater(total,0);self.assertGreater(accepted,0);self.tiny_counts=(total,accepted)
    def test_every_selected_subset_and_distant_input_receptor(self):
        result=search(self.model,'fixed',attempts=2000,seconds=30);self.assertIsNotNone(result['proof']);record=self.model.record();lookup={tuple(c['key']):c for c in record['placements']};literal=LiteralDomains(lookup)
        self.assertEqual(len(result['placements']),6)
        for mask in range(64):
            state=self.model.initial();graph=Graph(self.model,state);independent=initial(self.tiny,record)
            for i,k in enumerate(result['placements']):
                if mask&(1<<i):
                    self.assertEqual(state.legal(self.model.placement(k)),legal(lookup[tuple(k)],independent))
                    graph.update(self.model,state,state.place(self.model.placement(k)));independent=advance(lookup[tuple(k)],independent)
                    self.assertEqual(graph.domains,{p:set(v) for p,v in literal(independent).items()})
            self.assertEqual(graph.domains,{p:set(v) for p,v in literal(independent).items()})
        checked=extended_tree(self.tiny,record,result,self.inventory,None,record['initial_marks']);self.assertGreater(checked['nodes'],0);self.assertTrue(result['root_restored'])
    def test_automatic_dependent_family_promotion(self):
        spec=promotion();compiled,inventory,model=family_model(spec,[self.eq]);result=search(model,'fixed',attempts=2000,seconds=30)
        self.assertIsNotNone(result['proof']);self.assertTrue(any(c['rule']=='block' for c in result['proof']))
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=used_definitions(inventory,result['proof']),proof=result['proof'],target=spec['target'])
        self.assertEqual(whole_replay(request)['status'],'accepted');family=mine(request,inventory,dict(unit_discovered=True));literal=abstract(request,inventory,family['provenance'])
        for k,v in literal.items():self.assertEqual(v,family[k])
        self.assertTrue(family['dependencies']);higher=specialize([self.eq,family],spec,compiled['catalog']);self.assertIn(2,{d['level'] for d in higher['definitions']})
        checked=extended_tree(spec,model.record(),result,inventory,None,model.record()['initial_marks']);self.assertGreater(checked['nodes'],0)
    def test_same_roots_and_primitive_fallback(self):
        primitive=Model(self.tiny,self.compiled,self.inventory,1,False);full=self.model
        self.assertEqual(primitive.record()['roots'],full.record()['roots']);self.assertEqual(primitive.record()['initial_marks'],full.record()['initial_marks'])
        self.assertTrue(all(c['rule']!='block' for rows in primitive.domains for c in rows))
        for j,rows in enumerate(primitive.domains):self.assertTrue(all(c in full.domains[j] for c in rows))
        result=search(primitive,'base',attempts=2000,seconds=30);checked=extended_tree(self.tiny,primitive.record(),result,[],None,primitive.record()['initial_marks']);self.assertGreater(checked['nodes'],0)
    def test_missing_point_and_unfinished_ground_admission_rejected(self):
        for edit in [lambda r:r['domains'][0].pop(),lambda r:r['placements'][-1]['marks'].pop(),lambda r:r['initial_marks'].pop()]:
            record=json.loads(json.dumps(self.model.record()));edit(record);self.assertRaises(ValueError,model_binding,self.tiny,self.compiled,self.inventory,record,1,True)
        bad=admit(self.tiny,specialize([self.universal],self.tiny,self.compiled['catalog']),LogicalFixture(unknown=0));self.assertNotEqual(bad['status'],'native_accepted');self.assertRaises(ValueError,Model,self.tiny,self.compiled,bad,1,True)
        broken=specialize([self.eq],next(s for s in cases() if s['id']=='equality-predicate'),compile_guards(next(s for s in cases() if s['id']=='equality-predicate'),LogicalFixture())['catalog'])
        row=next(c for c in broken['native_blocks'][0]['proof'] if c['rule']=='eq_subst');row['left']=F('b')
        # Keep the two exported representations synchronized, then require
        # rejection by the independent rule semantics, rather than a hash check.
        broken['definitions'][0]['definition']=copy.deepcopy(broken['native_blocks'][0]);spec=next(s for s in cases() if s['id']=='equality-predicate')
        self.assertNotEqual(admit(spec,broken,LogicalFixture())['status'],'native_accepted')

if __name__=='__main__':unittest.main()
