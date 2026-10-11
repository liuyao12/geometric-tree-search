"""Exhaustive tiny word/region comparison using literal point assignments."""
import itertools
from audit_semantic_inventory import initial,legal,advance,need,pin,whole_replay

def point_word(spec,model,word):
    by_slot={j:[c for c in model['placements'] if c['slot']==j] for j in range(spec['length'])}
    state=initial(spec,model)
    if 'initial_marks' in model:state['marks']={tuple(p):v for p,v in model['initial_marks']}
    for j,command in enumerate(word):
        skeleton={k:v for k,v in command.items() if k!='inputs'}
        C=next(c for c in by_slot[j] if c['kind']=='command' and c['command']==skeleton)
        if not legal(C,state):return None
        state=advance(C,state)
        guards=[c for c in by_slot[j] if c['kind']=='guard' and c['command']==skeleton and legal(c,state)]
        if not guards:return None
        need(len(guards)==1,'literal prior words distinguish every compatible rule guard')
        state=advance(guards[0],state)
        mode=model['mode_ids'][command['name']] if command['rule']=='block' else 0
        for r in range(model['arity']):
            source=command['inputs'][r] if command['rule']=='block' and r<len(command['inputs']) else None
            candidates=[c for c in by_slot[j] if c.get('input')==r and c.get('mode')==mode
                        and c.get('source')==source]
            need(len(candidates)==1,'every strict-prior source factor or inactive field represented')
            if not legal(candidates[0],state):return None
            state=advance(candidates[0],state)
    need(set(state['totals'])==set(state['roots']) and all(v==12 for v in state['totals'].values()),'whole exact region')
    return tuple(sorted(state['selected']))

def compare(spec,original,marked,inventory):
    definitions={d['name']:d for d in inventory['native_blocks']};choices=[]
    for j,commands in enumerate(original['domains']):
        row=[]
        for c in commands:
            if c['rule']=='block':
                n=len(definitions[c['name']]['premises'])
                row.extend(dict(c,inputs=list(refs)) for refs in itertools.product(range(j),repeat=n))
            else:row.append(c)
        choices.append(row)
    total=0;before=set();after=set();accepted=[]
    for word in itertools.product(*choices):
        total+=1;old=point_word(spec,original,word);new=point_word(spec,marked,word)
        need((old is None)==(new is None),'no valid finite word lost or invented by failure markings')
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=inventory['native_blocks'],
                     proof=list(word),target=spec['target'])
        try:valid=whole_replay(request)['status']=='accepted'
        except ValueError:valid=False
        need(valid==(old is not None),'independent logical rule cross-check')
        if old is not None:before.add(old);after.add(new);accepted.append(word)
    need(before==after and len(before)>0,'exact solution set preserved')
    return dict(status='passed',words=total,original_regions=len(before),marked_regions=len(after),
        accepted_words_sha256=pin(accepted),line_counts=list(map(len,choices)),
        scope='Complete direct command-word census, every premise tuple, literal original/marked point agreement and independent logical replay. Finite evidence; not a universal compiler theorem.')
