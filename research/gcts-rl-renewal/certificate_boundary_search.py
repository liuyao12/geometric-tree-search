"""Finite certificate-word search driven solely by the fixed native machine.

Both methods are chronological proof-search controls, not the reference GCTS
point scheduler. The free field grammar is declared and complete within its
bound. Prefix queries use the same theory with the prefix's final formula as
its query target; they cannot change the externally fixed final assertion.
No host logical evaluator or supplied proof is used to decide a search move.
"""
import copy,hashlib,itertools,json,subprocess,time
from pathlib import Path
from proof_boundary import boundary_words
from tape_binary import write_micro_input

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()
RULES=('axiom','generalize','mp','refl','tautology')
def formula_basis(spec):
    found={};variables=set()
    def terms(t):
        if t[0]=='var':variables.add(t[1])
        elif t[0]=='fun':
            for a in t[2]:terms(a)
    def visit(a):
        found[canonical(a)]=a;k=a[0]
        if k=='all':variables.add(a[1]);visit(a[2])
        elif k in ('imp','and','or'):visit(a[1]);visit(a[2])
        elif k=='not':visit(a[1])
        elif k=='eq':terms(a[1]);terms(a[2])
        elif k=='pred':
            for t in a[2]:terms(t)
    visit(spec['target'])
    for a in spec['theory']['axioms'].values():visit(a)
    return [found[k] for k in sorted(found)],sorted(variables)
def choices(spec,slot,basis,variables):
    formulas=[spec['target']] if slot==spec['length']-1 else basis
    rows=[]
    for formula in formulas:
        for name in sorted(spec['theory']['axioms']):rows.append(dict(rule='axiom',formula=formula,name=name))
        for variable in variables:
            for source in range(slot):rows.append(dict(rule='generalize',formula=formula,variable=variable,source=source))
        for antecedent,implication in itertools.product(range(slot),repeat=2):rows.append(dict(rule='mp',formula=formula,antecedent=antecedent,implication=implication))
        rows.extend(dict(rule=rule,formula=formula) for rule in ('refl','tautology'))
    rows.sort(key=lambda r:(r['rule'],canonical(r['formula']),canonical(r)))
    if len({canonical(r) for r in rows})!=len(rows):raise ValueError('duplicate free command')
    return rows
class Oracle:
    def __init__(self,micro,initial,executable,code,directory):
        self.micro=micro;self.template=initial;self.directory=Path(directory);self.directory.mkdir(exist_ok=True,parents=True);self.records=[]
        self.process=subprocess.Popen([str(executable),str(code)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        expected=['READY',str(len(micro['rows'])),*[str(micro[n]) for n in ('start','accept','reject','space')]]
        if self.process.stdout.readline().split()!=expected:raise ValueError('fixed native oracle start')
    def initial(self,request):
        value=copy.deepcopy(self.template);fixed,free=boundary_words(request)
        for t,w in ((self.micro['boundary']['problem'],fixed),(self.micro['boundary']['certificate'],free)):
            value['words'][t]=w+':';value['capacities'][t]=len(w)+3;value['heads'][t]=1
        return value
    def query(self,spec,proof,final,limit):
        began=time.perf_counter();request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=copy.deepcopy(proof),target=spec['target'] if final else proof[-1]['formula']);initial=self.initial(request);inp=self.directory/'input.bin';out=self.directory/'output.bin';write_micro_input(initial,inp)
        self.process.stdin.write(str(inp)+' '+str(out)+' '+str(limit)+'\n');self.process.stdin.flush();reply=self.process.stdout.readline()
        if not reply:raise ValueError('native oracle stopped: '+self.process.stderr.read())
        result=json.loads(reply);record=dict(id=len(self.records),request=request,query_target='fixed_assertion' if final else 'prefix_final_formula',request_sha256=digest(request),input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),result=result,seconds=time.perf_counter()-began);self.records.append(record);return record
    def close(self):
        if self.process.poll() is None:self.process.stdin.write('quit\n');self.process.stdin.flush();self.process.wait(timeout=10)
        if self.process.returncode!=0:raise ValueError(self.process.stderr.read())
class Limit(Exception):pass
def search(spec,oracle,mode='prefix',queries=128,seconds=120,micro_steps=10**9):
    if mode not in ('prefix','flat'):raise ValueError('search control')
    began=time.perf_counter();basis,variables=formula_basis(spec);domains=[choices(spec,j,basis,variables) for j in range(spec['length'])];events=[];path=[];found=None;nodes=0;pruned=0;unknown=0;start_queries=len(oracle.records);limits=dict(queries=spec.get('queries',queries),seconds=seconds,micro_steps=micro_steps)
    def check():
        if len(oracle.records)-start_queries>=limits['queries'] or time.perf_counter()-began>=seconds:raise Limit()
    def visit(slot):
        nonlocal found,nodes,pruned,unknown
        for index,command in enumerate(domains[slot]):
            check();nodes+=1;path.append(index)
            try:
                proof=[domains[j][k] for j,k in enumerate(path)];final=slot==spec['length']-1
                event=dict(slot=slot,choice=index,path=list(path),query=None,action='descend');events.append(event)
                if mode=='prefix' or final:
                    record=oracle.query(spec,proof,final,micro_steps);event.update(query=record['id'],status=record['result']['status'])
                    if record['result']['status']=='rejected':event['action']='reject';pruned+=not final;continue
                    if record['result']['status']!='accepted':event['action']='unknown';unknown+=1;raise Limit()
                    if final:found=dict(proof=proof,path=list(path),query=record['id']);event['action']='accept';return True
                if visit(slot+1):return True
            finally:path.pop()
        return False
    try:ok=visit(0);status='native_proof_discovered' if ok else 'exhausted_finite_certificate_grammar'
    except Limit:status='unknown_search_budget'
    return dict(status=status,mode=mode,grammar=dict(rules=RULES,basis=basis,variables=variables,domains=domains,command_counts=list(map(len,domains)),complete_words=__import__('math').prod(map(len,domains)),final_formula='externally fixed assertion target',blocks=[],scope='Exact line count, five supported command forms, syntactic subformula basis, named input axioms and all strict-prior references. This is a proper finite subset of the fixed machine certificate language.'),events=events,found=found,nodes=nodes,prefix_rejections=pruned,unknown_queries=unknown,queries=len(oracle.records)-start_queries,limits=limits,seconds=time.perf_counter()-began,root_path_restored=not path,scope='Chronological certificate-word control driven by the whole fixed native program, not primitive-square GCTS or new RL training.')
