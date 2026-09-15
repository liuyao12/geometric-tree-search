"""Hash-bound aggregate of the six-frame ambient-marking reconstruction control."""
import hashlib
import json
from pathlib import Path
import sys
directory,library_check_path,root_check_path,output=map(Path,sys.argv[1:])
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(directory/'manifest.json');library_check=read(library_check_path);root_check=read(root_check_path)
assert manifest['orderingPolicies']==['coupled-observed']
rows=[]
for phase in ['Ih','II','VI']:
    path=directory/phase;source=read(path/'source.json');assert source['portableHash']==library_check['libraryHash']
    summary=read(path/'coupled-observed'/'summary.json');check=read(path/'coupled-observed-check.json')
    assert summary['sourceModelHash']==check['sourceModelHash']==sha(path/'source.json')
    assert summary['blocksHash']==check['blocksHash']==sha(path/'filtered.json')
    for result,verified in zip(summary['results'],check['results'],strict=True):
        assert result['file']==verified['file'] and result['selected']==verified['selected'] and result['scalarComplete']==verified['complete']
        assert result['rootRollback'] and result['markingStatus']=='verified-common-values'
        assert verified['verifiedAssignments']==2*verified['selected']
        assert verified['runHash']==sha(path/'coupled-observed'/f"{result['fold']}.json")
        root=next(r for r in root_check['results'] if r['file']==result['file']);assert root['blocksHash']==summary['blocksHash']
        meta=next(r for r in manifest['configurations'] if r['id']==result['file'])
        rows.append(dict(phase=phase,split=meta['split'],result=result,independentCheck=verified,rootCheck=root,sourceHashes=summary['sourceHashes']))
assert len(rows)==6
report=dict(scope=__doc__,manifest=manifest,libraryCheck=library_check,rootCheckHash=sha(root_check_path),results=rows,
            completeRuns=sum(r['independentCheck']['complete'] for r in rows),
            limits='Different marking hypothesis on fixed registered supports; not a same-problem speed comparison. Existing developmental frames, not blind transfer. Positive training checks and full search results are separate; no physics/chemistry, condition or continuous-growth claim.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(frames=len(rows),complete=report['completeRuns'])))
