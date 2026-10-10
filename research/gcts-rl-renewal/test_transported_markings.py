import copy
import json
import unittest
from pathlib import Path

import transported_markings as T
import check_transported_markings as V
import movable_proof_regions as M
import check_movable_regions as A

DOC = Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'


class TransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((DOC/'movable-regions-001.json').read_text())
        cls.source = cls.data['cases'][0]
        cls.checks = V.certify_donor(cls.source)

    def setup(self, changed=True, extra=4):
        s, mapping = T.recipient(self.source, changed, extra)
        catalog = T.inventory(s)
        proposal = T.propose(self.source, s, catalog, mapping)
        return s, catalog, proposal

    def test_rename_rule_permutation_and_boundary_extension(self):
        s, c, p = self.setup()
        checked = V.verify(self.source, s, c, p, self.checks)
        self.assertEqual(len(checked['pairs']), 4)
        self.assertGreater(checked['changed_rule_ids'], 0)
        self.assertNotEqual(p['source_context'], p['target_context'])

    def test_actual_remote_values_and_complete_domains(self):
        s, c, p = self.setup()
        pairs = V.verify(self.source, s, c, p, self.checks)['pairs']
        m = M.Model(c, s['target'], s['bound'], s['hypotheses'], pairs)
        state = m.initial()
        graph = M.Graph(m, state)
        first, second = pairs[0]
        graph.update(m, state, state.place(m.placement(first)))
        expected = A.domains(c['rules'], s, state.order, pairs)
        self.assertEqual({k: list(d) for k, d in graph.domains.items()}, expected)
        self.assertNotIn(second, graph.domains[A.cell(second[0])])
        self.assertEqual(dict(m.placement(first).marks)[M.learning_point(0)], 0)
        self.assertEqual(dict(m.placement(second).marks)[M.learning_point(0)], 1)

    def test_positive_solution_crops_to_the_donor(self):
        s, c, p = self.setup()
        m = M.Model(c, s['target'], s['bound'], s['hypotheses'])
        result = M.search(m)
        cropped = V.crop(self.source, s, c, p, result)
        old_spec = M.freeze(self.source['spec'])
        old = M.Model(T.inventory(old_spec), old_spec['target'], old_spec['bound'], old_spec['hypotheses'])
        state = old.initial()
        for key in cropped:
            state.place(old.placement(key))
        self.assertFalse(state.frontier())

    def test_budget_cutoff_is_not_a_failure_certificate(self):
        source = copy.deepcopy(self.source)
        source['certified'][0]['tree'] = None
        with self.assertRaises((ValueError, TypeError)):
            V.certify_donor(source)

    def test_unsafe_transport_is_rejected(self):
        for kind in ('target', 'hypotheses', 'arity', 'symbols', 'guard', 'rule-map',
                     'metadata', 'bound', 'context', 'closing', 'donor-check'):
            with self.subTest(kind=kind):
                s, c, p = self.setup()
                source, checks = copy.deepcopy(self.source), copy.deepcopy(self.checks)
                if kind == 'target':
                    s['target'] = ('bot',)
                elif kind == 'hypotheses':
                    s['hypotheses'] += (s['target'],)
                elif kind == 'arity':
                    s['theory']['predicates']['Supports'] = 2
                elif kind == 'symbols':
                    p['mapping']['predicates']['Q'] = 'Supports'
                elif kind == 'guard':
                    c['rules'][0]['guards'] = () if c['rules'][0]['guards'] else ('x',)
                elif kind == 'rule-map':
                    p['rule_map'][0] = p['rule_map'][1]
                elif kind == 'metadata':
                    c['variables'] = ('x',)
                elif kind == 'bound':
                    s['bound'] = 3
                elif kind == 'context':
                    p['source_context'] = '0'*64
                elif kind == 'closing':
                    p['certificates'][0]['maximum_endpoint'] = 100
                elif kind == 'donor-check':
                    checks[0]['certificate_sha256'] = '0'*64
                p['target_context'] = A.context_hash(c, s)
                with self.assertRaises((ValueError, KeyError, TypeError, IndexError)):
                    V.verify(source, s, c, p, checks)

    def test_no_closing_seed_cannot_be_transferred(self):
        source = copy.deepcopy(self.source)
        source['spec']['bound'] = 2
        rules = T.inventory(source['spec'])['rules']
        first = next(i for i, r in enumerate(rules) if r['kind']=='forall-elim'
                     and r['inputs'][0] == M.freeze(source['spec']['hypotheses'][0])
                     and r['parameters']['term'] == ('var','x'))
        second = next(i for i, r in enumerate(rules) if r['kind']=='forall-elim'
                      and r['inputs'][0] == M.freeze(source['spec']['hypotheses'][1])
                      and r['parameters']['term'] == ('var','x'))
        pair = ((0, first, (-2,)), (1, second, (-1,)))
        d = M.freeze(source['spec'])
        old = M.Model(T.inventory(d),d['target'],d['bound'],d['hypotheses'])
        failed = M.search(old,seeds=pair)
        self.assertEqual(failed['status'],'exhausted_finite_region')
        source['context_hash'] = old.context_hash()
        source['certified'] = [dict(pair=pair,tree=failed['search_tree'])]
        checks = V.certify_donor(source)
        s, mapping = T.recipient(source,False,2)
        c = T.inventory(s)
        p = T.propose(source,s,c,mapping)
        with self.assertRaisesRegex(ValueError, 'closing seed'):
            V.verify(source, s, c, p, checks)
        new = M.Model(c,s['target'],s['bound'],s['hypotheses'])
        success = M.search(new,seeds=pair)
        self.assertEqual(success['status'],'finite_exact_proof_region')


if __name__ == '__main__':
    unittest.main()
