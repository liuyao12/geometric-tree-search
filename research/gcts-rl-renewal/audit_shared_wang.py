"""Independent shared-palette, proof-search, boundary and trajectory audit.

Does not import the new producer or its inventory class. The existing
independently written proof/point and finite-table auditors are reused.
"""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from audit_serialized_kernel import freeze,replay
import audit_semantic_proofs as A,audit_hilbert_incidence as H
from audit_proof_boundary import (PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE,
    expected_constructor,input_bytes,code_bytes,micro_output,heap_records)
from audit_tape_kernel import check_table

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-shared-wang-audit-001')
SPEC='gcts-shared-wang-1:at-most-one-head;accept-absorbing;radius-one;translation-only;doubled-grid'
def sha(b):return hashlib.sha256(b).hexdigest()
def need(t,s):
    if not t:raise ValueError(s)
def table_rows(raw):
    magic,a,q,start,accept,reject,space=struct.unpack_from('<7I',raw);need(magic==0x47544d31,'magic')
    p=28;rows=[];count=0
    for _ in range(q):
        default,direction,mid,tape,n=struct.unpack_from('<5I',raw,p);p+=20
        choices={}
        for j in range(n):
            s,out,w,move,mout=struct.unpack_from('<5I',raw,p);p+=20
            need(s not in choices and 0<=s<a and 0<=w<a and 0<=out<q and move<=2,'row action')
            choices[s]=(out,w,move-1)
        count+=a if default else n;rows.append((default,direction,choices))
    need(p==len(raw),'table length')
    return a,q,start,accept,reject,space,rows,count
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True)
    artifact=DOCS/'shared-wang-001.json.gz';d=json.loads(gzip.decompress(artifact.read_bytes()))
    for n,pin in d['sources'].items():need(sha((HERE/n).read_bytes())==pin,'frozen source '+n)
    for n,pin in d['reused_artifacts'].items():need(sha((DOCS/n).read_bytes())==pin,'earlier artifact '+n)
    prior=json.loads((DOCS/'proof-boundary-001.json').read_text())
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()))
    raw=gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes())
    need(sha(raw)==d['literal_table_sha256']==PINNED_TABLE,'external literal table pin')
    need(sha(A.packed(prior['program']))==d['program_sha256']==PINNED_PROGRAM,'external program pin')
    need(sha(A.packed(micro))==d['micro_sha256']==PINNED_MICRO,'external micro pin')
    law=check_table(micro,raw)
    alph,q,start,accept,reject,space,rows,defined=table_rows(raw);del raw
    need(defined==law['expanded_defined_transitions'],'all defined transitions')
    iv=d['inventory'];expected=dict(copy=alph**3,center=(defined+alph)*alph**2,left=q*alph**3,right=q*alph**3)
    fingerprint=sha((SPEC+'\n'+PINNED_TABLE).encode('ascii'))
    need(iv['families']==expected and iv['tile_types']==sum(expected.values()),'disjoint factor count')
    need(iv['fingerprint']==fingerprint and (iv['symbols'],iv['states'],iv['start'],iv['accept'],iv['configuration_symbols'])==(alph,q,start,accept,alph*(q+1)),'inventory binding')
    labels=['L',*list('B^01:,;'),'#',*['@'+s for s in list('B^01:,;')+['#']],*['S'+str(i) for i in range(micro['tapes'])]]
    need(iv['alphabet']==labels,'literal symbol meanings')
    def delta(state,s):
        default,direction,choices=rows[state]
        return choices.get(s,(default-1,s,direction-1) if default else None)
    def unhead(v):
        need(type(v) is int and 0<=v<alph*(q+1),'symbol range')
        return divmod(v-alph,alph) if v>=alph else None
    def output(a,b,c):
        ha,hb,hc=map(unhead,(a,b,c));need(sum(h is not None for h in (ha,hb,hc))<=1,'at most one head')
        if hb:
            state,s=hb
            if state==accept:return b
            action=delta(state,s);need(action is not None,'center must have action')
            out,w,move=action
            return alph+alph*out+w if move==0 else w
        for h,direction in ((ha,1),(hc,-1)):
            if h and h[0]!=accept:
                action=delta(*h)
                if action and action[2]==direction:return alph+alph*action[0]+b
        return b
    def tile_check(t):
        a,b,c=t['triple'];need(t['identity']==':'.join(map(str,(a,b,c))),'tile identity')
        need(t['S']==b and t['N']==output(a,b,c) and t['W']==[a,b] and t['E']==[b,c],'four exact edge marks')
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_boundary_micro.cpp'),'-o',str(TMP/'runner')],check=True)
    (TMP/'code.bin').write_bytes(code_bytes(micro));summaries=[];rejected=0
    for row in d['cases']:
        need(row['inventory_fingerprint']==fingerprint,'same palette on each query')
        request=row['request'];need(A.pin(request)==row['problem_pin'],'theory/target pin')
        catalog=freeze(row['catalog']);r=freeze(row['result']);n=row['length']
        if row['kind']=='geometry':
            # Canonical JSON sorts dictionary keys, whereas the earlier
            # incidence auditor iterates binder maps in quantifier order.
            # Recover that order from the actual axiom syntax, checking that
            # the metadata has exactly those names. No proof data changes.
            for name,metadata in catalog['configuration']['metadata'].items():
                body=catalog['theory']['axioms'][name];outer=[]
                while body[0]=='all':outer.append(body[1]);body=body[2]
                need(set(outer)==set(metadata['binders']),'all and only declared outer binders')
                metadata['binders']={x:metadata['binders'][x] for x in outer}
        grammar=A.equation_inventory(catalog) if row['kind']=='arithmetic' else H.inventory(catalog)
        search=A.audit_point_run(catalog,n,r);decoded=A.check_decoded(catalog,n,r)
        need(A.packed(r['decoded']['request'])==A.packed(request),'actual discovered proof is input')
        if row['kind']=='arithmetic':
            external=freeze(A.external_problems()['add-one-universal'])
            need(catalog['target']==external['target'] and catalog['theory']==external['theory'],'nominated arithmetic theorem')
        else:
            target=('all','a',('all','u',('imp',('pred','Inc',(('var','a'),('var','u'))),('pred','Point',(('var','a'),)))))
            need(catalog['target']==target,'nominated symbolic incidence statement')
        nodes,root=expected_constructor(micro,row['initial'],request)
        template=prior['cases'][0]['initial'];boundary=micro['boundary']
        for t in range(micro['tapes']):
            need(row['initial']['heads'][t]==template['heads'][t],'fixed logical cursor')
            if t not in (boundary['problem'],boundary['certificate']):
                need(row['initial']['words'][t]==template['words'][t] and row['initial']['capacities'][t]==template['capacities'][t],'fixed bootstrap')
        need(row['fixed_sha256']==sha(row['fixed_word'].encode('ascii')) and row['proof_payload_sha256']==sha(row['free_word'].encode('ascii')),'boundary bytes')
        need(row['initial']['words'][boundary['problem']]==row['fixed_word']+':' and row['initial']['words'][boundary['certificate']]==row['free_word']+':','actual fixed/free bands')
        (TMP/'input.bin').write_bytes(input_bytes(row['initial']))
        constructor=json.loads(subprocess.check_output([str(TMP/'runner'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'output.bin'),'10000000000',str(boundary['old_start'])]))
        end=micro_output(TMP/'output.bin')
        need(constructor['status']=='stopped_state' and heap_records(end['words'][micro['heap']])==nodes,'actual canonical constructor')
        slot=micro['allocation'][0]['slots'][0];need(int(end['words'][slot][::-1],2)==root,'constructed root')
        fresh=json.loads(subprocess.check_output([str(TMP/'runner'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'output.bin'),'10000000000',str(len(micro['rows']))]))
        need(fresh['status']=='accepted','fresh independent execution')
        for key in ('status','micro_steps','physical_steps','micro_fnv64'):
            need(fresh[key]==row['selected'][key]==row['literal'][key],'complete shared execution '+key)
        need(sha((TMP/'output.bin').read_bytes())==row['selected_output_sha256'] and micro_output(TMP/'output.bin')==row['output'],'entire derived output')
        # Reconstruct the initial physical tape independently, then replay the
        # literal prefix to the crop. This pins a picture to the real request.
        tape=[0];lookup={s:i for i,s in enumerate(labels)}
        for t,(w,h,capacity) in enumerate(zip(row['initial']['words'],row['initial']['heads'],row['initial']['capacities'])):
            band=['^']+list(w)+['B']*(capacity-len(w)-1);band[h]='@'+band[h]
            tape.extend([17+t,*[lookup[s] for s in band],8])
        p=row['patch'];state=start;head=0
        for step in range(p['prefix_steps']+p['height']+1):
            if step>=p['prefix_steps']:
                y=step-p['prefix_steps'];left=p['left']
                symbols=[alph+alph*state+tape[x] if x==head else tape[x] for x in range(left-1,left+p['width']+1)]
                need(p['rows'][y]==symbols and p['trajectory'][y]==[step,state,head],'literal trajectory crop')
            if step<p['prefix_steps']+p['height']:
                out,w,move=delta(state,tape[head]);tape[head]=w;head+=move;state=out
        seen=set()
        for tile in p['tiles']:
            x,y=tile['x'],tile['y'];need((x,y) not in seen and 0<=x<p['width'] and 0<=y<p['height'],'crop occupancy');seen.add((x,y))
            need(tile['triple']==p['rows'][y][x:x+3] and tile['N']==p['rows'][y+1][x+1],'actual spacetime tile');tile_check(tile)
            for field in ('S','N','W','E','identity'):
                bad=copy.deepcopy(tile);bad[field]=None
                try:tile_check(bad)
                except (ValueError,TypeError):rejected+=1
                else:raise ValueError('tile mutation accepted')
        need(len(seen)==p['width']*p['height'],'complete crop')
        summaries.append(dict(kind=row['kind'],grammar=grammar,search=search,decoded=decoded,constructor=constructor,
            constructed_nodes=len(nodes),literal_crop_tiles=len(seen),fresh_execution=fresh))
        print(row['kind'],'proof, input and exact Wang crop independently checked',flush=True)
    for control in d['controls']:
        (TMP/'input.bin').write_bytes(input_bytes(control['initial']))
        fresh=json.loads(subprocess.check_output([str(TMP/'runner'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'output.bin'),str(control.get('limit',10**10)),str(len(micro['rows']))]))
        for key in ('status','micro_steps','physical_steps','micro_fnv64'):need(fresh[key]==control['result'][key],'negative/resource control')
        need(sha((TMP/'output.bin').read_bytes())==control['output_sha256'],'control whole output')
    result=dict(status='passed',source_sha256=sha(Path(__file__).read_bytes()),source_artifact=dict(file=artifact.name,sha256=sha(artifact.read_bytes()),bytes=artifact.stat().st_size),
        inventory_fingerprint=fingerprint,table_law=law,families=expected,cases=summaries,controls=len(d['controls']),
        tile_mutations_rejected=rejected,seconds=time.perf_counter()-began,
        scope='Complete fresh finite grammar/search/proof/boundary audits, full independent symbol runs, finite literal lowering law, replayed exact local patches. No full literal-Wang proof search or formal upstream soundness theorem.',
        preliminary_audit='The first attempt audited arithmetic and then stopped at the earlier incidence auditor\'s outer-binder iteration. Canonical JSON sorted binder-map keys. This audit independently recovers binder order from the unchanged axiom syntax, checking exact metadata membership. Measured producer, proofs, traces and machine table are unchanged.')
    (DOCS/'shared-wang-audit-001.json').write_bytes(A.packed(result)+b'\n');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
