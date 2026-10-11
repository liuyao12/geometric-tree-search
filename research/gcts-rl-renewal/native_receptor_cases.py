"""Statements, given premises and bounds only. No proof path is supplied."""
import copy
from certificate_boundary_cases import cases as earlier,theory
def cases():
    rows=copy.deepcopy(earlier()[:6])
    def chain(n):
        atoms=[['pred',chr(65+i),[]] for i in range(n+1)]
        axioms={'start':atoms[0]}
        axioms.update({'step'+str(i):['imp',atoms[i],atoms[i+1]] for i in range(n)})
        return dict(id='chain-'+str(n),title=str(n)+' successive implication applications',theory=theory(predicates={chr(65+i):0 for i in range(n+1)},axioms=axioms),target=atoms[-1],length=2*n+1,scope='Given ground premise chain; all command ordering and backward references are unknown to search.')
    rows.extend([chain(2),chain(3)])
    for id,title,extra in [('zero-placement','Zero point-placement budget',dict(attempts=0,queries=0)),('unfinished-native','One native step per query',dict(micro_steps=1))]:
        r=copy.deepcopy(rows[2]);r.update(id=id,title=title,scope='Unknown control; unfinished work cannot remove a candidate.',**extra);rows.append(r)
    return rows
