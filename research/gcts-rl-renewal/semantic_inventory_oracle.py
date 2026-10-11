"""Whole unchanged native checking with explicit generated lemma definitions."""
import copy,hashlib,json,time
from certificate_boundary_search import Oracle,digest
from tape_binary import write_micro_input

class RequestOracle(Oracle):
    def request(self,request,limit=5*10**9,purpose='semantic_inventory'):
        began=time.perf_counter();request=copy.deepcopy(request);initial=self.initial(request)
        inp=self.directory/'input.bin';out=self.directory/'output.bin';write_micro_input(initial,inp)
        self.process.stdin.write(str(inp)+' '+str(out)+' '+str(limit)+'\n');self.process.stdin.flush()
        reply=self.process.stdout.readline()
        if not reply:raise ValueError('native oracle stopped: '+self.process.stderr.read())
        result=json.loads(reply);record=dict(id=len(self.records),request=request,query_target='fixed_assertion',request_sha256=digest(request),
              input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
              result=result,seconds=time.perf_counter()-began,purpose=purpose)
        self.records.append(record);return record
    def query(self,spec,proof,final,limit):
        if not final:raise ValueError('semantic inventory pilot uses only declared fixed query targets')
        return self.request(dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=spec.get('blocks',[]),
                                 proof=proof,target=spec['target']),limit)
    def close(self):
        super().close()
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr):stream.close()

def check_inventory(spec,inventory,oracle,limit=5*10**9):
    taut=['imp',['bot'],['bot']]
    request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=inventory['native_blocks'],proof=[dict(rule='tautology',formula=taut)],target=taut)
    q=oracle.request(request,limit,'check_generated_lemma_definitions')
    status='native_accepted' if q['result']['status']=='accepted' else 'native_rejected' if q['result']['status']=='rejected' else 'unknown_native_inventory'
    return dict(**inventory,status=status,query=q['id'],seconds=q['seconds'])
