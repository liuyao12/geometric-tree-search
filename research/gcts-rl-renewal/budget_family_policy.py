"""Shared family attention using actually justified source receptors.

Occupied future conclusion tiles are not counted as established facts until
all their earlier premise references are justified. These features only guide
ordering; the original graph and certified distant marks govern legality.
"""
import receptor_attention as Original

FEATURES=('family','cells','concludes_target','justified_goal_gain','last_goal',
          'internal_fraction','hypothesis_fraction','compactness','level',
          'progress_family','guard_fraction','defer')
RATE=Original.RATE
EPOCHS=Original.EPOCHS
choose=Original.choose
reward=Original.reward
update=Original.update


def justified(model, keys):
    h=len(model.hypotheses)
    known={i:a for i,a in enumerate(model.hypotheses,-h)}
    for j,rid,refs in sorted(keys):
        if rid>=0:
            rule=model.catalog['rules'][rid]
            if all(known.get(i)==a for i,a in zip(refs,rule['inputs'])):
                known[j]=rule['output']
    return known


class Support(Original.Support):
    def vector(self,item,state,graph):
        if item is None:return (0.,)*11+(1.,)
        model=self.model;members=item['members'];slots={k[0] for k in members}
        rules=[model.catalog['rules'][k[1]] for k in members]
        before=max(map(self.relevance,justified(model,state.order).values()),default=0.)
        proposed={k[0]:k for k in state.order}
        for key in members:proposed.setdefault(key[0],key)
        after=max(map(self.relevance,justified(model,proposed.values()).values()),default=0.)
        refs=[j for k in members for j in k[2]]
        return (1.,len(members)/6,int(rules[-1]['output']==model.target),after-before,
            self.relevance(rules[-1]['output']),
            sum(j in slots for j in refs)/max(1,len(refs)),
            sum(j<0 for j in refs)/max(1,len(refs)),
            len(slots)/(max(slots)-min(slots)+1),item['level']/2,
            len(state.order)/model.length,
            sum(bool(r['guards']) for r in rules)/len(rules),0.)

    def record(self):
        return dict(distances=sorted(self.distance.items()),features=FEATURES,
            scope='Relaxed original-rule backward distance, with progress measured only over hypothesis receptors and occupied inference rows whose earlier premises are recursively justified. Hypothetical family progress is the same ascending dependency check on actual constituent keys. No supplied proof, formula-name parameter, new axiom or pruning; cold once per solve.')
