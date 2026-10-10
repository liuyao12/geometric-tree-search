"""Soundness hazards, complete tiny solution sets, graph equality and rollback."""
import copy
import itertools
import unittest

import dependency_budget as B
import dependency_budget_search as S
import check_dependency_budget as V
import movable_proof_regions as M
from quantifier_family_cases import case
from run_adaptive_clusters import inventory
from quantifier_family_search import search as frozen_search


def model(spec, marked=True):
    cat = inventory(spec)
    original = B.Model(cat, spec['target'], spec['bound'], spec['hypotheses'])
    cert = B.synthesis(original)
    V.certificate(cat['rules'], spec, cert)
    return (B.Model(cat, spec['target'], spec['bound'], spec['hypotheses'],
                    cert if marked else None), cert)


class Tests(unittest.TestCase):
    def test_cycles_do_not_erase_necessary_outputs(self):
        spec = case('dependency-test-cycle', hops=3)
        m, cert = model(spec)
        self.assertEqual(m.requirements[m.target], 8)
        self.assertGreater(len(cert['rounds']), 2)
        result = S.search(m)
        self.assertEqual(result['status'], 'finite_exact_proof_region')
        result['tiles'] = [dict(key=k, occupancy=m.placement(k).occupancy,
                                marks=m.placement(k).marks) for k in result['placements']]
        V.replay(m.catalog['rules'], spec, result, m.requirements)

    def test_shared_alternative_and_cyclic_grammars_preserve_all_solutions(self):
        # Abstract finite rule systems isolate AND/OR sharing and cycles.
        # They are combinatorial fixtures, not displayed mathematical proofs.
        a, b, c, d = [('pred', x, ()) for x in ('a', 'b', 'c', 'd')]
        systems = [[((a,), b), ((a,), c), ((b, c), d)],
                   [((a,), b), ((b,), d), ((a,), d)],
                   [((a,), b), ((b,), c), ((c,), b), ((b, c), d)],
                   [((a, a), b), ((b,), d)], [((b,), c), ((c,), b)]]
        for system in systems:
            rules = [dict(kind='fixture', inputs=ps, output=f,
                          guards=(), parameters={}) for ps, f in system]
            cat = dict(rules=rules, variables=(), formulas=[a, b, c, d])
            spec = dict(hypotheses=(a,), target=d, bound=3, variables=(),
                        theory=dict(functions={}, predicates={x: 0 for x in ('a', 'b', 'c', 'd')}, axioms={}))
            plain = B.Model(cat, d, 3, (a,));cert = B.synthesis(plain)
            V.certificate(rules, spec, cert)
            marked = B.Model(cat, d, 3, (a,), cert)
            solutions = []
            def enumerate_all(chosen, known):
                j = len(chosen)
                if known[j-1] == d:
                    solutions.append(tuple(chosen)+((j, -1, ()),)+tuple((i, -2, ()) for i in range(j+1, 4)))
                if j == 3:
                    return
                for rid, rule in enumerate(rules):
                    choices = [[i for i, f in known.items() if f == p] for p in rule['inputs']]
                    for refs in itertools.product(*choices):
                        enumerate_all(chosen+[(j, rid, refs)], dict(known, **{}) | {j: rule['output']})
            enumerate_all([], {-1: a})
            for keys in solutions:
                for m in (plain, marked):
                    state = m.initial()
                    for key in keys:
                        self.assertTrue(state.legal(m.placement(key)))
                        state.place(m.placement(key))
                    self.assertFalse(state.frontier())
            self.assertEqual(len(solutions), len(set(solutions)))

    def test_literal_domains_and_exact_parent_rollback(self):
        spec = case('dependency-test-graph', nested=True, compound=True, hops=2)
        m, cert = model(spec);state=m.initial();graph=B.Graph(m, state)
        pending=[(state, graph)];visited=0
        while pending and visited < 120:
            state, graph = pending.pop();visited += 1
            explicit = V.domains(m.catalog['rules'], spec, state.order, m.requirements)
            self.assertEqual({p: sorted(d) for p, d in graph.domains.items()},
                             {p: sorted(d) for p, d in explicit.items()})
            self.assertEqual(graph.decision(state)[:2], V.A.decide(explicit)[:2])
            before, fingerprint = state.copy(), graph.fingerprint()
            kind, p, keys = graph.decision(state)
            if kind in ('branch', 'forced'):
                for key in list(keys)[:3]:
                    self.assertTrue(state.legal(m.placement(key)))
                    child, cg = state.copy(), graph.copy()
                    cg.update(m, child, child.place(m.placement(key)))
                    pending.append((child, cg))
            self.assertEqual(state, before)
            self.assertEqual(graph.fingerprint(), fingerprint)
        self.assertGreater(visited, 15)
        invalid=m.initial();invalid.marks[B.point(0)]=1
        with self.assertRaises(ValueError):B.Graph(m, invalid)

    def test_certificate_corruptions_are_rejected(self):
        spec=case('dependency-test-corrupt');m, cert=model(spec)
        for name in ('context', 'given', 'eligible', 'round', 'required'):
            broken=copy.deepcopy(cert)
            if name=='context':broken['context_sha256']='!'
            elif name=='given':broken['given']=[]
            elif name=='eligible':broken['eligible_rules'].pop()
            elif name=='round':broken['rounds'][0][cert['target']]=[]
            else:broken['required'][cert['target']]+=1
            with self.assertRaises(ValueError):V.certificate(m.catalog['rules'], spec, broken)

    def test_unmarked_adapter_matches_frozen_baseline_and_cutoffs_replay(self):
        spec=case('dependency-test-base', nested=True);m, cert=model(spec, False)
        result=S.search(m);old=frozen_search(M.Model(m.catalog, m.target, m.bound, m.hypotheses), attempts=50000, seconds=60)
        for name in ('status', 'placements', 'proof', 'endpoint', 'tile_generations', 'candidate_universe'):
            self.assertEqual(result[name], old[name])
        self.assertEqual(result['metrics']['attempts'], old['metrics']['attempts'])
        def shape(t):return (t['kind'], t['point'], tuple((ch['key'],shape(ch['tree'])) for ch in t['children']))
        self.assertEqual(shape(result['search_tree']), shape(old['search_tree']))
        small=S.search(model(spec, False)[0], attempts=2)
        self.assertEqual(small['status'], 'unknown_search_budget')
        V.replay(m.catalog['rules'], spec, small, None)
        bad=copy.deepcopy(small);bad['status']='exhausted_finite_region'
        with self.assertRaises(ValueError):V.replay(m.catalog['rules'], spec, bad, None)


if __name__ == '__main__':
    unittest.main()
