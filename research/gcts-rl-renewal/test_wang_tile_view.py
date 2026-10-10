"""Validate new drawing data against the frozen searched point types."""
import copy,json,unittest
import export_wang_tile_view as E
from audit_serialized_kernel import freeze

class TileViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=json.loads((E.DOCS/'coarse-proofs-001.json').read_text())
        cls.parent=freeze(cls.raw)
        cls.reader=json.loads((E.DOCS/'wang-proofs-001.json').read_text())
        cls.draw=json.loads((E.DOCS/'wang-tiles-001.json').read_text())
        cls.evaluations={r['problem']['id']:r for r in cls.parent['evaluation']}
        cls.donors={r['problem']['id']:r for r in cls.parent['donors']}

    def source(self,proof):
        if proof['discovered_by']=='donor-gcts':
            row=self.donors[proof['id']];return row,row,()
        row=self.evaluations[proof['id']]
        run=next(r for r in row['runs'] if r['lane']==proof['discovered_by'] and r['replica']==proof['replica'])
        return row,run,self.parent['library'] if run['library'] else ()

    def test_exact_reader_and_parent_bindings(self):
        for key in ('parent','proof_reader'):
            binding=self.draw[key]
            self.assertEqual(binding['sha256'],E.file_sha(E.DOCS/binding['file']))
        self.assertEqual(self.draw['exporter_sha256'],E.file_sha(E.HERE/'export_wang_tile_view.py'))
        for name,pin in self.draw['dependencies'].items():self.assertEqual(pin,E.file_sha(E.HERE/name))
        for name,pin in self.raw['sources'].items():self.assertEqual(pin,E.file_sha(E.HERE/name))

    def test_every_selected_point_type_and_proof_link(self):
        self.assertEqual(len(self.draw['theorems']),10)
        self.assertEqual(sum(len(r['tiles']) for r in self.draw['theorems']),29)
        for proof,shown in zip(self.reader['theorems'],self.draw['theorems']):
            with self.subTest(theorem=proof['id']):
                row,run,library=self.source(proof)
                expected=E.record(row['problem'],run,row['catalog'],library,proof)
                self.assertEqual(shown,json.loads(json.dumps(expected)))
                c=row['catalog'];totals={};values={}
                for tile in shown['tiles']:
                    for p,v in tile['weights']:totals[tuple(p)]=totals.get(tuple(p),0)+v
                    for p,v in tile['marks']:
                        p=tuple(p)
                        if p in values:self.assertEqual(values[p],v)
                        values[p]=v
                    for output in tile['outputs']:
                        self.assertEqual(output['formula_id'],c['rules'][output['rule_id']]['output'])
                    for i in tile['root_lines']:
                        self.assertGreaterEqual(i,0);self.assertLess(i,len(proof['request']['proof']))
                self.assertEqual(totals,{(2*j,0):12 for j in range(shown['length'])})
                self.assertEqual(values[(2*(shown['length']-1),1)],shown['target_id'])

    def test_remote_marks_are_present_without_remote_occupancy(self):
        for row in self.draw['theorems']:
            with self.subTest(theorem=row['id']):
                distant=[]
                for tile in row['tiles']:
                    cells={k[0] for k in tile['members']}
                    distant.extend(p for p,v in tile['marks'] if p[1]==1 and p[0]//2 not in cells)
                self.assertTrue(distant)
        self.assertTrue(any(len(t['members'])>1 for r in self.draw['theorems'] for t in r['tiles']))

    def test_changed_certificate_cannot_be_displayed(self):
        proof=copy.deepcopy(self.reader['theorems'][0]);row,run,library=self.source(proof)
        proof['certificate_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'certificate/run binding'):
            E.record(row['problem'],run,row['catalog'],library,proof)

    def test_changed_problem_cannot_be_displayed(self):
        proof=copy.deepcopy(self.reader['theorems'][0]);row,run,library=self.source(proof)
        proof['problem_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'external theorem binding'):
            E.record(row['problem'],run,row['catalog'],library,proof)

    def test_changed_root_line_binding_is_rejected(self):
        proof=self.reader['theorems'][0];row,run,library=self.source(proof)
        changed=copy.deepcopy(run['hierarchy']);changed['request']['proof'][1]['formula']=('bot',)
        with self.assertRaisesRegex(ValueError,'metatile/root line binding'):
            E.root_links(row['catalog'],run['result'],changed)

if __name__=='__main__':unittest.main(verbosity=2)
