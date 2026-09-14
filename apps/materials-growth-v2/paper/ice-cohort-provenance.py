"""Bind existing ice IDs/hashes to conservative, source-reviewed cohort metadata."""
import hashlib
import json
import sys
from pathlib import Path

source,dest=map(Path,sys.argv[1:])
p=json.loads(source.read_text())
records=[]
for row in p['configurations']:
    records.append({'id':row['id'],'elements':['H','O'],'split':row['split'],
        'sourceSha256':row['sourceSha256'],'sourceFrame':row['sourceFrame'],
        'temperatureK':row['temperatureK'],'pressurePa':row['pressurePa'],
        'paperProtocolTemperatureK':100,'paperProtocolPressurePa':100000,
        'conditionEvidence':'paper-level protocol; file mapping unverified',
        'conditionSource':'https://arxiv.org/html/2405.20217v1#S2.SS2.SSS2',
        'trajectoryId':row['independentTrajectoryId'],'trajectorySource':None,
        'independenceEvidence':'author random configuration split; independent runs not established'})
out={'provenanceHash':hashlib.sha256(source.read_bytes()).hexdigest(),
     'sourceReviewDate':'2026-09-14','records':records,
     'sourceNotes':['The preprint methods describe random validation selection from 500 sampled structures per polymorph.',
                    'The sampling and target electronic-structure ensembles are explicitly distinguished by the authors.',
                    'The preprint lists 80 molecules for VIII; the acquired files contain 64. File-level mapping remains unresolved.'],
     'learnerBoundary':'These records are evaluation provenance only; never pass them as geometry or marking features.'}
dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'records':len(records),'provenanceHash':out['provenanceHash']}))
