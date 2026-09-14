"""Withheld-witness invariance and exact ranking checks."""
import copy
import importlib.util
from pathlib import Path
from fractions import Fraction
import json
import sys
spec=importlib.util.spec_from_file_location('p',Path(__file__).with_name('boron-type-priors.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
d=json.loads(Path(sys.argv[1]).read_text());s=json.loads(Path(sys.argv[2]).read_text())['result']['selected']
folds=p.fit_priors(d,s);pairs=0
for i,fold in enumerate(folds):
    changed=copy.deepcopy(s);changed[i]=[]
    assert p.fit_priors(d,changed)[i]==fold
    assert i not in fold['trainingConfigurations']
    for a in fold['types']:
        assert a['selected']<=a['observed']
        for b in fold['types']:
            x=Fraction(a['numerator'],a['denominator']);y=Fraction(b['numerator'],b['denominator'])
            assert (x<y)==(a['rank']<b['rank']) and (x==y)==(a['rank']==b['rank']);pairs+=1
print({'withheldWitnessMutations':len(folds),'exactRankComparisons':pairs})
