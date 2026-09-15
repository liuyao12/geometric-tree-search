"""Search for joint geometry/marking pose witnesses at fixed tolerances.

Numerical local minimization cannot certify nonexistence. No sample target poses
are supplied to the optimizer: only paired motif ports and learned marks.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import minimize, least_squares
from scipy.spatial.transform import Rotation


def solve(source,target,sm,tm,R,t,geps,meps,strategy='minimax'):
    if strategy=='least-squares':
        def residual(x):
            rotation=R@Rotation.from_rotvec(x[:3]).as_matrix()
            return np.r_[((source@rotation+t+x[3:]-target)/geps).ravel(),
                ((sm@rotation-tm)/(meps*np.sqrt(len(sm)))).ravel()]
        result=least_squares(residual,np.zeros(6),max_nfev=200,ftol=1e-12,gtol=1e-12,xtol=1e-12)
        rotation=R@Rotation.from_rotvec(result.x[:3]).as_matrix();translation=t+result.x[3:]
        geometry=float(np.linalg.norm(source@rotation+translation-target,axis=1).max())
        marking=float(np.sqrt(np.mean(np.sum((sm@rotation-tm)**2,axis=2),axis=0)).max())
        return {'geometryMaximum':geometry,'markingMaximum':marking,'rotationRow':rotation.tolist(),
            'translation':translation.tolist(),'evaluations':result.nfev,'optimizerSuccess':bool(result.success),
            'status':'witness' if geometry<=geps and marking<=meps else 'local-search-unknown'}
    def measures(x):
        rotation=Rotation.from_rotvec(x[:3]).as_matrix()
        geometry=np.sum((source@rotation+x[3:6]-target)**2,axis=1)/geps**2
        marking=np.mean(np.sum((sm@rotation-tm)**2,axis=2),axis=0)/meps**2
        return geometry,marking,rotation
    x=np.r_[Rotation.from_matrix(R).as_rotvec(),t,1.]
    g,m,_=measures(x);x[-1]=np.sqrt(max(g.max(),m.max()))
    initial=float(x[-1])
    result=minimize(lambda x:x[6],x,method='SLSQP',
        bounds=[(None,None)]*6+[(0,None)],
        constraints={'type':'ineq','fun':lambda x:x[6]**2-np.concatenate(measures(x)[:2])},
        options={'maxiter':200,'ftol':1e-11})
    g,m,rotation=measures(result.x)
    geometry=float(np.sqrt(g.max())*geps);marking=float(np.sqrt(m.max())*meps)
    return {'initialNormalizedMaximum':initial,'geometryMaximum':geometry,'markingMaximum':marking,
            'rotationRow':rotation.tolist(),'translation':result.x[3:6].tolist(),
            'iterations':int(result.nit),'optimizerSuccess':bool(result.success),
            'optimizerMessage':str(result.message),
            'status':'witness' if geometry<=geps and marking<=meps else 'local-search-unknown'}


if __name__=='__main__':
    dr=Path(sys.argv[1]).read_bytes();dictionary=json.loads(dr)
    cr=Path(sys.argv[2]).read_bytes();data=json.loads(cr)
    assert hashlib.sha256(dr).hexdigest()==data['dictionaryHash']
    run=next(r for r in data['results'] if r['channels']==4)
    strategy=sys.argv[4] if len(sys.argv)>4 else 'minimax'
    marks=np.array(data['channels'][:4]);results=[]
    for index,p in enumerate(run['probeDetails']):
        if p['mismatch']<=run['tolerance']:continue
        ta,tb=p['targetType'],p['sourceType'];a=np.array(p['targetSites']);b=np.array(p['sourceSites'])
        source=np.array(dictionary['types'][tb]['positions'])[b]
        target=np.array(dictionary['types'][ta]['positions'])[a]
        result=solve(source,target,marks[:,6*tb+b,:],marks[:,6*ta+a,:],
            np.array(p['rotationRow']),np.array(p['translation']),.05,run['tolerance'],strategy)
        result['probeIndex']=index;results.append(result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('rotationRow','translation')}),flush=True)
    with open(sys.argv[3],'x') as out:json.dump({'scope':__doc__,
        'dictionaryHash':hashlib.sha256(dr).hexdigest(),'channelArtifactHash':hashlib.sha256(cr).hexdigest(),
        'channels':4,'strategy':strategy,'geometryTolerance':.05,'markingTolerance':run['tolerance'],'results':results},out,indent=2)
