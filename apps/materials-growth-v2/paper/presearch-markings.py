"""Exact scalar pre-search control; geometric identities are validated upstream."""
from fractions import Fraction

def equality_labels(n, groups):
    parent=list(range(n))
    def root(p):
        while parent[p]!=p:
            parent[p]=parent[parent[p]];p=parent[p]
        return p
    for group in groups:
        for p in group[1:]:parent[root(p)]=root(group[0])
    classes={};labels=[]
    for p in range(n):
        r=root(p)
        if r not in classes:classes[r]=len(classes)
        labels.append(classes[r])
    return labels

def precheck(required, placements):
    totals={};markings={};errors=[]
    for a,placement in enumerate(placements):
        for p,value in placement.get('t',{}).items():
            v=Fraction(value)
            if not 0<=v<=1:errors.append(('invalid-t',a,p))
            totals[p]=totals.get(p,Fraction(0))+v
        for p,value in placement.get('m',{}).items():
            if p in markings and markings[p]!=value:errors.append(('mark-conflict',a,p))
            else:markings[p]=value
    for p,v in totals.items():
        if v>1:errors.append(('over-capacity',p,str(v)))
    for p in required:
        if totals.get(p,Fraction(0))!=1:errors.append(('incomplete-filling',p,str(totals.get(p,0))))
    return {'valid':not errors,'errors':errors,'filledRequired':sum(totals.get(p,0)==1 for p in required),
            'assignedMarkingPoints':len(markings)}

if __name__=='__main__':
    import json,sys,hashlib
    from pathlib import Path
    raw=Path(sys.argv[1]).read_bytes();data=json.loads(raw);results=[]
    for run in data['runs']:
        groups=[[] for _ in range(432)];instances=[]
        for i,t in enumerate(run['types']):
            for o in t['occurrences']:
                row=[]
                for u,p in enumerate(o['sites']):
                    point=o['frame']*216+p;variable=3*i+u;groups[point].append(variable);row.append((point,variable))
                instances.append(row)
        weights=list(map(Fraction,run['weights']));labels=equality_labels(len(weights),groups)
        placements=[{'t':{p:str(weights[v]) for p,v in row},'m':{p:labels[v] for p,v in row}} for row in instances]
        check=precheck(list(range(432)),placements);assert check['valid']
        compatible=[(i,j) for i in range(len(weights)) for j in range(i,len(weights)) if weights[i]+weights[j]<=1]
        separated=[(i,j) for i,j in compatible if labels[i]!=labels[j]]
        out={'degree':run['summary']['degree'],'variables':len(weights),'equalityComponents':len(set(labels)),
             'componentSizes':[labels.count(i) for i in range(len(set(labels)))],
             'capacityCompatibleSitePairs':len(compatible),'separatedSitePairs':len(separated),
             'precheck':check,'labels':labels,'groups':groups}
        results.append(out);print(json.dumps({k:v for k,v in out.items() if k not in ['labels','groups']}))
    with open(sys.argv[2],'x') as f:json.dump({'inputHash':hashlib.sha256(raw).hexdigest(),'results':results},f)
