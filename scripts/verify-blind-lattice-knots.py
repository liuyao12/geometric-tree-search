"""Independent blind-bank coverage, lattice movie, and learned proof audit."""
import sys,json,gzip,hashlib,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/knot-classifier'))
from verify_lattice_movie import verify,loop,edges
from verify_extension_proofs import replay_event

def require(condition,message):
    if not condition: raise ValueError(message)

def face_groups(diff):
    groups=[]
    for e in diff:
        a,b=tuple(e); axis=next(i for i in range(3) if a[i]!=b[i])
        for j in range(3):
            if j==axis: continue
            for sign in (-1,1):
                c=tuple(x+(sign if i==j else 0) for i,x in enumerate(b));d=tuple(x+(sign if i==j else 0) for i,x in enumerate(a))
                f=[a,b,c,d];groups.append({frozenset((u,v)) for u,v in zip(f,f[1:]+f[:1])}&diff)
    return groups

def translated(signature,origin):
    return {frozenset(tuple(x+origin[i] for i,x in enumerate(p)) for p in e) for e in json.loads(signature)}

def verify_report(path):
    started=time.perf_counter();path=Path(path);data=json.loads(path.read_text());refs=data['references'];cases=data['cases'];bounds=data['bounds']
    corpus_path=Path(__file__).resolve().parents[1]/'research/knot-classifier/lattice-corpus-12.json'
    corpus=json.loads(corpus_path.read_text())['records'];scaled=data.get('stage')=='scale12';retry=data.get('stage')=='retry-six'
    bank={r['id']:r for r in corpus if 3<=r['crossings']<=(12 if scaled else 8)}
    require(len(bank)==(2977 if scaled else 35) and len(refs)==len(bank) and {r['evaluatorKnot'] for r in refs}==set(bank),'Incomplete prime bank')
    def shuffle(values,seed):
        values=list(values)
        for i in range(len(values)-1,0,-1):
            seed=(1664525*seed+1013904223)&0xffffffff;j=(seed*(i+1))//4294967296;values[i],values[j]=values[j],values[i]
        return values
    ordered=list(bank)
    if retry:
        parent_path=path.parent/data['parent']['file'];raw=parent_path.read_bytes();parent=json.loads(raw)
        require(hashlib.sha256(raw).hexdigest()==data['parent']['sha256'],'Changed immutable parent')
        chosen=[r['caseIndex'] for r in next(l for l in parent['lanes'] if l['learn'])['runs'] if r['status']=='unknown']
        require(data['parent']['caseIndices']==chosen and refs==parent['references'],'Retry changed cases or bank')
        expected=[dict(parent['cases'][i],originalCaseIndex=parent['cases'][i].get('originalCaseIndex',i)) for i in chosen]
        require(cases==expected,'Retry changed input or provenance')
    elif scaled:
        require(hashlib.sha256(corpus_path.read_bytes()).hexdigest()==data['corpusSha256'],'Changed scaling corpus')
        selected=[k for n in range(9,13) for k in ([r['id'] for r in corpus if r['crossings']==n][0],[r['id'] for r in corpus if r['crossings']==n][-1])]
        require(data['selectedTypes']==selected and len(cases)==24,'Pilot selection or coverage')
        require([(r['evaluatorKnot'],r['seed']) for r in refs]==shuffle([(k,57011+i*7919 if k in selected else None) for i,k in enumerate(ordered)],717171),'Scaling reference seed/order mismatch')
        require([(r['evaluatorKnot'],r['seedIndex'],r['inputSeed']) for r in cases]==shuffle([(k,j,97003+i*104729+j*15485863) for i,k in enumerate(ordered) if k in selected for j in range(3)],626262),'Scaling query seed/order mismatch')
    else:
        require(len(cases)==105 and {(r['evaluatorKnot'],r['seedIndex']) for r in cases}=={(k,s) for k in bank for s in range(3)},'Incomplete seeded cases')
        require([(r['evaluatorKnot'],r['seed']) for r in refs]==shuffle([(k,31013+i*7919) for i,k in enumerate(ordered)],515151),'Reference seed/order mismatch')
        require([(r['evaluatorKnot'],r['seedIndex'],r['inputSeed']) for r in cases]==shuffle([(k,j,81017+i*104729+j*15485863) for i,k in enumerate(ordered) for j in range(3)],424242),'Query seed/order mismatch')
    require(all(c['inputSeed']!=next(r['seed'] for r in refs if r['evaluatorKnot']==c['evaluatorKnot']) for c in cases),'Shared source/reference seed')
    require(data['region'] is None and data['stepsPerIndependentScramble']==8 and bounds['maxDepth']==16 and bounds['maxEdges']==240,'Changed benchmark scope')
    provenance=0;nontrivialInputs=sum(edges(loop(c['vertices']))!=edges(loop(next(r['vertices'] for r in refs if r['evaluatorKnot']==c['evaluatorKnot']))) for c in cases)
    for r in refs+cases:
        p=r['provenance']
        if p is None:
            require(scaled and r in refs and r['evaluatorKnot'] not in data['selectedTypes'] and edges(loop(r['vertices']))==edges(loop(bank[r['evaluatorKnot']]['vertices'])),'Noncanonical unproven reference');continue
        require(len(p['steps'])==8 and p['options'].get('region') is None,'Not an unrestricted eight-step scramble')
        require(edges(loop(p['source']))==edges(loop(bank[r['evaluatorKnot']]['vertices'])) and edges(loop(p['target']))==edges(loop(r['vertices'])),'Provenance endpoints')
        verify(p);provenance+=1
    require(not data['incomplete'] and len(data['lanes'])==2,'Incomplete experiment')
    for lane in data['lanes']:
        for i,stub in enumerate(lane['runs']):
            if 'artifact' not in stub:continue
            artifact=stub['artifact'];raw=(path.parent/artifact['file']).read_bytes();require(len(raw)==artifact['bytes'] and hashlib.sha256(raw).hexdigest()==artifact['sha256'] and artifact['format']=='json.gz','Query artifact integrity')
            run=json.loads(gzip.decompress(raw));require(all(run[k]==v for k,v in stub.items() if k!='artifact'),'Query manifest summary mismatch');lane['runs'][i]=run
    root_rules={};event_meta={};labels=proofs=movies=cancelled_movies=0;movieKinds={};movieLengths={};lane_summary=[]
    for lane in data['lanes']:
        require(not lane['incomplete'] and len(lane['runs'])==len(cases) and lane['bounds']==bounds,'Lane coverage or mismatched bounds')
        counters={'root':0,'local':0,'capacity':0};versions={k:0 for k in counters};case_events={};probePrefixes={ch:[0] for ch in counters};activationPrefixes={ch:[0] for ch in counters}
        if lane['learn']:
            arch=lane['proofArchive'];parts=arch.get('files',[arch]);joined=hashlib.sha256();size=0
            for part in parts:
                raw=(path.parent/part['file']).read_bytes();require(hashlib.sha256(raw).hexdigest()==part['sha256'] and len(raw)==part['bytes'],'Archive part integrity');joined.update(raw);size+=len(raw)
            require(joined.hexdigest()==arch['sha256'] and size==arch['bytes'],'Joined archive integrity')
            def proof_lines():
                for part in parts:
                    with gzip.open(path.parent/part['file'],'rt') as stream:yield from stream
            for line in proof_lines():
                entry=json.loads(line);ch=entry['channel'];event=entry['event'];require(entry['eventIndex']==counters[ch],'Proof index discontinuity');counters[ch]+=1
                case_events.setdefault((entry['caseIndex'],ch),[]).append(entry['eventIndex'])
                if ch in ('root','local'):
                    require(hashlib.sha256(event['signature'].encode()).hexdigest()==entry['proofId'],'Proof digest')
                    n=replay_event(event);labels+=n;proofs+=1
                    require(event['width']==len(json.loads(event['signature'])) and event['width']<=(480 if ch=='root' else 48),'Proof support scope')
                    require(all(s['horizon']<=16 for s in event['samples']) if ch=='root' else True,'Root horizon scope')
                    if ch=='root':
                        require(entry['proofId'] not in root_rules,'Repeated root catalog insertion')
                        root_rules[entry['proofId']]={'signature':event['signature'],'lower':event['lower'],'caseIndex':entry['caseIndex']}
                else:
                    w=event['width'];require(w in (1,2) and len(event['samples'])==2**w,'Capacity profiles')
                    require({tuple(s['profile']) for s in event['samples']}=={tuple((b>>i)&1 for i in range(w)) for b in range(2**w)},'Capacity profile coverage')
                    for sample in event['samples']:
                        positive=not any(sample['profile']);require(sample['outcome']==('positive' if positive else 'negative'),'Capacity outcome')
                        require(all(v is None or v==sample['profile'][i] for i,v in enumerate(event['values']))==positive,'Capacity stencil')
                node_limit=bounds['rootProbeNodeCap'] if ch=='root' else bounds['extensionProbeNodeCap'] if ch=='local' else 64
                require(all(type(s['nodes']) is int and 0<=s['nodes']<=node_limit for s in event['samples']),'Probe node accounting')
                probePrefixes[ch].append(probePrefixes[ch][-1]+sum(s['nodes'] for s in event['samples']))
                activationPrefixes[ch].append(activationPrefixes[ch][-1]+(sum(s['nodes'] for s in event['samples'] if s['outcome']!='unresolved') if ch!='capacity' else 0))
                event_meta[(ch,entry['eventIndex'])]=event['activated']
            require(counters==arch['eventCounts'],'Archive counts')
        correct=incorrect=unknown=totalnodes=0;bytype={k:{'correct':0,'incorrect':0,'unknown':0} for k in bank};byseed={str(i):{'correct':0,'incorrect':0,'unknown':0} for i in range(3)};stats={};rootexcluded=0;rootReuse=0;rootCrossTypeReuse=0
        for i,run in enumerate(lane['runs']):
            require(run['caseIndex']==i,'Query permutation changed');query=cases[i]
            for ch,field in [('root','rootLearning'),('local','extensions'),('capacity','learning')]:
                model=run[field]
                if not lane['learn']:require(model is None,'Brute force imported markings');continue
                require(model['initialVersion']==versions[ch],'Catalog reset or unexplained import')
                lo,hi=model['archiveRange'];require(list(range(lo,hi))==case_events.get((i,ch),[]),'Missing case proof events')
                require(model['nodes']==probePrefixes[ch][hi],'Probe subtotal differs from archived events')
                if ch!='capacity':require(model['activationValidationNodes']==activationPrefixes[ch][hi] and model['transferValidationNodes']==0,'Activation/transfer cost accounting')
                require(model['version']==versions[ch]+sum(event_meta[(ch,j)] for j in range(lo,hi)),'Version change not supported by new proof events');versions[ch]=model['version']
            root=run['rootGraph'];require(root['point']=='reference-choice' and root['boundary']==[['root-budget',0]],'Root point model')
            require([c['id'] for c in root['candidates']]==list(range(len(root['candidates']))) and len(root['candidates'])<=len(refs),'Root reference domain')
            admitted=[]
            for candidate in root['candidates']:
                require(candidate['t']==[['reference-choice',1]],'Root tile t')
                if lane['learn']:
                    diff=edges(loop(query['vertices']))^edges(loop(refs[candidate['id']]['vertices']));union=set();membership={};lower=0
                    for index,component in enumerate(candidate['components']):
                        rule=root_rules[component['proofId']];require(rule['caseIndex']<=i and component['lower']==rule['lower'],'Root proof unavailable or altered')
                        rootReuse+=int(rule['caseIndex']<i);rootCrossTypeReuse+=int(rule['caseIndex']<i and cases[rule['caseIndex']]['evaluatorKnot']!=query['evaluatorKnot']);support=translated(rule['signature'],component['origin']);require(not union&support,'Overlapping discrepancy components');union|=support
                        for e in support:membership[e]=index
                        lower+=rule['lower']
                    require(union==diff,'Root windows do not match actual endpoint discrepancy')
                    require(all(len({membership[e] for e in group})<=1 for group in face_groups(diff)),'Component lower bounds cannot be summed')
                    require(lower==candidate['lower'],'Root composed bound')
                else:require(candidate['lower']==0 and candidate['components']==[],'Unmarked root has hidden filters')
                require(candidate['m']==([['root-budget',1]] if candidate['lower']>bounds['maxDepth'] else []),'Root elimination not a proved marking mismatch')
                if not candidate['m']:admitted.append(candidate['id'])
            if root['complete']:
                require(len(root['candidates'])==len(refs) and root['forward']==[['reference-choice',admitted]] and root['reverse']==[[j,['reference-choice']] for j in admitted],'Incomplete root incidence')
            else:require(run['status']=='unknown' and not root['forward'] and not root['reverse'],'Partial root claimed complete')
            require(run['referenceChecks']==len(root['candidates']) and run['referencesAdmitted']==len(admitted),'Root accounting')
            rootexcluded+=len(root['candidates'])-len(admitted)
            attempts=[a for c in run['comparisons'] for a in c['attempts']]+[a for c in run['retired'] for a in c.get('attempts',[])]
            require(run['nodes']==sum(a['stats'].get('nodes',0) for a in attempts) and run['nodes']<=bounds['nodeCap'],'Aggregate node cost')
            for attempt in attempts:
                require(0<=attempt['depth']<=bounds['maxDepth'],'Contour horizon')
                for k,v in attempt['stats'].items():stats[k]=max(stats.get(k,0),v) if k.startswith('peak') or k.endswith('Versions') else stats.get(k,0)+v
            totalnodes+=run['nodes'];certificate=run['certificate']
            if run['status']=='identified':
                require(root['complete'] and certificate is not None and run['referenceIndex'] in admitted,'Unverified assignment')
                require(edges(loop(certificate['source']))==edges(loop(query['vertices'])) and edges(loop(certificate['target']))==edges(loop(refs[run['referenceIndex']]['vertices'])),'Wrong blind certificate endpoints')
                require(certificate['options'].get('region') is None and certificate['options']['maxEdges']==bounds['maxEdges'] and len(certificate['steps'])<=bounds['maxDepth'],'Restricted positive movie')
                replayed=verify(certificate);movies+=1;movieLengths[str(replayed['tiles'])]=movieLengths.get(str(replayed['tiles']),0)+1
                for kind,n in replayed['kinds'].items():movieKinds[kind]=movieKinds.get(kind,0)+n
                predicted=refs[run['referenceIndex']]['evaluatorKnot'];ok=predicted==query['evaluatorKnot'];require(run['predictedKnot']==predicted and run['correct']==ok,'Evaluator score')
                field='correct' if ok else 'incorrect';correct+=ok;incorrect+=not ok
            else:
                require(run['status']=='unknown' and certificate is None and run['referenceIndex'] is None and run['predictedKnot'] is None and run['correct'] is None,'Unknown became negative or label')
                unknown+=1;field='unknown'
                if run.get('candidateCertificate'):verify(run['candidateCertificate']);cancelled_movies+=1
            bytype[query['evaluatorKnot']][field]+=1;byseed[str(query['seedIndex'])][field]+=1
        require((correct,incorrect,unknown,totalnodes)==(lane['correct'],lane['incorrect'],lane['unknown'],lane['nodes']),'Lane totals')
        require(lane['proofProbeAndValidationNodes']==sum(c['nodes']+c['activationValidationNodes']+c['transferValidationNodes'] for c in lane['proofCosts'].values()),'Combined proof node accounting')
        for ch,field in [('root','rootLearning'),('local','extensions'),('capacity','learning')]:
            require(lane['proofCosts'][ch]['nodes']==((lane['runs'][-1][field] or {}).get('nodes',0)),'Proof cost final snapshot')
        require(abs(lane['queryTotalMs']-sum(r['totalMs'] for r in lane['runs']))<0.01 and lane['totalMs']>=lane['queryTotalMs'],'Total time accounting')
        lane_summary.append({'lane':lane['lane'],'correct':correct,'incorrect':incorrect,'unknown':unknown,'nodes':totalnodes,'totalMs':lane['totalMs'],'queryTotalMs':lane['queryTotalMs'],'rootExcluded':rootexcluded,'priorQueryRootApplications':rootReuse,'crossTypeRootApplications':rootCrossTypeReuse,'statsAggregation':'Counters sum attempts; peak and version fields take the maximum over attempts.','stats':stats,'byType':bytype,'bySeed':byseed})
    return {'verified':True,'provenanceMovies':provenance,'nontrivialInputs':nontrivialInputs,'identificationMovies':movies,'identificationMoveKinds':movieKinds,'certificateLengths':movieLengths,'cancelledUnscoredMovies':cancelled_movies,'extensionProofs':proofs,'resolvedLabels':labels,'lanes':lane_summary,'independentVerificationMs':1000*(time.perf_counter()-started)}

if __name__=='__main__':print(json.dumps(verify_report(sys.argv[1])))
