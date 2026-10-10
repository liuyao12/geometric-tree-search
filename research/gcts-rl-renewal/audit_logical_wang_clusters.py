"""Bind derived operational fragments to actual decoded proof contexts.

No imports from the new producer, proof logic, encoder or search. The native
algebra derives every node again; Python independently applies each observed
response and decodes the heap/registers it actually produces. This is finite
evidence, not a formal universal soundness proof.
"""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from audit_proof_boundary import (PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE,
    code_bytes,input_bytes,heap_records,expected_constructor,micro_output)
from audit_tree_kernel import need,packed,decode_input

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-logical-cluster-audit-001');RAW='B^01:,;'
FIELDS=('target','assumptions','registry','theory','forbidden','proved','pending')
BANDS=(0,1,2,3,7,9,8)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sha(x):return hashlib.sha256(packed(x)).hexdigest()
def artifact(a):
    path=DOCS/a['name'];need(digest(path)==a['sha256'] and path.stat().st_size==a['bytes'],'artifact binding')
    raw=gzip.decompress(path.read_bytes());need(len(raw)==a['uncompressed_bytes'],'artifact length');return raw
def free(a):
    tag=a[0]
    if tag=='var':return {a[1]}
    if tag in ('fun','pred'):return set().union(*(free(x) for x in a[2]))
    if tag=='all':return free(a[2])-{a[1]}
    if tag=='bot':return set()
    return set().union(*(free(x) for x in a[1:]))
def apply(response,tapes,heads,base,state,physical_head):
    need(response['q']==state,'fragment incoming state')
    cost=physical_head+int(response['physical_constant']);seen=set()
    for b in response['bands']:
        t=b['tape'];need(t not in seen and 0<=t<len(tapes),'fragment band');seen.add(t);h=heads[t]
        need(0<=h+b['extent'][0]<=h+b['extent'][1]<len(tapes[t]),'fragment frame')
        cost+=b['physical_coefficient']*(base[t]+h)
        for lo,hi,mask in b['pre']:
            need(lo<hi and 0<mask<128,'fragment mask')
            for p in range(lo,hi):need(mask&(1<<tapes[t][h+p]),'fragment input mismatch')
    for b in response['bands']:
        t=b['tape'];h=heads[t]
        for lo,hi,s in b['writes']:
            need(lo<hi and 0<=s<7,'fragment write')
            for p in range(lo,hi):tapes[t][h+p]=s
        heads[t]+=b['shift']
    need(cost>0,'positive literal height')
    return response['out'],base[response['last']]+heads[response['last']],cost
def word(tape):return ''.join(RAW[v] for v in tape[1:]).rstrip('B')
def context(tapes,heads,checkpoint,micro):
    need(heads==checkpoint['heads'] and word(tapes[micro['heap']])==checkpoint['heap'],'checkpoint derived heap and cursors')
    words=[word(tapes[t]) for t in BANDS];need(words==checkpoint['register_words'],'checkpoint derived registers')
    nodes=heap_records(checkpoint['heap'])
    values=[int(w[::-1],2) for w in words]
    def pair(v):need(257<=v<257+len(nodes),'context cons');return nodes[v-257]
    def plain(v):
        result=[]
        while v!=256:a,v=pair(v);result.append(a)
        return result
    def text(v):
        values=plain(v);need(all(0<=b<256 for b in values),'context bytes');return bytes(values).decode('utf-8')
    def value(v):return decode_input(nodes,v)
    target,assumptions,registry,theory,forbidden,proved,pending=values
    entries=[]
    for v in plain(registry):
        name,body=pair(v);premises,conclusion=pair(body)
        entries.append(dict(name=text(name),premises=[value(x) for x in plain(premises)],conclusion=value(conclusion)))
    return dict(target=value(target),assumptions=[value(x) for x in plain(assumptions)],registry=entries,
        theory=value(theory),forbidden=[text(x) for x in plain(forbidden)],
        proved=[value(x) for x in plain(proved)],pending=[value(x) for x in plain(pending)])
def bind_contexts(request,contexts,accepted):
    scopes=[dict(name=b['name'],target=b['conclusion'],assumptions=b['premises'],proof=b['proof']) for b in request['blocks']]
    scopes.append(dict(name='root',target=request['target'],assumptions=[],proof=request['proof']))
    position=0;registry=[];labels=[]
    for scope in scopes:
        count=len(scope['proof']);forbidden=set().union(*(free(a) for a in scope['assumptions']))
        for j in range(count+1):
            if position==len(contexts):
                need(not accepted,'missing accepted context');return labels
            c=contexts[position]
            need(c['target']==scope['target'] and c['theory']==request['theory'],'context target/theory')
            need(c['assumptions']==scope['assumptions'] and c['registry']==registry,'context hypotheses and checked inventory')
            need(len(c['forbidden'])==len(set(c['forbidden'])) and set(c['forbidden'])==forbidden,'open premise variable scope')
            need(c['proved']==[line['formula'] for line in scope['proof'][:j]],'actual prior facts')
            need(c['pending']==scope['proof'][j:],'actual remaining proof lines')
            labels.append(dict(scope=scope['name'],line=j if j<count else None,
                rule=scope['proof'][j]['rule'] if j<count else 'scope-end',
                formula=scope['proof'][j]['formula'] if j<count else scope['target']))
            position+=1
        if scope['name']!='root':registry.insert(0,dict(name=scope['name'],premises=scope['assumptions'],conclusion=scope['target']))
    need(position==len(contexts),'unexpected proof-loop contexts');return labels
