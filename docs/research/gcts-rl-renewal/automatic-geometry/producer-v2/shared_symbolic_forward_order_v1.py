"""Fixed generic ordering of a COMPLETE chosen primitive point domain.

No target, theory name, geometry constant, proof word, pruning or training.
Recipe ASTs and selected outputs supply ranking features only.
"""
import json
import time


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def ast_nodes(value):
    if not isinstance(value, list):
        return 0
    tag = value[0]
    if tag in ('var', 'bot'):
        return 1
    if tag in ('fun', 'pred'):
        return 1 + sum(ast_nodes(x) for x in value[2])
    if tag == 'all':
        return 1 + ast_nodes(value[2])
    return 1 + sum(ast_nodes(x) for x in value[1:])


class ForwardOrder:
    def __init__(self, graph):
        started = time.perf_counter()
        self.graph = graph
        self.formula_index = {canonical(f): i for i, f in enumerate(graph.formulas)}
        self.features = []
        for recipe in graph.recipes:
            witness = recipe.witness
            universal, equality, antecedent = None, None, None
            if witness['rule'] == 'instantiate':
                universal = self.formula_index.get(canonical(witness['universal']))
            elif witness['rule'] == 'eq_subst':
                # Reading the already checked recipe AST is a ranking feature;
                # this does not apply a substitution or establish an inference.
                out = witness['formula']
                equality = self.formula_index.get(canonical(out[1]))
                antecedent = self.formula_index.get(canonical(out[2][1]))
            self.features.append((witness['rule'], universal, equality, antecedent,
                                  ast_nodes(witness['formula']), canonical(witness)))
        self.metrics = {'feature_preparation_seconds': time.perf_counter() - started,
                        'feature_seconds': 0.0, 'sort_seconds': 0.0, 'permutation_check_seconds': 0.0,
                        'calls': 0, 'complete_keys_ranked': 0}

    def order(self, keys):
        started = time.perf_counter()
        g = self.graph
        proved = {g.recipes[k.recipe].output for k in g.selected}
        scored = []
        for key in keys:
            recipe = g.recipes[key.recipe]
            rule, universal, equality, antecedent, size, witness = self.features[key.recipe]
            if recipe.output in proved:
                tier = 6
            elif rule == 'mp' and all(any(k.row == ref for k in g.selected) for ref in key.refs):
                tier = 0
            elif rule == 'instantiate' and universal in proved:
                tier = 1
            elif rule == 'eq_subst' and equality in proved and antecedent in proved:
                tier = 2
            elif rule == 'axiom':
                tier = 3
            elif rule == 'eq_subst' and equality in proved:
                tier = 4
            else:
                tier = 5
            scored.append(((tier, size, witness, key.recipe, key.refs), key))
        self.metrics['feature_seconds'] += time.perf_counter() - started
        started = time.perf_counter()
        scored.sort(key=lambda value: value[0])
        ordered = [key for _, key in scored]
        self.metrics['sort_seconds'] += time.perf_counter() - started
        started = time.perf_counter()
        if len(ordered) != len(keys) or len(set(ordered)) != len(keys) or set(ordered) != set(keys):
            raise AssertionError('fixed order dropped or duplicated a legal base candidate')
        self.metrics['permutation_check_seconds'] += time.perf_counter() - started
        self.metrics['calls'] += 1
        self.metrics['complete_keys_ranked'] += len(keys)
        return ordered
