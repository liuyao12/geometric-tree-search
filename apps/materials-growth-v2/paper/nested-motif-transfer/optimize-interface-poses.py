"""Bounded continuous-pose feasibility for frozen learned pair interfaces.

Optimizes rotations/translations, never source atoms or learned parameters.
Nonconvex, budgeted, fixed-correspondence trials: failure means unknown.
"""
import hashlib,importlib.util,itertools,json,sys,time
from pathlib import Path
import numpy as np
from ase.geometry import find_mic
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    coordp,metap,motifp,interfacep,reposedp,out=map(Path,sys.argv[1:]);coords=json.loads(coordp.read_text());meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text());interfaces=json.loads(interfacep.read_text());reposed=json.loads(reposedp.read_text())
    assert reposed['interfaceHash']==sha(interfacep) and reposed['motifHash']==sha(motifp) and reposed['coordinateHash']==sha(coordp) and reposed['metadataHash']==sha(metap)
    spec=importlib.util.spec_from_file_location('enum',Path(__file__).with_name('enumerate-rigid-proposals.py'));enum=importlib.util.module_from_spec(spec);spec.loader.exec_module(enum)
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};rr={r['id']:r for r in motifs['rows']};cache={};rows=[]
    def poses(cid,k):
        key=(cid,k)
        if key in cache:return cache[key]
        c=cc[cid];cluster=rr[cid]['clusters'][k];template=motifs['types'][cluster['type']];p=cluster['fit'];X=np.asarray(template['positions']);P=X@p['rotationRow']+p['translation'];predicted=np.empty_like(P);predicted[p['permutation']]=P
        delta,_=find_mic(np.asarray(c['positions'])[cluster['ids']]-predicted,np.asarray(c['cell']),pbc=c['pbc']);Y=predicted+delta
        extra,stats=enum.enumerate_poses(X,Y,template['species'],motifs['epsilonAngstrom']);cache[key]=(X,Y,[p]+extra,stats);return cache[key]
    for ri,r in enumerate(reposed['rows']):
        row=dict(r);row.update(optimized=False,trials=0,budgetStopped=False);rows.append(row)
        if r['witness'] is not None:continue
        o=interfaces['observations'][r['observation']];cid=o['configuration'];c=cc[cid]
        models=[(i,m) for i,m in enumerate(interfaces['models']) if m['trainingFrames']>=2 and (m['typeA'],m['typeB'])==(o['typeA'],o['typeB'])]
        if not models:continue
        XA,YA,AA,sa=poses(cid,o['clusterA']);XB,YB,BB,sb=poses(cid,o['clusterB']);row['correspondenceBudgetStopped']=sa['truncated'] or sb['truncated'];trials=[]
        for (mi,m),pa,pb in itertools.product(models,AA,BB):
            RA=np.asarray(pa['rotationRow']);RB=np.asarray(pb['rotationRow']);d,_=find_mic(np.asarray(pb['translation'])-pa['translation'],np.asarray(c['cell']),pbc=c['pbc'])
            e=np.linalg.norm(np.asarray(m['anchorA'])@RA-np.asarray(m['anchorB'])@RB-d)+np.linalg.norm(np.asarray(m['valueA'])@RA-np.asarray(m['valueB'])@RB)
            trials.append((float(e),mi,m,pa,pb,d))
        trials.sort(key=lambda x:x[0]);started=time.monotonic()
        for _,mi,m,pa,pb,d in trials[:12]:
            if time.monotonic()-started>2:row['budgetStopped']=True;break
            row['trials']+=1;A0=np.asarray(pa['rotationRow']);B0=np.asarray(pb['rotationRow']);QA=YA[pa['permutation']]-pa['translation'];QB=YB[pb['permutation']]-pb['translation']
            a=np.asarray(m['anchorA']);b=np.asarray(m['anchorB']);u=np.asarray(m['valueA']);v=np.asarray(m['valueB'])
            def state(z):
                A=A0@Rotation.from_rotvec(z[:3]).as_matrix();B=B0@Rotation.from_rotvec(z[6:9]).as_matrix();da=z[3:6];db=z[9:12];D=d+db-da
                e=[np.linalg.norm(a@A-b@B-D),np.linalg.norm(u@A-v@B),np.linalg.norm(u@A-D),np.linalg.norm(v@B-D)]
                residual=np.r_[np.linalg.norm(XA@A+da-QA,axis=1)-motifs['epsilonAngstrom'],np.linalg.norm(XB@B+db-QB,axis=1)-motifs['epsilonAngstrom'],np.asarray(e)-np.array([interfaces['positionPairTolerance'],interfaces['valuePairTolerance'],interfaces['valueTargetTolerance'],interfaces['valueTargetTolerance']])]
                return A,B,da,db,residual
            def inequalities(z):return z[12]-state(z)[4]
            class Budget(Exception):pass
            def callback(z):
                if time.monotonic()-started>2:raise Budget()
            z=np.zeros(13);z[12]=max(0,float(max(state(z)[4])))
            try:
                solved=minimize(lambda z:z[12],z,method='SLSQP',bounds=[(-np.pi,np.pi)]*3+[(-.3,.3)]*3+[(-np.pi,np.pi)]*3+[(-.3,.3)]*3+[(0,None)],constraints={'type':'ineq','fun':inequalities},callback=callback,options={'maxiter':120,'ftol':1e-10})
            except Budget:row['budgetStopped']=True;break
            A,B,da,db,residual=state(solved.x)
            if max(residual)>1e-9:continue
            ta=np.asarray(pa['translation'])+da;tb=np.asarray(pb['translation'])+db;D,_=find_mic(tb-ta,np.asarray(c['cell']),pbc=c['pbc'])
            errors=[float(np.linalg.norm(a@A-b@B-D)),float(np.linalg.norm(u@A-v@B)),float(max(np.linalg.norm(u@A-D),np.linalg.norm(v@B-D)))]
            if any(e>interfaces[key]+1e-9 for e,key in zip(errors,['positionPairTolerance','valuePairTolerance','valueTargetTolerance'])):continue
            row['witness']=dict(interface=mi,poseA=dict(permutation=pa['permutation'],rotationRow=A.tolist(),translation=ta.tolist(),residual=float(max(np.linalg.norm(XA@A+da-QA,axis=1)))),poseB=dict(permutation=pb['permutation'],rotationRow=B.tolist(),translation=tb.tolist(),residual=float(max(np.linalg.norm(XB@B+db-QB,axis=1)))),errors=errors)
            row['optimized']=True;break
        row['trialCapReached']=len(trials)>12 and row['trials']==12 and not row['optimized'];row['seconds']=time.monotonic()-started
        if ri%20==0:print(json.dumps(dict(processed=ri+1,recovered=sum(r['optimized'] for r in rows))),flush=True)
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        group=[r for r in rows if mm[r['configuration']]['phase']==phase];ids={r['configuration'] for r in group}
        summary.append(dict(phase=phase,pairs=len(group),baselineMatched=sum(r['baselineMatched'] for r in group),refittedMatched=sum(r['witness'] is not None for r in group),frames=len(ids),allPairsMatched=sum(all(r['witness'] is not None for r in group if r['configuration']==cid) for cid in ids)))
    report=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),interfaceHash=sha(interfacep),reposedHash=sha(reposedp),codeHash=sha(Path(__file__)),rows=rows,summary=summary,
                limits='Fixed-correspondence nonconvex SLSQP, at most 12 ranked initializations and two seconds per failed pair, 120 iterations each. All tolerances and learned values frozen. Positive witnesses independently replayable; failures unknown. Shared motifs can still use inconsistent poses across different pair witnesses. Not GCTS t-learning, joint decoration, condition matching or growth.')
    with out.open('x') as f:json.dump(report,f)
    print(json.dumps(dict(summary=summary,optimized=sum(r['optimized'] for r in rows),budgetStops=sum(r['budgetStopped'] for r in rows))),flush=True)
if __name__=='__main__':main()