def checked_chain(row,micro,events,root):
    initial=row['initial'];tapes=[bytearray(RAW.index(s) for s in '^'+w+'B'*(n-len(w)-1)) for w,n in zip(initial['words'],initial['capacities'])]
    heads=list(initial['heads']);base=[];offset=1
    for n in initial['capacities']:base.append(offset+1);offset+=n+2
    observations={o['node']:o['response'] for o in root['observations']}
    state=micro['start'];p=0;steps=physical=0;contexts=[];fragments=[];beforeevent=-1
    for e in events:
        if e['kind']=='fragment':
            need(e['node'] in observations,'fragment independently derived')
            r=observations[e['node']]
            need(e['from_event']==beforeevent and e['q']==state and e['start_step']==steps and e['start_physical']==physical and e['input_head']==p,'fragment incoming receptor')
            state,p,cost=apply(r,tapes,heads,base,state,p);steps+=r['steps'];physical+=cost
            need(e['out']==state and e['end_step']==steps and e['end_physical']==physical and e['output_head']==p,'fragment outgoing receptor')
            fragments.append(dict(e,response=r,physical_height=cost,literal_width=offset+2))
            beforeevent=e['to_event']
        elif e['kind']=='checkpoint':
            need(e['event']==len(contexts)==beforeevent and state==e['state']==1688 and steps==e['step'] and physical==e['physical'] and p==e['physical_head'],'checkpoint position')
            contexts.append(context(tapes,heads,e,micro))
        else:raise ValueError('event kind')
    need(beforeevent==-2 and state==row['expected']['state'],'terminal state') if 'state' in row['expected'] else need(beforeevent==-2,'terminal fragment')
    need(steps==row['expected']['micro_steps'] and physical==row['expected']['physical_steps'],'complete chain count')
    expected_state=micro['accept'] if row['expected']['status']=='accepted' else micro['reject']
    need(state==expected_state,'whole logical result')
    final=dict(state=state,heads=heads,words=[word(t) for t in tapes])
    labels=bind_contexts(row['request'],contexts,state==micro['accept'])
    lines=[]
    for f in fragments:
        i=f['from_event'];j=f['to_event']
        if i>=0 and labels[i]['line'] is not None:
            accepted=j>=0 and labels[j]['scope']==labels[i]['scope'] and labels[j]['line']==(labels[i]['line']+1 if contexts[j]['pending'] else None)
            lines.append(dict(label=labels[i],input_context=contexts[i],output_context=contexts[j] if accepted else None,
                fragment=f,outcome='line-checked' if accepted else 'line-rejected'))
    return dict(contexts=len(contexts),fragments=len(fragments),lines=lines,final=final,physical_head=p)
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True)
    data=json.loads(gzip.decompress((DOCS/'logical-wang-clusters-001.json.gz').read_bytes()))
    need(data['program_sha256']==PINNED_PROGRAM and data['micro_sha256']==PINNED_MICRO and data['literal_table_sha256']==PINNED_TABLE,'external pins')
    for field,rootpath in (('sources',HERE),('reused_source_pins',HERE),('reused_artifacts',DOCS)):
        for n,pin in data[field].items():need(digest(rootpath/n)==pin,'source/artifact '+n)
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()));need(sha(micro)==PINNED_MICRO,'actual fixed code')
    old=json.loads((DOCS/'proof-boundary-001.json').read_text());program=old['program'];need(sha(program)==PINNED_PROGRAM,'actual fixed program')
    f=program['functions'][66];a=micro['allocation'][66]
    need(f['name']=='proof' and f['code'][36]==['call',32,6,[20]] and f['code'][71]==['jump',36] and f['code'][68]==['move',29,52] and f['code'][70]==['move',20,54],'reviewed line-loop observation site')
    need(micro['entries'][66][36]==1688 and all(r in a['live_in'][36] for r in (1,2,3,4,19,29,20)) and [a['slots'][r] for r in (1,2,3,4,19,29,20)]==list(BANDS),'live receptor registers')
    need(data['observation']==dict(function=66,pc=36,state=1688,heap=micro['heap'],registers=[1,2,3,4,19,29,20],bands=list(BANDS),fields=list(FIELDS)),'observer metadata')
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'micro_line_check.cpp'),'-o',str(TMP/'checker')],check=True)
    (TMP/'code.bin').write_bytes(code_bytes(micro));results=[];mutations=[];rules=set()
    for row in data['cases']:
        need(row['status']=='checked_response','bounded compiler control incomplete')
        p=row['provenance'];path=DOCS/p['artifact'];prior=json.loads(gzip.decompress(path.read_bytes())) if path.suffix=='.gz' else json.loads(path.read_text())
        source=next(r for r in prior['cases'] if r[p['key']]==p['value'])
        need(packed(source['request'])==packed(row['request']) and packed(source['initial'])==packed(row['initial']),'explicit reused proof/input')
        need(sha({k:row['request'][k] for k in ('protocol','theory','target')})==row['problem_pin'],'fixed theorem binding')
        expected_constructor(micro,row['initial'],row['request'])
        events=[json.loads(line) for line in artifact(row['events']).splitlines()];raw=artifact(row['grammar'])
        stored=json.loads(artifact(row['responses']));(TMP/'grammar.bin').write_bytes(raw)
        (TMP/'input.bin').write_bytes(input_bytes(row['initial']));need(digest(TMP/'input.bin')==row['input_sha256'],'exact input')
        ids=[e['node'] for e in events if e['kind']=='fragment'];(TMP/'observed.bin').write_bytes(struct.pack('<'+'I'*(len(ids)+1),len(ids),*ids))
        start=time.perf_counter();r=json.loads(subprocess.check_output([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'grammar.bin'),str(TMP/'output.bin'),str(10**10),str(1500000000),str(TMP/'root.json'),str(TMP/'observed.bin')]))
        need(r['status']=='checked_response' and digest(TMP/'output.bin')==row['output_sha256'],'whole fresh response')
        root=json.loads((TMP/'root.json').read_text());need(root==stored,'all independently rederived observed responses')
        chain=checked_chain(row,micro,events,root);need(chain.pop('final')==micro_output(TMP/'output.bin'),'independent chain whole output')
        for line in chain['lines']:
            if line['outcome']=='line-checked':rules.add(line['label']['rule'])
        # Changed labels, heap claims, context boundaries or responses cannot
        # become authority merely by updating reader-side metadata.
        for kind in ('checkpoint-register','checkpoint-heap','incoming-head','outgoing-state','fragment-node','fragment-cost','fixed-target','open-premise'):
            changed=copy.deepcopy(events);badrow=copy.deepcopy(row);badroot=copy.deepcopy(root)
            e=next(e for e in changed if e['kind']=='checkpoint');f=next(e for e in changed if e['kind']=='fragment')
            if kind=='checkpoint-register':e['register_words'][0]='0'
            elif kind=='checkpoint-heap':e['heap']=e['heap'][:-1]
            elif kind=='incoming-head':f['input_head']+=1
            elif kind=='outgoing-state':f['out']+=1
            elif kind=='fragment-node':f['node']=0xffffffff
            elif kind=='fragment-cost':
                response=next(o['response'] for o in badroot['observations'] if o['node']==f['node'])
                response['physical_constant']=str(int(response['physical_constant'])+1)
            elif kind=='fixed-target':badrow['request']['target']=['bot']
            elif kind=='open-premise' and badrow['request']['blocks']:badrow['request']['blocks'][0]['premises']=[['bot']]
            if kind=='open-premise' and not badrow['request']['blocks']:
                continue
            try:
                if kind in ('fixed-target','open-premise'):
                    # A failed local block can stop before the root target is
                    # read by the proof loop. Bind the complete input first.
                    expected_constructor(micro,badrow['initial'],badrow['request'])
                checked_chain(badrow,micro,changed,badroot)
            except (ValueError,KeyError,IndexError):mutations.append(dict(case=row['name'],kind=kind))
            else:raise ValueError('accepted mutation '+row['name']+' '+kind)
        results.append(dict(name=row['name'],result=r['result'],checker=r,independent_seconds=time.perf_counter()-start,**chain))
        print(row['name'],chain['contexts'],'contexts',len(chain['lines']),'literal line clusters bound',flush=True)
    need(rules=={'axiom','tautology','refl','instantiate','distribute','eq_subst','mp','generalize','induction','assumption','block'},'complete eleven-command coverage')
    result=dict(version='logical-wang-clusters-audit-001',input_sha256=digest(DOCS/'logical-wang-clusters-001.json.gz'),
        source_sha256=digest(__file__),checker_source_sha256=digest(HERE/'micro_line_check.cpp'),
        cases=results,checked_rules=sorted(rules),mutations_rejected=mutations,seconds=time.perf_counter()-began,
        scope='All grammar nodes derived afresh; every observed fragment applied in sequence; actual heap/cursors decoded and bound to theory, target, open hypotheses, forbidden variables, checked inventory, prior facts and pending lines. Reuses the previously audited fixed literal lowering law; compiler and kernel universal soundness remain open.')
    path=DOCS/'logical-wang-clusters-audit-001.json.gz';path.write_bytes(gzip.compress(packed(result)+b'\n',mtime=0))
    print('complete',round(result['seconds'],3),'seconds, mutations',len(mutations),flush=True)
if __name__=='__main__':main()
