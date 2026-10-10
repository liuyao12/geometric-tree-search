"""Hash-bound lazy access to individual complete experimental traces."""
import gzip
import hashlib
import json
from pathlib import Path

class Records:
    def __init__(self,root,refs,wrapped=True):self.root=root;self.refs=refs;self.wrapped=wrapped
    def __len__(self):return len(self.refs)
    def __getitem__(self,index):
        if isinstance(index,slice):return [self[i] for i in range(*index.indices(len(self)))]
        ref=self.refs[index];path=self.root/ref['path'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('trace hash: '+ref['path'])
        out=json.loads(gzip.decompress(raw))
        if self.wrapped:
            if out['sources']!=ref['sources']:raise ValueError('trace source binding')
            return out['data']
        return out
    def __iter__(self):
        for i in range(len(self)):yield self[i]

class Cases(Records):
    def __getitem__(self,index):
        c=super().__getitem__(index)
        runs={};catalog=None
        for lane,ref in c.pop('run_files').items():
            part=Records(self.root,[ref],wrapped=False)[0];runs[lane]=part['result'];catalog=part['catalog']
            if part['spec']!=c['spec']:raise ValueError('evaluation statement binding')
        c.update(catalog=catalog,runs=runs);return c

def load(path):
    path=Path(path);data=json.loads(path.read_text());root=path.parent
    discovery=Records(root,[data.pop('discovery_file')])[0]
    data.update(donors=discovery['donors'],library=discovery['library'])
    training=data['training'];training['initial_baseline_runs']=Records(root,training.pop('baseline_files'))
    training['episodes']=Records(root,training.pop('episode_files'));data['cases']=Cases(root,data.pop('case_files'),wrapped=False)
    return data
