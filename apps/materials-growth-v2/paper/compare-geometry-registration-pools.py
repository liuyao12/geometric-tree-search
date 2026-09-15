"""Compare local connection patterns, not near-equal floating-point rotations."""
import hashlib
import json
from pathlib import Path
import sys
junction,joined,geometry,out=map(Path,sys.argv[1:]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=json.loads(junction.read_text());old=json.loads(joined.read_text());new=json.loads(geometry.read_text())
assert old['junctionHash']==sha(junction) and old['inputHash']==new['inputHash']
rows=[]
for f,fold in enumerate(new['folds']):
    nodes={n['point']:n for n in j['folds'][f]['nodes']};before=set();after=set()
    for e in old['folds'][f]['edges']:
        for pair in e['allowedPresentStates']:before.add((e['candidate'],*(tuple(sorted(nodes[point]['states'][state]['candidates'])) for point,state in zip(e['points'],pair))))
    for e in fold['edges']:
        for fit in e['registrations']:after.add((e['candidate'],*map(lambda ids:tuple(sorted(ids)),fit['selectedArms'])))
    rows.append({'file':fold['file'],'oldPatterns':len(before),'geometryPatterns':len(after),'retainedOldPatterns':len(before&after),'oldPatternsNotRecovered':len(before-after),'additionalPatterns':len(after-before)})
result={'scope':__doc__,'junctionHash':sha(junction),'oldRegistrationHash':sha(joined),'geometryRegistrationHash':sha(geometry),'checks':rows,
        'limits':'Same learned input family; compares discrete arm selections only. Does not assert equality of marking-value sets or complete continuous-pose coverage.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
