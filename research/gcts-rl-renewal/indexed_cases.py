"""Same declarative controls plus longer and compound-receptor transfers."""
from resumable_cases import registry as old,branch
def registry():
    donors,training,evaluation=old()
    evaluation.extend([branch('indexed-tail-five',tail=5),branch('indexed-compound-decoys',tail=3,decoys=3,compound=True)])
    return donors,training,evaluation
