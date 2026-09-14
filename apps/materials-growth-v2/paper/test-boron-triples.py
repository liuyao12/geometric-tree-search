import importlib.util
from pathlib import Path
from fractions import Fraction
import numpy as np
from scipy.sparse import csr_matrix
import json
import sys
import tempfile
spec=importlib.util.spec_from_file_location('triples',Path(__file__).with_name('boron-triple-precheck.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A=csr_matrix([[1,1,0],[0,1,1],[1,0,1]])
assert m.rational_polish(A,[1,1,1],[.499999,.500001,.5])==[Fraction(1,2)]*3
assert m.rational_polish(csr_matrix([[1],[1]]),[1,2],[1]) is None
x=m.rational_polish(csr_matrix([[1,2,1]]),[1],[.2,.3,.2])
assert sum(a*b for a,b in zip([1,2,1],x))==1
template=np.array([[0.,0,0],[2,0,0],[.3,1.1,0]]);template-=template.mean(axis=0)
R,_=np.linalg.qr(np.array([[1.,2,3],[2,-1,4],[1,3,-1]]))
if np.linalg.det(R)<0:R[:,0]*=-1
fit=m.geom.fit(template,template@R+[4,5,6],m.PERMS,.00001)
assert fit is not None and fit['residual']<1e-12
print('Passed exact polishing, inconsistency, free-variable, and proper-rotation controls.')
if len(sys.argv)==3:
    verifier=m.module('independent_verifier','verify-boron-triples.py')
    original=json.loads(Path(sys.argv[2]).read_text())
    def mutation(change):
        data=json.loads(json.dumps(original));change(data)
        with tempfile.TemporaryDirectory(prefix='gcts-boron-mutation-') as folder:
            path=Path(folder)/'mutated.json';path.write_text(json.dumps(data))
            try:verifier.verify(sys.argv[1],path)
            except AssertionError:return
            raise AssertionError('Independent verifier accepted corrupted evidence')
    mutation(lambda d:d['configurations'][0]['occurrences'][0]['translation'].__setitem__(0,1000))
    mutation(lambda d:d['configurations'][0]['occurrences'][0]['ids'].__setitem__(0,-1))
    first=next(i for i,r in enumerate(original['results']) if 'weights' in r)
    mutation(lambda d:d['results'][first]['weights'].__setitem__(0,'1'))
    mutation(lambda d:d['results'][first]['labels'].__setitem__(0,-1))
    print('Rejected corrupted transform, point identity, coverage weight, and marking.')
