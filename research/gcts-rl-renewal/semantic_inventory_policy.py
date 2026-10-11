"""Fresh policy learning, rewarded in verified base-point obligations."""
from native_inventory_policy import choose,update,RATE
from semantic_inventory_guidance import FEATURES,FIXED

EPISODES=24

def reward(result,accepted,arity):
    growth=(2+arity)*len(result['proof']) if accepted else 0
    work=result['metrics'].get('validation_checks',0)+result['metrics'].get('sample_pair_tests',0)
    return growth/max(1,result['metrics'].get('attempts',0))-0.25*min(1.,work/100000)
