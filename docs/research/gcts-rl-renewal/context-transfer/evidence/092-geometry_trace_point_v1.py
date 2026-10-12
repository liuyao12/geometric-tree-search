"""Independent literal point-domain reconstruction, with proved-child exclusions.

No production graph, factor helper, controller, ranker, search or decoder import.
The old independent State supplies unit t / assigned m updates only. This new
adapter derives full domains from all ordered literal reference bindings and
adds exclusions/semantic snapshots that the old controlled-only audit forbade.
"""
import copy
from full_point_oracle_v1 import State, canonical, digest, integer, need, points


def key_data(key):
    return [key[0], key[1], list(key[2])]


def literal_key(value):
    need(type(value) is list and len(value) == 3 and type(value[2]) is list,
         "exact three-field candidate key")
    return integer(value[0]), integer(value[1]), tuple(integer(v) for v in value[2])


class PointState(State):
    def base_legal(self, key):
        i, row, refs = key
        integer(i); integer(row)
        need(0 <= i < len(self.recipes) and 0 <= row < self.height, "complete key boundary")
        try:
            t, m = points(self.recipes[i], row, refs, self.height)
        except ValueError:
            return False
        return self.totals[row] == 0 and self.compatible(m)

    def legal(self, key):
        return self.base_legal(key) and key not in self.excluded[key[1]]

    def candidates(self, row, include_excluded=False):
        """Direct literal port binding enumeration, independent of factor tables.

        Every raw negative offset maps either to a prior nonnegative row or an
        exterior point. All exterior formula points are assigned -1; all recipe
        formula codes are nonnegative, so precisely the negative references are
        rejected. Per-port tests are ordinary assigned m agreement, including
        offset points. The only joint port interaction is conflicting values at
        one shared formula point; repeated equal ports retain multiplicity.
        """
        integer(row); need(0 <= row < self.height, "required row")
        if self.totals[row]:
            return
        marks = self.marks
        for i, recipe in enumerate(self.recipes):
            if (1, row) in marks and marks[1, row] != recipe["output"]:
                continue
            if not recipe["inputs"]:
                k = (i, row, ())
                if include_excluded or k not in self.excluded[row]:
                    yield k
                continue
            need(len(recipe["inputs"]) == 2, "two exact ordered primitive MP ports")
            permitted = []
            for port, code in enumerate(recipe["inputs"]):
                permitted.append([ref for ref in range(row)
                    if ((1, ref) not in marks or marks[1, ref] == code)
                    and ((2 + port, row) not in marks or marks[2 + port, row] == ref - row)])
            for a in permitted[0]:
                for b in permitted[1]:
                    if a == b and recipe["inputs"][0] != recipe["inputs"][1]:
                        continue
                    k = (i, row, (a, b))
                    if include_excluded or k not in self.excluded[row]:
                        yield k

    def semantic(self):
        domains = []
        for row in range(self.height):
            factors = []
            if not self.totals[row]:
                for i, recipe in enumerate(self.recipes):
                    if (1, row) in self.marks and self.marks[1, row] != recipe["output"]:
                        continue
                    if not recipe["inputs"]:
                        factors.append([i, 0, 0, False, 1]); continue
                    options = []
                    for port, code in enumerate(recipe["inputs"]):
                        options.append([ref for ref in range(row)
                            if ((1, ref) not in self.marks or self.marks[1, ref] == code)
                            and ((2 + port, row) not in self.marks or self.marks[2 + port, row] == ref - row)])
                    different = recipe["inputs"][0] != recipe["inputs"][1]
                    # Explicitly enumerate every allowed ordered binding. No
                    # production mask multiplication or producer count is used.
                    count = sum(1 for a in options[0] for b in options[1]
                                if not different or a != b)
                    if count:
                        factors.append([i, sum(1 << r for r in options[0]),
                            sum(1 << r for r in options[1]), different, count])
            base_count = sum(f[4] for f in factors)
            removed = [k for k in sorted(self.excluded[row]) if self.base_legal(k)]
            domains.append(dict(factors=factors, base_count=base_count,
                excluded_legal=[key_data(k) for k in removed], count=base_count-len(removed)))
        return dict(totals=list(self.totals),
            marks=[[x, y, v, self.refs[x, y]] for (x, y), v in sorted(self.marks.items())],
            order=[key_data(k) for k in self.order],
            selected_generations=[[key_data(k), self.selected[k]] for k in sorted(self.selected)],
            roots=list(self.roots), excluded=[[key_data(k) for k in sorted(s)] for s in self.excluded],
            domains=domains, model_epoch=self.epoch)


