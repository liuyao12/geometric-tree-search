#!/usr/bin/env python3
"""Add observational hooks to PySAT's prepared Glucose 3.0 Solver.cc.

Usage: python3 scripts/instrument-nonacube-glucose.py /path/to/pysat
Prepare only glucose30 using solvers/prepare.py first. Hooks do not change
assignments, branching, propagation, clause learning, or restart policy.
"""
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / 'solvers/glucose30/core/Solver.cc'
s = p.read_text()
def replace(old, new):
    global s
    assert s.count(old) == 1, (old, s.count(old))
    s = s.replace(old, new)
replace('using namespace Glucose30;', 'extern void gcts_trace(int, int, int);\nusing namespace Glucose30;')
replace('            assigns [x] = g3l_Undef;', '            if (x > 0 && x <= 8140 && !sign(trail[c])) gcts_trace(2, x, level);\n            assigns [x] = g3l_Undef;')
replace('        trail_lim.shrink(trail_lim.size() - level);', '        trail_lim.shrink(trail_lim.size() - level);\n        gcts_trace(5, level, 0);')
replace('    trail.push_(p);', '    trail.push_(p);\n    if (var(p) > 0 && var(p) <= 8140 && !sign(p)) gcts_trace(1, var(p), decisionLevel());')
replace('    starts++;', '    starts++;\n    gcts_trace(6, starts, decisionLevel());')
replace('            // CONFLICT\n', '            // CONFLICT\n            gcts_trace(4, decisionLevel(), ca[confl].size());\n')
replace("            // Increase decision level and enqueue 'next'", "            gcts_trace(3, var(next) * (sign(next) ? -1 : 1), decisionLevel());\n            // Increase decision level and enqueue 'next'")
p.write_text(s)
print('Installed six observational hooks in', p)
