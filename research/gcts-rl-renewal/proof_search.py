"""Learned rewrite-sequence proposals, packed Wang proofs and fair bounds.

Proposals receive no validity privilege. Valid word derivations compile to a
complete rectangle preference; lazy_wang still checks every placed constituent
through global dead/forced scheduling and retains every base alternative.
The universal proof relation is directed finite word reachability, not the
separate first-order Hilbert kernel. Linking that kernel remains explicit work.
"""
import itertools,random,time
from collections import Counter
from turtle import Policy
from rewrite_machine import check_derivation
import lazy_wang,wang

def singles(theory,word,capacity):
    for rule,(left,right) in enumerate(theory.rules):
        for position in range(len(word)+1):
            if word[position:position+len(left)]==left:
                new=word[:position]+right+word[position+len(left):]
                if len(new)<=capacity:yield ((rule,position),new)

def actions(theory,word,capacity):
    for command,after in singles(theory,word,capacity):
        yield (command,),after
        for second,last in singles(theory,after,capacity):yield (command,second),last

def distance(a,b):
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        next_row=[i]
        for j,y in enumerate(b,1):next_row.append(min(next_row[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=next_row
    return row[-1]

def features(theory,word,target,sequence,after):
    counts=Counter(rule for rule,pos in sequence)
    out={"distance_gain":distance(word,target)-distance(after,target),
         "length_distance_gain":abs(len(word)-len(target))-abs(len(after)-len(target)),
         "base_steps":len(sequence),"certificate_bytes":-sum(2+pos for rule,pos in sequence)}
    out.update({f"rule:{r}":n for r,n in counts.items()});return out

def propose(machine,source,capacity,seed,policy,max_actions=8,learn=False,machine_step_limit=10000):
    start=time.monotonic();rng=random.Random(seed);word=tuple(source);commands=[];traces=[];expansions=[]
    for _ in range(max_actions):
        if word==machine.target:break
        candidates=list(actions(machine.theory,word,capacity))
        if not candidates:break
        fs=[features(machine.theory,word,machine.target,seq,after) for seq,after in candidates]
        if learn:i,gradient=policy.select(rng,fs);traces.append(gradient)
        else:
            indexes=list(range(len(candidates)));rng.shuffle(indexes)
            i=max(indexes,key=lambda j:sum(policy.weights[k]*v for k,v in fs[j].items()))
        seq,after=candidates[i];executed=[]
        for command in seq:
            if word==machine.target:break
            options=dict(singles(machine.theory,word,capacity))
            if command not in options:raise AssertionError("proposal lost a rule constituent")
            word=options[command];commands.append(command);executed.append(command)
        expansions.append({"proposed":seq,"executed":executed})
    tokens=machine.certificate_tokens(commands);verified,derivation=check_derivation(machine.theory,tuple(source),machine.target,commands,capacity)
    operational=machine.run(source,capacity,tokens,step_limit=machine_step_limit) if verified else None
    if operational:assert operational['status']!='reject',"compiled checker disagrees with independently valid word proof"
    steps=operational['steps'] if operational else None
    reward=(1 if verified else -.5)+.1*(distance(tuple(source),machine.target)-distance(word,machine.target))-.002*len(commands)-(steps or 0)/10000
    if learn:policy.update(traces,reward)
    return {"seed":seed,"status":"checked_rewrite_proposal" if verified else "no_proof_within_proposal_budget",
            "commands":commands,"derivation":derivation,"tokens":tokens,"expansions":expansions,
            "base_steps":len(commands),"sequence_extra_steps":sum(max(0,len(e['executed'])-1) for e in expansions),
            "machine_steps":steps,"machine_status":operational['status'] if operational else None,
            "machine_step_budget":machine_step_limit,"reward":reward,"seconds":time.monotonic()-start,
            "scope":"bounded learned word-rule sequence proposal; final validity checked independently and by compiled TM"}

def rectangle_preference(machine,source,capacity,certificate_length,height,proposal):
    if proposal['status']!='checked_rewrite_proposal' or len(proposal['tokens'])>certificate_length:return None
    tokens=tuple(proposal['tokens'])+('_',)*(certificate_length-len(proposal['tokens']))
    result=machine.run(source,capacity,tokens,step_limit=height+1)
    if result['status']!='accept' or result['steps']>height:return None
    rows=result['rows'];rows.extend([rows[-1]]*(height-result['steps']))
    return lazy_wang.preferred_from_rows(machine.compiler,rows)

def pack(result):
    """Lossless finite point certificate; repeated tile types occur once."""
    out={k:v for k,v in result.items() if k not in ('rows','placements','initial','tile_generations')}
    if not result.get('verified'):return out
    symbols=set()
    for x,y,t in result['placements']:symbols.update(t['triple']);symbols.add(t['N'])
    symbols=sorted(symbols,key=repr);ids={s:i for i,s in enumerate(symbols)}
    types=[];registry={};grid=[[] for _ in range(result['height'])]
    for x,y,t in result['placements']:
        key=tuple(ids[s] for s in t['triple'])+(ids[t['N']],)
        if key not in registry:registry[key]=len(types);types.append(key)
        assert len(grid[y])==x;grid[y].append(registry[key])
    out['certificate']={"symbols":symbols,"tile_types_used":types,"grid":grid,
                        "initial":[ids[s] for s in result['initial']],"placed_tile_generation":1}
    return out

def immutable(value):return tuple(immutable(v) for v in value) if isinstance(value,list) else value

def unpack(data):
    cert=data['certificate'];symbols=[immutable(s) for s in cert['symbols']]
    if len(symbols)!=len(set(symbols)):raise ValueError("duplicate symbol ids")
    if data['marking'] not in ('standard-Wang-colors','redundant-neighbor-values'):raise ValueError("unknown marking control")
    if type(cert['placed_tile_generation']) is not int or cert['placed_tile_generation']!=1:raise ValueError("invalid tile generation")
    types=[]
    for a,b,c,n in cert['tile_types_used']:
        if any(type(i) is not int or not 0<=i<len(symbols) for i in (a,b,c,n)):raise ValueError("invalid symbol id")
        aa,bb,cc,nn=(symbols[i] for i in (a,b,c,n))
        types.append({"S":bb,"N":nn,"W":(aa,bb),"E":(bb,cc),"triple":(aa,bb,cc)})
    grid=cert['grid'];width=data['width'];height=data['height']
    if type(width) is not int or type(height) is not int or width<3 or height<1:raise ValueError("invalid rectangle dimensions")
    if len(grid)!=height or any(len(row)!=width for row in grid):raise ValueError("invalid grid shape")
    if len(cert['initial'])!=width or any(type(i) is not int or not 0<=i<len(symbols) for i in cert['initial']):raise ValueError("invalid initial symbol id")
    placements=[];rows=[tuple(symbols[i] for i in cert['initial'])]
    for y,row in enumerate(grid):
        if any(type(i) is not int or not 0<=i<len(types) for i in row):raise ValueError("invalid tile id")
        placements.extend((x,y,types[i]) for x,i in enumerate(row));rows.append(tuple(types[i]['N'] for i in row))
    return rows,placements

def replay(machine,source,capacity,certificate_length,height,data):
    try:
        rows,placements=unpack(data);pattern=machine.pattern(source,capacity,certificate_length)
        if data['height']!=height or data['width']!=len(pattern):return False
        if not lazy_wang.independent_check(machine.compiler,pattern,machine.accepting_row(len(pattern)),rows,placements,
                                           extended=data['marking']=='redundant-neighbor-values'):return False
        tokens=rows[0][capacity+4:capacity+4+certificate_length];commands=machine.parse_certificate(tokens)
        return check_derivation(machine.theory,tuple(source),machine.target,commands,capacity)[0]
    except (ValueError,KeyError,TypeError,IndexError,RecursionError):return False

def bounds(minimum_capacity,stage):
    """A finite dovetail over powers of two and increasing node budgets.

    Padding permits any shorter certificate; absorbing acceptance permits any
    larger height. Every fixed triple is revisited with unbounded node budget.
    Thus every finite proof is eventually covered in unlimited execution.
    """
    for a in range(stage+1):
        capacity=2**a
        if capacity<minimum_capacity:continue
        for b in range(stage-a+1):
            for c in range(stage-a-b+1):yield capacity,2**b,2**c,2**stage

def fair_search(machine,source,max_stage=None,extended=True,policy=None,proposal_actions=8,seed=0):
    attempts=0;history=[];start=time.monotonic();minimum=max(len(source),len(machine.target))
    for stage in itertools.count():
        if max_stage is not None and stage>max_stage:
            return {"status":"unknown_outer_stage_budget","attempts":attempts,"seconds":time.monotonic()-start,"recent_attempts":history[-16:]}
        for capacity,certificate_length,height,nodes in bounds(minimum,stage):
            pattern=machine.pattern(source,capacity,certificate_length)
            preferred=None
            if policy is not None:
                proposal=propose(machine,source,capacity,seed+attempts,policy,max_actions=proposal_actions)
                preferred=rectangle_preference(machine,source,capacity,certificate_length,height,proposal)
            result=lazy_wang.search(machine.compiler,pattern,height,machine.accepting_row(len(pattern)),node_limit=nodes,seconds=float('inf'),extended=extended,preferred=preferred)
            attempts+=1;history.append({"stage":stage,"capacity":capacity,"certificate_length":certificate_length,"height":height,"node_budget":nodes,"status":result['status']})
            if len(history)>32:history=history[-16:]
            if result.get('verified'):
                return {"status":"proof_found_by_fair_bounds","capacity":capacity,"certificate_length":certificate_length,
                        "height":height,"attempts":attempts,"seconds":time.monotonic()-start,"proof":pack(result),"recent_attempts":history}
