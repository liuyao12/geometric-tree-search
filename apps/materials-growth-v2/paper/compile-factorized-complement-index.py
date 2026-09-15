"""Complete conservative signature index; indexed pairs still need cloud checks."""
import collections,hashlib,importlib.util,json,pathlib,sys,time
import numpy as np
from scipy.spatial import cKDTree
source_path,blocks_path,output=map(pathlib.Path,sys.argv[1:])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('half',pathlib.Path(__file__).with_name('half-cloud-support.py'));half=importlib.util.module_from_spec(spec);spec.loader.exec_module(half)
source=json.loads(source_path.read_text());data=json.loads(blocks_path.read_text());assert data['sourceModelHash']==digest(source_path)
models=[]
for row in data['models']:
    start=time.monotonic();records=[];groups=collections.defaultdict(list);features=[]
    for i,b in enumerate(row['blocks']):
        for side,cs in enumerate(b['endpointChoices']):
            for j,c in enumerate(cs):
                layout,x=half.signature(source['clouds'][c['cloud']]);key=(b['markPoints'][side],layout)
                groups[key].append(len(records));records.append([i,side,j]);features.append(x)
    neighbors=[[] for _ in records];threshold=2*row['cloudRadius']+1e-8
    for ids in groups.values():
        tree=cKDTree(np.array([features[k] for k in ids]))
        for a,b in tree.query_pairs(threshold,p=np.inf,output_type='ndarray'):
            i,j=ids[a],ids[b]
            if row['blocks'][records[i][0]]['inventory']==row['blocks'][records[j][0]]['inventory']:continue
            neighbors[i].append(j);neighbors[j].append(i)
    for ns in neighbors:ns.sort()
    report={'file':row['file'],'fold':row['fold'],'records':len(records),'directedEdges':sum(map(len,neighbors)),'seconds':time.monotonic()-start}
    models.append({'file':row['file'],'fold':row['fold'],'records':records,'neighbors':neighbors,'threshold':threshold,'report':report});print(json.dumps(report),flush=True)
with output.open('x') as f:json.dump({'scope':__doc__,'sourceModelHash':digest(source_path),'blocksHash':digest(blocks_path),'compilerHash':digest(pathlib.Path(__file__)),'models':models},f)
