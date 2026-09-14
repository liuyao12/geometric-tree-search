"""Freeze the predeclared eight-additional-cover marking snapshot for search."""
import hashlib
import json
from pathlib import Path
import sys
dest=Path(sys.argv[2]);dest.mkdir()
for i in range(6):
    raw=(Path(sys.argv[1])/f'{i}.json').read_bytes();e=json.loads(raw);snapshot=e['snapshots'][-1]
    assert snapshot['additionalCoversPerConfiguration']==8
    out={'scope':__doc__,'trainingDictionaryHash':e['trainingDictionaryHash'],'selectedArtifactHash':e['selectedArtifactHash'],
        'ensembleHash':hashlib.sha256(raw).hexdigest(),'labels':snapshot['labels'],
        'summary':{k:v for k,v in snapshot.items() if k!='labels'}}
    (dest/f'{i}.json').write_text(json.dumps(out))
