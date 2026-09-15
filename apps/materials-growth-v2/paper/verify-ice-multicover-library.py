"""Independent provenance, exact-cover and raw-cloud transport checks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-ice-portable.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
coordinates,cover_path,dictionary_path,selection_path,alternative_path,one_path,multi_path,output=sys.argv[1:]
corpus,cover,dictionary,selection,alternative,one,multi=map(read,[coordinates,cover_path,dictionary_path,selection_path,alternative_path,one_path,multi_path])
assert multi['baseMotifs'][:len(one['baseMotifs'])]==one['baseMotifs']
assert multi['motifs'][:len(one['motifs'])]==one['motifs']
assert multi['trainingRegistrations'][:len(one['trainingRegistrations'])]==one['trainingRegistrations']
assert multi['alternativeCoverHash']==sha(alternative_path) and one['alternativeCoverHash'] is None
cc={c['id']:c for c in corpus['configurations']};cv={r['id']:r for r in cover['results']}
dc={r['id']:r for r in dictionary['configurations']};ss={r['id']:r for r in selection['results']};aa={r['id']:r for r in alternative['results']}
reports=[]
for path,data in [(one_path,one),(multi_path,multi)]:
    assert data['codeHash']==sha(Path(__file__).with_name('ice-multicover-library.py'))
    for key,source in zip(['coordinates','cover','dictionary','selection'],[coordinates,cover_path,dictionary_path,selection_path]):assert data['sourceHashes'][key]==sha(source)
    seen=set();motifs=set();fits=0;max_error=0.
    for row in data['trainingRegistrations']:
        cid=row['id'];kind=row['coverVariant'];assert (cid,kind) not in seen;seen.add((cid,kind))
        assert dc[cid]['training'] and kind in ['original','alternative']
        selected=(ss if kind=='original' else aa)[cid]['selected']
        assert [r['edge'] for r in row['selected']]==selected
        queries,_=v.local_clouds(cc[cid],cv[cid],selected) # Also verifies atom totals and component degrees.
        for item in row['selected']:
            o=dc[cid]['occurrences'][item['edge']];ends=v.ends(o,cv[cid]['components'],cv[cid]['componentPairs'][item['edge']])
            motif=data['motifs'][item['motif']];base=data['baseMotifs'][motif['base']];motifs.add(item['motif'])
            assert item['roots']==[root for _,root in ends] and base['componentSites']==[sites for sites,_ in ends]
            assert base['pairType']==o['type'] and base['anchors']==dictionary['types'][o['type']]['positions']
            assert base['t']==[1]*len(o['ids']) and base['species']==dictionary['types'][o['type']]['species']
            rotation=v.proper(o['rotationRow'])
            for side,(_,root) in enumerate(ends):
                marking=motif['cloudM'][side];query=queries[root]
                assert marking['colors']==query['colors']
                error=float(np.max(np.abs(np.asarray(marking['vectors'])@rotation-query['vectors'])))
                assert error<1e-8;max_error=max(max_error,error);fits+=1
    expected={(cid,'original') for cid in cc if dc[cid]['training']}
    if path==multi_path:expected|={(cid,'alternative') for cid in aa if not aa[cid]['unchanged']}
    assert seen==expected and motifs==set(range(len(data['motifs'])))
    reports.append(dict(libraryHash=sha(path),**data['summary'],endpointTransportsChecked=fits,maxCoordinateDifference=max_error))
result=dict(scope=__doc__,verifierHash=sha(__file__),results=reports,originalLibraryIsExactPrefix=True,
            limits='Verifies training-observed libraries and exact t coverage, not transferable or exclusive markings. Alternative connectivity has a separate swap-replay certificate.')
with Path(output).open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
