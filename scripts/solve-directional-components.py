"""Finite {-1,0,+1,*} feasibility check; requires the optional z3-solver package.
Input is generated from unmarked pair labels, never a known marking.
"""
import json
import sys
import z3

data = json.load(sys.stdin)
assigned = [z3.Bool(f'a{i}') for i in range(len(data['support']))]
values = [z3.Int(f'v{i}') for i in range(data['lineCount'])]
solver = z3.Solver()
solver.set(timeout=20000)
solver.add(*[z3.And(v >= -1, v <= 1) for v in values])
for row in data['rows']:
    conflicts = [z3.And(assigned[i], assigned[j],
                       values[data['lines'][i]] != sign * values[data['lines'][j]])
                 for i, j, sign in row['pairs']]
    rejects = z3.Or(conflicts)
    solver.add(z3.Not(rejects) if row['status'] == 'valid' else rejects)
result = solver.check()
output = {'result': str(result), 'solverVersion': z3.get_version_string()}
if result == z3.sat:
    model = solver.model()
    output['support'] = [dict(entry, value=model.eval(values[data['lines'][i]],
                         model_completion=True).as_long())
                         for i, entry in enumerate(data['support'])
                         if z3.is_true(model.eval(assigned[i], model_completion=True))]
elif result == z3.unknown:
    output['reason'] = solver.reason_unknown()
json.dump(output, sys.stdout)