def decision(full):
    g = full["graph"]
    rows = [r for r, t in enumerate(g["totals"]) if t < 1]
    if not rows:
        return ["complete", None, 0, None]
    generation = lambda r: min([g["roots"][r]] + [v for k, v in g["selected_generations"] if k[1] == r])
    for kind, count in (("dead", 0), ("forced", 1)):
        matching = [r for r in rows if g["domains"][r]["count"] == count]
        if matching:
            row = min(matching)
            return [kind, row, count, generation(row)]
    row = min(rows, key=lambda r: (generation(r), g["domains"][r]["count"], r))
    return ["branch", row, g["domains"][row]["count"], generation(row)]


class TransactionState:
    """Independent deep snapshots; no producer trail/rollback implementation."""
    def __init__(self, state, body_epoch):
        self.state, self.body_epoch = state, body_epoch
        self.graph_trail = 0; self.hint_trail = 0; self.revision = 1
        self.cache = {}; self.censuses = []

    def graph_key(self):
        s = self.state
        return canonical([s.totals, sorted(s.marks.items()), sorted(s.refs.items()),
            s.order, sorted(s.selected.items()), [sorted(v) for v in s.excluded]])

    def full(self):
        cache_key = self.graph_key()
        if cache_key not in self.cache:
            graph = self.state.semantic()
            need(all(self.state.marks.get((1, r)) == -1 for r in range(-23, 0)),
                 "complete negative exterior is retained")
            need(all(type(v) is int and v >= 0 for recipe in self.state.recipes
                     for v in [recipe["output"], *recipe["inputs"]]), "exterior disjoint formula codes")
            # Cross-check the complete direct key stream census at every row,
            # including all base-legal excluded keys. These are exact ordered
            # bindings, not a finite shortlist or a producer factor iterator.
            row_counts = []
            for row, domain in enumerate(graph["domains"]):
                base = sum(1 for _ in self.state.candidates(row, include_excluded=True))
                legal = base - len(domain["excluded_legal"])
                need(base == domain["base_count"] and legal == domain["count"],
                     "independent complete row census/factor serialization")
                row_counts.append(dict(row=row, base=base, legal=legal))
            self.cache[cache_key] = graph
            self.censuses.append(dict(graph_sha256=digest(graph), rows=row_counts,
                complete_base_candidates=sum(v["base"] for v in row_counts),
                complete_legal_candidates=sum(v["legal"] for v in row_counts)))
        return dict(graph=self.cache[cache_key], hint_states=[], hint_revision=self.revision,
            descriptor_ids=[], root_rejected=[], authority_epoch=self.body_epoch)

    def checkpoint(self):
        return [self.graph_trail, self.hint_trail, self.revision, digest([]), digest(self.full())]

    def saved(self):
        return (copy.deepcopy(self.state), self.graph_trail, self.hint_trail, self.revision)

    def restore(self, saved):
        self.state, self.graph_trail, self.hint_trail, self.revision = copy.deepcopy(saved)

    def sync(self):
        self.hint_trail += 1; self.revision += 1

    def apply(self, k):
        need(self.state.legal(k), "chosen complete point-domain member")
        self.state.apply(k); self.graph_trail += 1; self.sync()

    def exclude(self, k):
        need(self.state.legal(k), "restored-parent legal child key before exclusion")
        self.state.excluded[k[1]].add(k); self.graph_trail += 1; self.sync()

    def compact(self):
        full = self.full(); projection = copy.deepcopy(full)
        for domain in projection["graph"]["domains"]:
            del domain["factors"]
        return dict(full_semantic_sha256=digest(full), projection=projection)
