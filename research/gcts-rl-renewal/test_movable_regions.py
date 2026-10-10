import copy
import itertools
import unittest

import movable_proof_regions as M
import check_movable_regions as A
import quantified_receptors as Q
from quantified_receptor_cases import registry
from audit_serialized_kernel import replay
from serialized_kernel import canonical


class MovableRegionTests(unittest.TestCase):
    def setUp(self):
        cases, _ = registry()
        self.spec = copy.deepcopy(cases[0])
        self.spec['bound'] = self.spec.pop('length')
        self.cat = Q.inventory(self.spec['theory'], self.spec['hypotheses'],
                               self.spec['terms'], self.spec['variables'],
                               self.spec['rounds'],
                               generalization_rounds=self.spec['generalization_rounds'])

    def model(self, marking=(), spec=None):
        d = spec or self.spec
        return M.Model(self.cat, d['target'], d['bound'], d['hypotheses'], marking)

    def compare(self, m, s, g, spec=None):
        expected = A.domains(self.cat['rules'], spec or self.spec, s.order, m.marking)
        self.assertEqual(expected, {p: list(d) for p, d in g.domains.items()})
        for p, keys in expected.items():
            self.assertEqual(len(keys), len(g.domains[p]))
            for k in keys:
                self.assertEqual(g.candidate_points(k), {p})
                self.assertTrue(s.legal(m.placement(k)))

    def test_initial_complete_graph_and_exact_boundaries(self):
        m = self.model()
        s = m.initial()
        self.assertEqual(s.marks[M.flow(0)], 1)
        self.assertEqual(s.marks[M.flow(m.length)], 0)
        g = M.Graph(m, s)
        self.compare(m, s, g)
        self.assertEqual(m.context_hash(), A.context_hash(self.cat, self.spec))
        for value in (None, 1):
            bad = s.copy()
            if value is None:
                del bad.marks[M.flow(m.length)]
            else:
                bad.marks[M.flow(m.length)] = value
            with self.assertRaises(ValueError):
                M.Graph(m, bad)

    def test_partial_states_and_complete_rollback(self):
        m = self.model()
        result = M.search(m)
        s = m.initial()
        g = M.Graph(m, s)
        for key in result['placements']:
            original = (copy.deepcopy(s), g.fingerprint())
            ss, gg = s.copy(), g.copy()
            gg.update(m, ss, ss.place(m.placement(key)))
            self.compare(m, ss, gg)
            self.assertEqual((s, g.fingerprint()), original)
            s, g = ss, gg
        self.assertFalse(s.frontier())
        self.assertTrue(all(v == 1 for v in s.tile_generations))

    def test_brute_point_legality_equals_factor_domains(self):
        d = copy.deepcopy(self.spec)
        d['bound'] = 2
        m = self.model(spec=d)
        s = m.initial()
        g = M.Graph(m, s)
        for _ in range(3):
            expected = A.domains(self.cat['rules'], d, s.order)
            brute = {p: [] for p in s.frontier()}
            for j in range(m.length):
                keys = [(j, M.PAD, ())]
                if j or m.hypotheses:
                    keys.append((j, M.END, ()))
                if j < m.bound:
                    for rid, r in enumerate(self.cat['rules']):
                        for refs in itertools.product(range(-len(m.hypotheses), j), repeat=len(r['inputs'])):
                            if all(refs[a] != refs[b] or r['inputs'][a] == r['inputs'][b]
                                   for a in range(len(refs)) for b in range(a)):
                                keys.append((j, rid, refs))
                for key in keys:
                    c = m.placement(key)
                    if Q.cell(j) in brute and s.legal(c):
                        brute[Q.cell(j)].append(key)
            self.assertEqual(expected, brute)
            self.compare(m, s, g, d)
            kind, p, keys = g.decision(s)
            if kind in ('empty', 'dead'):
                break
            key = keys[0] if len(keys) == 1 else next(iter(keys))
            g.update(m, s, s.place(m.placement(key)))

    def test_tree_certificate_and_actual_closure_cluster(self):
        m = self.model()
        r = M.search(m, collect_pairs=True)
        self.assertTrue(A.tree(self.cat['rules'], self.spec, r)['outcome'])
        r['closing_cluster'] = M.closing_cluster(m, r['endpoint'])
        tiles = [dict(key=k, occupancy=m.placement(k).occupancy, marks=m.placement(k).marks)
                 for k in r['placements']]
        self.assertEqual(A.certificate(self.cat['rules'], self.spec, r, tiles)['endpoint'], 4)
        self.assertEqual(A.cluster(self.cat['rules'], self.spec, r)['cells'], 1)
        bad = copy.deepcopy(tiles)
        bad[0]['marks'] = tuple((p, 1-v if p[1] == -2 else v) for p, v in bad[0]['marks'])
        with self.assertRaises(ValueError):
            A.certificate(self.cat['rules'], self.spec, r, bad)

    def test_certified_failures_become_actual_remote_marks(self):
        m = self.model()
        base = M.search(m, collect_pairs=True)
        for item in base['negatives']:
            self.assertFalse(A.tree(self.cat['rules'], self.spec, seeds=item['pair'],
                                    node=item['tree'])['outcome'])
        pairs = [r['pair'] for r in base['negatives']]
        marked = self.model(pairs)
        a, b = pairs[0]
        self.assertIn((M.learning_point(0), 0), marked.placement(a).marks)
        self.assertIn((M.learning_point(0), 1), marked.placement(b).marks)
        s = marked.initial()
        g = M.Graph(marked, s)
        g.update(marked, s, s.place(marked.placement(a)))
        self.assertFalse(s.legal(marked.placement(b)))
        self.compare(marked, s, g)
        warm = M.search(marked)
        self.assertLess(warm['metrics']['nodes'], base['metrics']['nodes'])
        self.assertTrue(A.tree(self.cat['rules'], self.spec, warm, pairs)['outcome'])
        # Learned points are absent from the mathematical kernel's proof.
        request = M.compile_region(warm['proof'], marked.target, marked.hypotheses,
                                   self.spec['theory'], True)['request']
        self.assertEqual(replay(canonical(request))['status'], 'accepted')

    def test_scope_and_capture_controls(self):
        cases, _ = registry()
        for d in cases:
            if d['id'] not in ('scope-reject', 'capture-safe', 'capture-reject'):
                continue
            d = copy.deepcopy(d)
            d['bound'] = d.pop('length')
            cat = Q.inventory(d['theory'], d['hypotheses'], d['terms'], d['variables'],
                              d['rounds'], generalization_rounds=d['generalization_rounds'])
            m = M.Model(cat, d['target'], d['bound'], d['hypotheses'])
            r = M.search(m)
            self.assertEqual(r['status'], 'finite_exact_proof_region'
                             if d['id'] == 'capture-safe' else 'exhausted_finite_region')
            self.assertEqual(A.tree(cat['rules'], d, r)['outcome'], d['id'] == 'capture-safe')

    def test_zero_inference_rows_and_padding_are_not_proof_steps(self):
        d = copy.deepcopy(self.spec)
        d['target'] = d['hypotheses'][-1]
        m = self.model(spec=d)
        r = M.search(m)
        self.assertEqual(r['endpoint'], 0)
        self.assertEqual(r['proof'], [])
        self.assertEqual(len(r['placements']), d['bound']+1)
        self.assertTrue(A.tree(self.cat['rules'], d, r)['outcome'])
        compiled = M.compile_region([], d['target'], d['hypotheses'], d['theory'], True)
        self.assertEqual(replay(canonical(compiled['request']))['status'], 'accepted')

    def test_global_dead_forced_generation_order(self):
        m = self.model()
        s = m.initial()
        g = M.Graph(m, s)
        # Synthetic complete graph tests order, not a geometry claim.
        base = Q.Domain(0, 2, ())
        g.domains = {(0, 0): M.Domain(base, ((0, -2, ()),)),
                     (2, 0): M.Domain(base, ())}
        self.assertEqual(g.decision(s)[0:2], ('dead', (2, 0)))
        g.domains[(2, 0)] = M.Domain(base, ((1, -2, ()), (1, -1, ())))
        self.assertEqual(g.decision(s)[0:2], ('forced', (0, 0)))
        g.domains[(0, 0)] = M.Domain(base, ((0, -2, ()), (0, -1, ()), (0, 0, ())))
        s.generations[(0, 0)] = 0
        s.generations[(2, 0)] = 1
        self.assertEqual(g.decision(s)[0:2], ('branch', (0, 0)))

    def test_budget_is_unknown_and_contexts_do_not_transfer(self):
        m = self.model()
        r = M.search(m, node_limit=1)
        self.assertEqual(r['status'], 'unknown_search_budget')
        self.assertIsNone(r['search_tree'])
        other = self.model(spec=dict(self.spec, bound=5))
        self.assertNotEqual(m.context_hash(), other.context_hash())


if __name__ == '__main__':
    unittest.main()
