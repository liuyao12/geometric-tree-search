import importlib.util
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('transport',Path(__file__).with_name('transport-holonomy.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
I=np.eye(3);Z=np.diag([-1.,-1,1]);X=np.diag([1.,-1,-1])
flat=m.analyze([0,1],[(0,I,1,Z)])
assert flat['components'][0]['numericalNullity']==3
axis=m.analyze([0],[(0,I,0,Z)])
assert axis['components'][0]['numericalNullity']==1
frustrated=m.analyze([0],[(0,I,0,Z),(0,I,0,X)])
assert frustrated['components'][0]['numericalNullity']==0
Q=np.array([[0.,-1,0],[1,0,0],[0,0,1]])
other=m.analyze([0],[(0,Q,0,Q@Z),(0,Q,0,Q@X)])
assert np.allclose(other['components'][0]['meanGram'],frustrated['components'][0]['meanGram'])
print('Flat transport, one-axis invariant, incompatible loops, and global-rotation invariance passed.')
