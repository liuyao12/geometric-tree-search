"""Compare exhaustive and indexed enumeration under contact conflicts."""
import unittest
import induction_clusters as H
import indexed_proof_clusters as J
class JoinTests(unittest.TestCase):
    def setUp(self):
        rules=[dict(inputs=[],output=i,recipe=dict(kind='primitive',witness=dict(rule='tautology'))) for i in range(3)]
        rules += [dict(inputs=[i],output=j,recipe=dict(kind='block',operation='generic')) for i in range(3) for j in range(3)]
        rules += [dict(inputs=[i,j],output=k,recipe=dict(kind='block',operation='generic')) for i in range(3) for j in range(3) for k in range(3)]
        self.c=dict(rules=rules)
        self.seed=dict(kind='primitive',operation='tautology');self.op=dict(kind='block',operation='generic')
    def pattern(self,name,nodes):return dict(name=name,nodes=nodes,span=nodes[-1]['offset']+1,size=len(nodes))
    def test_complete_nonlocal_and_external_contacts(self):
        lib=[self.pattern('nonlocal',[dict(offset=0,family=self.seed,refs=[]),dict(offset=2,family=self.op,refs=[0]),dict(offset=3,family=self.op,refs=[0,2])]),self.pattern('external',[dict(offset=0,family=self.op,refs=[-1]),dict(offset=1,family=self.op,refs=[0])])]
        self.assertEqual(J.instances(self.c,6,lib),H.instances(self.c,6,lib));self.assertTrue(J.instances(self.c,6,lib))
    def test_repeated_contacts_are_functional(self):
        lib=[self.pattern('repeat',[dict(offset=0,family=self.seed,refs=[]),dict(offset=1,family=self.op,refs=[0,0])])]
        actual=J.instances(self.c,3,lib);self.assertEqual(actual,H.instances(self.c,3,lib))
        for item in actual:
            self.assertEqual(self.c['rules'][item['members'][1][1]]['inputs'][0],self.c['rules'][item['members'][1][1]]['inputs'][1])
    def test_empty_library(self):self.assertEqual(J.instances(self.c,6,[]),[])
    def test_all_pattern_provenance_retained(self):
        nodes=[dict(offset=0,family=self.seed,refs=[]),dict(offset=1,family=self.op,refs=[0])];lib=[self.pattern('one',nodes),self.pattern('two',nodes)]
        actual=J.instances(self.c,4,lib);self.assertEqual(actual,H.instances(self.c,4,lib));self.assertTrue(all(x['patterns']==['one','two'] for x in actual))
if __name__=='__main__':unittest.main()
