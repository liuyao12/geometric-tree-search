"""Exhaustive controls for the invariant equality-marking capacity statement."""
from itertools import product
import random

rng=random.Random(78);checked=0;accepted=0
for _ in range(50):
    n=rng.randrange(2,6)
    edges=[(a,b) for a in range(n) for b in range(a+1,n) if rng.random()<.35]
    reach=[[i==j or (min(i,j),max(i,j)) in edges for j in range(n)] for i in range(n)]
    for k in range(n):
        for i in range(n):
            for j in range(n):reach[i][j]=reach[i][j] or (reach[i][k] and reach[k][j])
    # Four values represent two binary invariant channels.
    for assignment in product(range(4),repeat=n):
        checked+=1
        if not all(assignment[a]==assignment[b] for a,b in edges):continue
        accepted+=1
        assert all(not reach[a][b] or assignment[a]==assignment[b] for a in range(n) for b in range(n))
    # Distinct labels per component realize every separation allowed by training.
    component=[min(j for j in range(n) if reach[i][j]) for i in range(n)]
    assert all(component[a]==component[b] for a,b in edges)
    assert all((component[a]==component[b])==reach[a][b] for a in range(n) for b in range(n))
print({'graphs':50,'twoChannelAssignmentsChecked':checked,'trainingCompatibleAssignments':accepted})
