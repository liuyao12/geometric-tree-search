"""Declared source, recipient and control statements for witness transfer."""
import logic as L
import hilbert_incidence_tiles as F
import hilbert_quantified_tiles as Q
def source():
    p=Q.problem('line-has-point');return dict(p,id=p['name'],length=10,transport=True)
def problem(name):
    p=Q.problem('unique-joining-line')
    if name=='joining-exists-reordered':
        p['name']=name;p['goal']=F.exists('l0',F.conjunction([F.pred('Inc','b','l0'),F.pred('Inc','a','l0'),F.pred('Line','l0')]))
        p['target']=F.close(p['variables'],L.Imp(p['hypothesis'],p['goal']));p['source']='Reordered existence of a joining line; consequence of planar Hilbert I.1'
        return dict(p,id=name,length=7,transport=False)
    if name!='unique-joining-line':raise ValueError(name)
    return dict(p,id=name,length=12,transport=False)
def cases():
    return [('unique-joining-line','unique-joining-line',12,(),2),('joining-exists-reordered','joining-exists-reordered',7,(),2),('joining-no-I1','unique-joining-line',12,('I.1-existence',),1),('joining-no-I2','unique-joining-line',12,('I.2-uniqueness',),1),('joining-short','unique-joining-line',11,(),1)]
