"""Small positive and mutation controls for the independent Python verifier."""
import copy
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-boron-composed-proofs.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
model={'capacity':1,'required':['p','q','r'],'candidates':[
 {'id':'a','t':[{'point':'p','value':1}],'m':[{'point':'z','lo':0,'hi':0}]},
 {'id':'b','t':[{'point':'q','value':1}],'m':[{'point':'w','lo':0,'hi':0}]},
 {'id':'c','t':[{'point':'q','value':1}],'m':[{'point':'z','lo':1,'hi':1}]},
 {'id':'d','t':[{'point':'r','value':1}],'m':[{'point':'w','lo':1,'hi':1}]},
 {'id':'e','t':[{'point':'r','value':1}],'m':[{'point':'z','lo':1,'hi':1}]},
 {'id':'f','t':[{'point':'p','value':1}],'m':[{'point':'z','lo':1,'hi':1}]}]}
nodes=[{'kind':'force','point':'q','target':'b','ids':['a'],'uses':[]},
       {'kind':'dead','point':'r','ids':['a','b'],'uses':[]},
       {'kind':'resolve','clause':1,'implication':0,'ids':['a']},
       {'kind':'force','point':'p','target':'f','ids':[],'uses':[2]}]
assert v.check_nodes(model,nodes,{'f','c','d'})==({'force':2,'dead':1,'resolve':1},1)
mutations=[(0,'ids',[]),(0,'point','r'),(1,'ids',['a']),(2,'ids',[]),
           (2,'clause',2),(2,'implication',1),(3,'uses',[]),(3,'uses',[4]),(3,'target','a')]
for index,key,value in mutations:
    bad=copy.deepcopy(nodes);bad[index][key]=value
    try:v.check_nodes(model,bad,{'f','c','d'})
    except AssertionError:pass
    else:raise AssertionError(f'Accepted invalid proof mutation {index,key,value}')
print({'validProofNodes':4,'priorClauseImplication':True,'invalidProofsRejected':len(mutations)})
