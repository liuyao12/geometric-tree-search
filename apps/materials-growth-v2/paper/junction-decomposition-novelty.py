"""Compare a verified finite search filling with supplied training decompositions.

This measures placement-set novelty on unchanged coordinates, not a new material.
"""
import hashlib
import json
from pathlib import Path
import sys

learned,alternatives,run_path,out=map(Path,sys.argv[1:])
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads(learned.read_text())['result'];a=json.loads(alternatives.read_text());run=json.loads(run_path.read_text())
assert a['learningHash']==digest(learned)
result=run['result'];assert result['status']=='exact finite point-cover witness'
fold=result['fold'];chosen=set(map(int,result['selected']));assert len(chosen)==len(result['selected'])
training=[('original',r['selected'][fold])]+[(f"alternative-{x['seed']}",x['selected']) for x in a['runs'] if x['fold']==fold]
comparisons=[{'trainingRecord':name,'placements':len(ids),'symmetricDifference':len(chosen^set(ids))} for name,ids in training]
summary={'scope':__doc__,'runHash':digest(run_path),'learningHash':digest(learned),'alternativeHash':digest(alternatives),
         'file':result['file'],'selected':len(chosen),'comparisons':comparisons,'differentFromEveryTrainingRecord':all(c['symmetricDifference']>0 for c in comparisons)}
out.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
