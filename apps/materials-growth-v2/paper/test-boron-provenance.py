"""Ensure missing data, differing sources and old results are not conflated."""
import hashlib
import json
from pathlib import Path
import sys
import gemmi

folder=Path(sys.argv[1]);register=json.loads(Path(sys.argv[2]).read_text());source=(folder/'input-audit.json').read_bytes()
assert register['inputAuditHash']==hashlib.sha256(source).hexdigest()
assert register['sources']['reply']!=register['sources']['erratum']
assert len(register['validatedOriginalFiles'])==6 and len(register['reportedPendingStructures'])==10
for row in register['validatedOriginalFiles']:
    raw=(folder/row['file']).read_bytes();assert row['sha256']==hashlib.sha256(raw).hexdigest()
    b=gemmi.cif.read_file(str(folder/row['file'])).sole_block()
    tags=[]
    for item in b:
        if item.pair:tags.append(item.pair[0])
        elif item.loop:tags.extend(item.loop.tags)
    assert tags==row['cifTags']
    assert not row['conditionMatchedAdmission'] and row['temperatureK'] is None and row['pressureGPa'] is None
    assert not [t for t in tags if any(s in t.lower() for s in ('temperature','pressure','computing','refine'))]
for row in register['reportedPendingStructures']:
    assert row['coordinateSha256'] is None and not row['conditionMatchedAdmission']
    assert not row['learningTested'] and not row['growthTested']
assert register['summary']['conditionMatchedAdmittedFiles']==0
assert register['summary']['totalDistinctStructures']=='not determined'
print('Six hashes/tag inventories, ten missing-data rows, and separate Reply/Erratum identities verified.')
