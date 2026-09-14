import importlib.util
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location('boron',Path(__file__).with_name('boron-pair-precheck.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
p=np.array([[0,0,0],[1,1,0],[1,0,1],[0,1,1]],dtype=float)
def config(p):
    return {'file':'synthetic tetrahedron','atoms':len(p),'positions':p.tolist(),'cell':(np.eye(3)*30).tolist()}
a=module.run(config(p),1.15,.01)
assert a['status']=='exact finite-quotient t/m precheck passed'
assert a['weights']==['1/3'] and a['scalarMarkClasses']==1
q,_=np.linalg.qr(np.array([[1.,2.,3.],[4.,-2.,1.],[2.,1.,-3.]]))
if np.linalg.det(q)<0:q[:,0]*=-1
b=module.run(config(p@q+[7,8,9]),1.15,.01)
assert b['weights']==a['weights'] and b['precheck']==a['precheck']
c=module.run(config(np.array([[0.,0,0],[1.,0,0],[2.,0,0]])),1.15,.01)
assert c['status']=='restricted LP infeasible'
print('Passed tetrahedron exact weight, rigid-transform invariance, and path infeasibility controls.')
