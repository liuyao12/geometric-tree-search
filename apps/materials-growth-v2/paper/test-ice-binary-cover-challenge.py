"""Exhaustive small GF(2) controls for the independent challenge verifier."""
import importlib.util
from pathlib import Path
import random
import numpy as np

spec=importlib.util.spec_from_file_location('verifier',Path(__file__).with_name('verify-ice-binary-cover-challenge.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
rng=random.Random(1701);checked=0
for n in range(1,9):
    for trial in range(20):
        rows={rng.randrange(1<<n) for _ in range(12)};A=v.rref(rows,n)
        solutions=[bits for bits in range(1<<n) if all((bits&row).bit_count()%2==0 for row in rows)]
        assert len(solutions)==1<<(n-len(A))
        forced={i for i in range(n) if all(not ((bits>>i)&1) for bits in solutions)}
        assert forced=={int(np.flatnonzero(row)[0]) for row in A if np.count_nonzero(row)==1}
        for bits in range(1<<n):
            values=np.array([(bits>>i)&1 for i in range(n)])
            assert (not np.any((A.astype(int)@values)%2))==(bits in solutions)
            checked+=1
for n in (3,4,5,6):
    c={'atoms':n,'occurrences':[{'matched':True,'type':0,'ids':[i,(i+1)%n],'permutation':[0,1]} for i in range(n)]}
    rows,components=v.equations(c,list(range(n)),{'ports':{'0':[0,1]}},[0])
    assert rows==({1} if n%2 else set()) and components==1
    try:v.equations(c,list(range(n))+[0],{'ports':{'0':[0,1]}},[0])
    except AssertionError:pass
    else:raise AssertionError('duplicate physical placement accepted')
    try:v.equations(c,list(range(n-1)),{'ports':{'0':[0,1]}},[0])
    except AssertionError:pass
    else:raise AssertionError('incomplete coverage accepted')
print({'models':160,'assignmentChecks':checked,'cycleControls':4,'invalidCoverRejections':8})
