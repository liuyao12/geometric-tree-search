import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('verifier',Path(__file__).with_name('verify-boron-selected.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
c={'atoms':6,'occurrences':[{'type':t,'ids':ids} for ids in ([0,1,2],[3,4,5]) for t in range(3)]}
assert v.cover(c,list(range(6)),3)==2
for selected in ([0,1,2,3,4],[0,1,2,3,4,4],[0,1,2,3,4,9]):
    try:v.cover(c,selected,3)
    except AssertionError:pass
    else:raise AssertionError('Corrupt selection was accepted')
print('Verified integer incidence and disconnected components; rejected omission, duplicate, and invalid index.')
