"""Fixed table serialization and observation, never runtime proof decisions."""
import struct
from pathlib import Path
from tape_tree_machine import physical_input,RAW

def write_machine(p,d,path):
    alphabet={s:i for i,s in enumerate(p['alphabet'])};reads={v[3]:int(q) for q,v in p['entries'].items()}
    with Path(path).open('wb') as out:
        def words(*values):out.write(struct.pack('<'+'I'*len(values),*values))
        words(0x47544d31,len(alphabet),len(p['rows']),p['start'],p['accept'],p['reject'],p['space'])
        for q,row in enumerate(p['rows']):
            default,choices=(None,{}) if row is None else row
            micro=reads.get(q);tape=0 if micro is None else d['rows'][micro][0]
            words(0 if default is None else default[0]+1,1 if default is None else default[1]+1,0 if micro is None else micro+1,tape,len(choices))
            for s,(n,w,move) in sorted(choices.items(),key=lambda kv:alphabet[kv[0]]):
                mout=0 if micro is None or s[1:] not in d['rows'][micro][1] else d['rows'][micro][1][s[1:]][0]
                words(alphabet[s],n,alphabet[w],move+1,mout)
def write_input(p,initial,path):
    alphabet={s:i for i,s in enumerate(p['alphabet'])};tape=physical_input(initial)
    with Path(path).open('wb') as out:
        values=[0x47544931,len(initial['capacities']),*initial['capacities'],len(tape),*(alphabet[s] for s in tape)]
        out.write(struct.pack('<'+'I'*len(values),*values))
def read_output(p,initial,path):
    raw=Path(path).read_bytes();values=struct.unpack('<'+'I'*(len(raw)//4),raw)
    magic,state,head,n,*tape=values
    if magic!=0x47544f31 or n!=len(tape):raise ValueError('output length')
    symbols=[p['alphabet'][s] for s in tape];words=[];heads=[];start=1
    for i,capacity in enumerate(initial['capacities']):
        if symbols[start]!='S'+str(i):raise ValueError('output header')
        band=symbols[start+1:start+capacity+1];marked=[j for j,s in enumerate(band) if s.startswith('@')]
        if len(marked)==0 and state==p['space'] and head==start+capacity+1:j=capacity
        elif len(marked)==1:j=marked[0];band[j]=band[j][1:]
        else:raise ValueError('output logical head count')
        if band[0]!='^' or symbols[start+capacity+1]!='#':raise ValueError('output tape bounds')
        heads.append(j);words.append(''.join(band[1:]).rstrip('B'));start+=capacity+2
    return dict(state=state,head=head,heads=heads,words=words)

def write_micro(d,path):
    with Path(path).open('wb') as out:
        def words(*values):out.write(struct.pack('<'+'I'*len(values),*values))
        words(0x47544d32,len(d['rows']),d['start'],d['accept'],d['reject'],d['space'])
        for row in d['rows']:
            tape,choices=(0,{}) if row is None else row;words(tape,len(choices))
            for s,(q,w,move) in sorted(choices.items()):words(RAW.index(s),q,RAW.index(w),move+1)
def write_micro_input(initial,path):
    with Path(path).open('wb') as out:
        values=[0x47544d33,len(initial['words'])]
        for w,h,n in zip(initial['words'],initial['heads'],initial['capacities']):
            body=['^']+list(w)+['B']*(n-len(w)-1);values.extend([n,h,*(RAW.index(s) for s in body)])
        out.write(struct.pack('<'+'I'*len(values),*values))
def read_micro_output(path):
    raw=Path(path).read_bytes();v=struct.unpack('<'+'I'*(len(raw)//4),raw);magic,state,nt=v[:3]
    if magic!=0x47544d34:raise ValueError('micro output magic')
    cursor=3;heads=[];words=[]
    for _ in range(nt):
        h,n=v[cursor:cursor+2];cursor+=2;body=v[cursor:cursor+n];cursor+=n
        heads.append(h);words.append(''.join(RAW[a] for a in body[1:]).rstrip('B'))
    if cursor!=len(v):raise ValueError('micro output length')
    return dict(state=state,heads=heads,words=words)
