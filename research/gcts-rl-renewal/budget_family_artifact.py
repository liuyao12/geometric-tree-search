"""Lazy, digest-bound access to discovery, training and primary worker trees."""
from pathlib import Path
import json
from receptor_attention_artifact import Records

class Cases(Records):
    def __getitem__(self,index):
        c=super().__getitem__(index);runs={};certificates={};catalog=None
        for lane,ref in c.pop('run_files').items():
            part=Records(self.root,[ref],wrapped=False)[0]
            if part['spec']!=c['spec'] or part['sources']!=c['sources']:raise ValueError('whole worker statement/source binding')
            if catalog is not None and catalog!=part['catalog']:raise ValueError('all lanes use the same original grammar')
            catalog=part['catalog'];runs[lane]=part['result'];certificates[lane]=part['certificate']
        c.update(catalog=catalog,runs=runs,certificates=certificates);return c

def load(path):
    path=Path(path);data=json.loads(path.read_text());root=path.parent
    discovery=Records(root,[data.pop('discovery_file')])[0]
    data.update(donors=discovery['donors'],library=discovery['library'])
    training=data['training'];training['initial_baseline_runs']=Records(root,training.pop('baseline_files'))
    training['episodes']=Records(root,training.pop('episode_files'));data['cases']=Cases(root,data.pop('case_files'),wrapped=False)
    return data
