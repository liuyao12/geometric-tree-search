"""Certificate transport and small-instance reference response algebra.

The executable checker independently implements the algebra. This module
never defines proof rules or replaces acceptance with a host logical callback.
"""
import gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from computation_blocks import compose as one_band
from tape_tree_machine import RAW

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def compile_tools(directory):
    before=time.perf_counter()
    for source,name in (('micro_cert_builder.cpp','builder'),('micro_response_check.cpp','checker')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(directory/name)],check=True)
    return time.perf_counter()-before
def run(exe,args):
    before=time.perf_counter();r=json.loads(subprocess.check_output([str(exe),*[str(a) for a in args]]));r['wall_seconds']=time.perf_counter()-before;return r
def cuts(micro):return [i for i,name in enumerate(micro['names']) if name.startswith('instruction/') or name in ('boundary-token','lookup-record','cons-record')]
def write_cuts(values,path):Path(path).write_bytes(struct.pack('<'+'I'*(len(values)+1),len(values),*values))
def header(path):
    with Path(path).open('rb') as f:values=struct.unpack('<5I3Q',f.read(44))
    magic,n,root,start,out,steps,physical,head=values
    if magic!=0x47444331 or Path(path).stat().st_size!=44+16*n:raise ValueError('certificate transport')
    return dict(nodes=n,root=root,q=start,out=out,steps=steps,physical=physical,head=head)
def write_grammar(path,nodes,root,q,out,steps,physical,head):
    raw=struct.pack('<5I3Q',0x47444331,len(nodes),root,q,out,steps,physical,head)
    Path(path).write_bytes(raw+b''.join(struct.pack('<4I',*n) for n in nodes))

def leaf(micro,node):
    kind,q,b,c=node;t,choices=micro['rows'][q]
    if kind==0:
        out,w,move=choices[RAW[b]];symbol=RAW.index(w)
        band=dict(shift=move,pre=[[0,1,1<<b]],writes=[] if b==symbol else [[0,1,symbol]],extent=[min(0,move),max(0,move)],coefficient=1)
        return dict(q=q,out=out,last=t,steps=1,constant=2+int(move!=0),bands={t:band})
    if kind!=1 or b not in (0,2) or c<1:raise ValueError('sweep')
    move=b-1;mask=sum(1<<RAW.index(s) for s,a in choices.items() if a==[q,s,move])
    if not mask:raise ValueError('sweep law')
    return dict(q=q,out=q,last=t,steps=c,constant=move*c*(c-1)+3*c,
        bands={t:dict(shift=move*c,pre=[[0,c,mask]] if move>0 else [[1-c,1,mask]],writes=[],extent=[min(0,move*c),max(0,move*c)],coefficient=2*c-1)})

def compose(a,b):
    if a['out']!=b['q']:raise ValueError('state mismatch')
    zero=dict(shift=0,pre=[],writes=[],extent=[0,0],coefficient=0)
    constant=a['constant']+b['constant']+a['bands'].get(a['last'],zero)['shift']
    constant+=sum(v['coefficient']*a['bands'].get(t,zero)['shift'] for t,v in b['bands'].items())
    bands={}
    for t in a['bands'].keys()|b['bands'].keys():
        aa=a['bands'].get(t,zero);bb=b['bands'].get(t,zero)
        # Reuse the earlier independently tested interval algebra for this
        # small-instance Python control, not in the executable checker.
        band=one_band(dict(aa,q=0,out=0,steps=0),dict(bb,q=0,out=0,steps=0))
        for k in ('q','out','steps'):band.pop(k)
        band['coefficient']=aa['coefficient']+bb['coefficient']+int(t==a['last']);bands[t]=band
    return dict(q=a['q'],out=b['out'],last=b['last'],steps=a['steps']+b['steps'],constant=constant,bands=bands)
