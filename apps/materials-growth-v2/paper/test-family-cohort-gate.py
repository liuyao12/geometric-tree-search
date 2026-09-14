import copy
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('gate',Path(__file__).with_name('family-cohort-gate.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
base=[{'id':str(i),'elements':['O','H'],'split':s,'temperatureK':100,'pressurePa':100000,
       'conditionEvidence':'file-linked protocol','conditionSource':'audited source',
       'trajectoryId':str(i),'trajectorySource':'audited run metadata',
       'independenceEvidence':'documented independent runs'} for i,s in enumerate(('train','test'))]
assert g.assess(base)['independentTrajectoryHoldoutAdmitted']
checks=0
for key,value in [('temperatureK',None),('pressurePa',None),('conditionSource',None),
                  ('conditionEvidence','paper-level protocol'),('temperatureK',float('nan')),
                  ('temperatureK',True),('pressurePa',200000),('elements',['Si'])]:
    data=copy.deepcopy(base);data[1][key]=value
    assert not g.assess(data)['sameConditionClaimAdmitted'];checks+=1
for key,value in [('trajectoryId',None),('trajectoryId','0'),('trajectorySource',None),
                  ('independenceEvidence','random configuration split')]:
    data=copy.deepcopy(base);data[1][key]=value
    assert g.assess(data)['sameConditionClaimAdmitted']
    assert not g.assess(data)['independentTrajectoryHoldoutAdmitted'];checks+=1
data=copy.deepcopy(base)
for r in data:r.update(temperatureK=None,pressurePa=None,trajectoryId=None)
assert not g.assess(data)['sameConditionClaimAdmitted']
assert g.assess(data)['exploratoryGeometryTrainingAllowed'];checks+=1
print({'positiveControl':1,'negativeControls':checks})
