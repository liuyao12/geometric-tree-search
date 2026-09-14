"""Versioned data-admission register; metadata never becomes a GCTS rule.

Verify existing source hashes and inspect all CIF tags for condition/protocol
metadata. Record literature corrections separately from coordinate assertions.
Missing coordinates and unknown conditions cannot count as admitted examples.
"""
import hashlib
import json
from pathlib import Path
import sys
import gemmi

ERRATUM='https://doi.org/10.1103/PhysRevLett.118.159902'
COMMENT='https://doi.org/10.1103/PhysRevLett.118.159601'
REPLY='https://doi.org/10.1103/PhysRevLett.118.089602'
COORDINATES='https://drive.google.com/open?id=0B4BhFV36dCUjU2lqNmtNSEpHdG8'

def audit(folder):
    folder=Path(folder);raw=(folder/'input-audit.json').read_bytes();source=json.loads(raw);rows=[]
    for c in source['results']:
        path=folder/c['file'];data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==c['sha256']
        block=gemmi.cif.read_file(str(path)).sole_block();tags=[];metadata={}
        for item in block:
            if item.pair:
                tag,value=item.pair;tags.append(tag)
                if any(key in tag.lower() for key in ('temperature','pressure','computing','refine')):metadata[tag]=value
            elif item.loop:
                tags.extend(item.loop.tags)
                for tag in item.loop.tags:
                    if any(key in tag.lower() for key in ('temperature','pressure','computing','refine')):
                        metadata[tag]=list(block.find_values(tag))
        rows.append({'id':'an2016-'+c['file'],'file':c['file'],'sha256':c['sha256'],'atoms':c['atoms'],
                     'coordinateStatus':'previously validated; source hash rechecked','source':c['source'],
                     'conditionProtocolTags':metadata,'cifTags':tags,
                     'temperatureK':None,'pressureGPa':None,'conditionMatchedAdmission':False,
                     'reason':'No numerical condition values have been established for this specific coordinate file.'})
    pending=[{'id':f'an2017-tau-S{i}','reportedLabel':f'S-{i}','reportedFamily':'tau-B106',
              'source':ERRATUM,'sourceLocation':'Table I and reference 8','coordinateLink':COORDINATES,
              'coordinateStatus':'not acquired','coordinateSha256':None,'temperatureK':None,'pressureGPa':None,
              'conditionMatchedAdmission':False,'learningTested':False,'growthTested':False,
              'distinctFromOriginalSix':'not established without coordinates'} for i in range(1,11)]
    return {'schemaVersion':1,'checkedOn':'2026-09-14','inputAuditHash':hashlib.sha256(raw).hexdigest(),
            'sources':{'original':'https://doi.org/10.1103/PhysRevLett.117.085501',
                       'reply':REPLY,'erratum':ERRATUM,'independentComment':COMMENT},
            'literatureCorrections':[
                {'claim':'The original tau ground-state assignment was withdrawn.','source':ERRATUM},
                {'claim':'The reported original alpha/beta/gamma and tau energy calculations used different PAW pseudopotentials.',
                 'source':ERRATUM,'scope':'Reported calculation batches; does not identify the relaxation protocol of each stored CIF.'},
                {'claim':'The correction reports ten tau-B106 occupancy arrangements recalculated with the newer pseudopotential and PBE.',
                 'source':ERRATUM,'scope':'Published method description; file-level settings await coordinate acquisition.'}],
            'coordinateAccess':{'url':COORDINATES,'checkedOn':'2026-09-14',
                                'observation':'Published link and ordinary download endpoint redirected to Google sign-in without authentication.',
                                'scope':'Access result in this session, not proof that the data are unavailable everywhere.'},
            'validatedOriginalFiles':rows,'reportedPendingStructures':pending,
            'summary':{'validatedCoordinateFiles':len(rows),'filesWithConditionProtocolTags':sum(bool(r['conditionProtocolTags']) for r in rows),
                       'conditionMatchedAdmittedFiles':sum(r['conditionMatchedAdmission'] for r in rows),
                       'reportedCorrectionVariants':len(pending),'correctionVariantsAcquired':0,
                       'totalDistinctStructures':'not determined'},
            'interpretation':'Existing geometry/filling/search results remain valid for their stored inputs. They are cross-structure controls, not an all-boron census or condition-matched ensemble.'}

if __name__=='__main__':
    out=audit(sys.argv[1])
    with Path(sys.argv[2]).open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out['summary'],indent=2))
