#!/usr/bin/env python3
"""JSON-lines incremental signed marking synthesis. Requires z3-solver.

An assigned component is an integer, an unassigned component is *. Positive
patch overlaps imply equality only when both slots are assigned. Each negative
pair needs at least one assigned disagreement. SAT is restricted to the supplied
finite support and signed component action; it is not an infinite-tiling claim.
"""
import json
import sys
import time
import z3

class MarkingSolver:
    def __init__(self, n, timeout_ms=500):
        self.n = n
        self.solver = z3.Solver()
        self.solver.set(timeout=timeout_ms, random_seed=17)
        self.assigned = [z3.Bool(f'a{i}') for i in range(n)]
        self.values = [z3.Int(f'v{i}') for i in range(n)]
        # Every satisfiable signed equality/disequality pattern on n variables
        # has a representative using 0 and at most n distinct magnitudes.
        self.solver.add(*[z3.And(v >= -n, v <= n) for v in self.values])
        self.negative = []
        self.seen_equalities = set()

    def add(self, positive, contacts):
        if positive:
            for i, j, sign in contacts:
                edge = (min(i,j), max(i,j), sign)
                if edge in self.seen_equalities:
                    continue
                self.seen_equalities.add(edge)
                self.solver.add(z3.Implies(z3.And(self.assigned[i], self.assigned[j]), self.values[i] == sign*self.values[j]))
        else:
            self.negative.append(contacts)
            self.solver.add(z3.Or(*[z3.And(self.assigned[i], self.assigned[j], self.values[i] != sign*self.values[j]) for i,j,sign in contacts]))

    def solve(self):
        started = time.perf_counter()
        status = self.solver.check()
        if status != z3.sat:
            return {'status': str(status), 'reason': self.solver.reason_unknown() if status == z3.unknown else 'inconsistent finite support', 'solveMs': (time.perf_counter()-started)*1000}
        model = self.solver.model()
        values = [model.eval(v, model_completion=True).as_long() if z3.is_true(model.eval(a, model_completion=True)) else None for a,v in zip(self.assigned,self.values)]
        # Erasing an assignment cannot hurt positive agreement. Keep a witness
        # for every negative; this is a reduction, not re-encoding equalities.
        for i, old in enumerate(values):
            if old is None:
                continue
            values[i] = None
            if any(not any(values[a] is not None and values[b] is not None and values[a] != sign*values[b] for a,b,sign in contacts) for contacts in self.negative):
                values[i] = old
        return {'status':'sat', 'values':values, 'solveMs':(time.perf_counter()-started)*1000}

if __name__ == '__main__':
    solver = None
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if request['op'] == 'init':
                solver = MarkingSolver(request['n'], request.get('timeoutMs',500))
                response = {'status':'ready', 'z3':z3.get_version_string()}
            else:
                for row in request.get('constraints',[]):
                    solver.add(row['positive'], row['contacts'])
                response = solver.solve()
            print(json.dumps(response), flush=True)
        except Exception as error:
            print(json.dumps({'status':'error','message':str(error)}),flush=True)
