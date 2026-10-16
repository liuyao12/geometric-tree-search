"""SOURCE ONLY restricted six-rule open-parameter FOL host checker.

No imports/calls by the author. Existing five-rule ground and universal native
checkers remain unchanged. This version permits declared open parameter terms
and unary generalization under the complete original Gamma side condition.
Its deterministic capture-avoiding substitution uses the legacy native/host
fresh0,fresh1,... spelling; bounded overflow is UNKNOWN, never silent trimming.
No induction, reflexivity, tautology, deduction or block rule is admitted.
"""
import copy
import math
import time

VERSION='arithmetic-open-parameter-six-rule-Q-v1'
ARITIES={'axiom':0,'assumption':0,'instantiate':0,'eq_subst':0,'mp':2,'generalize':1}

class BudgetExceeded(TimeoutError):pass

def require(ok,label):
    if not ok:raise ValueError(label)

def name(value):
    require(type(value) is str and value and len(value.encode())<=64,'bounded nonempty variable/symbol string')
    return value

class QChecker:
    def __init__(self,theory,parameters,gamma,*,deadline,maximum_visits=5000000,maximum_depth=64,maximum_fresh=32):
        require(type(deadline) in (int,float) and math.isfinite(deadline),'finite actual caller deadline')
        require(type(maximum_visits) is int and 0<maximum_visits<=5000000,'bounded checker visits')
        require(type(maximum_depth) is int and 0<maximum_depth<=64,'bounded syntax depth')
        require(type(maximum_fresh) is int and 0<maximum_fresh<=32,'bounded deterministic fresh name suffix')
        self.deadline=deadline;self.maximum_visits=maximum_visits;self.maximum_depth=maximum_depth
        self.maximum_fresh=maximum_fresh;self.visits=0
        require(type(theory) is dict and set(theory)=={'functions','predicates','axioms','schemas'},'whole exact theory')
        require(theory['schemas']==[],'Q adds no induction or unimplemented schema')
        for kind in ('functions','predicates'):
            require(type(theory[kind]) is dict,'signature table')
            for symbol,arity in theory[kind].items():
                name(symbol);require(type(arity) is int and 0<=arity<=4,'declared literal arity')
        require(type(parameters) is list and len(parameters)==len(set(parameters))<=4,'declared distinct parameter names')
        for variable in parameters:name(variable)
        self.theory=copy.deepcopy(theory);self.parameters=tuple(parameters)
        require(type(gamma) is list,'original occurrence-ordered Gamma list')
        self.gamma=copy.deepcopy(gamma)
        for formula in self.theory['axioms'].values():
            self.formula(formula);require(not self.free(formula),'original named axiom closed')
        for formula in gamma:
            self.formula(formula);require(self.free(formula)<=set(parameters),'original context free-variable scope')
        self.forbidden=set().union(*(self.free(f) for f in gamma))

    def tick(self,depth=0):
        self.visits+=1
        if self.visits>self.maximum_visits or depth>self.maximum_depth or time.perf_counter()>=self.deadline:
            raise BudgetExceeded('Q complete syntax/checking unresolved')

    def term(self,value,depth=0):
        self.tick(depth);require(type(value) is list and value,'literal term AST')
        if value[0]=='var':
            require(len(value)==2,'variable fields');name(value[1]);return
        require(len(value)==3 and value[0]=='fun' and type(value[2]) is list,'function AST fields')
        require(value[1] in self.theory['functions'] and len(value[2])==self.theory['functions'][value[1]],'exact term signature/arity')
        for child in value[2]:self.term(child,depth+1)

    def formula(self,value,depth=0):
        self.tick(depth);require(type(value) is list and value,'literal formula AST')
        tag=value[0]
        if tag=='bot':require(len(value)==1,'bottom fields')
        elif tag=='eq':
            require(len(value)==3,'equality fields');self.term(value[1],depth+1);self.term(value[2],depth+1)
        elif tag=='pred':
            require(len(value)==3 and type(value[2]) is list and value[1] in self.theory['predicates']
                    and len(value[2])==self.theory['predicates'][value[1]],'predicate fields/arity')
            for term in value[2]:self.term(term,depth+1)
        elif tag=='all':
            require(len(value)==3,'universal fields');name(value[1]);self.formula(value[2],depth+1)
        else:
            require((tag=='not' and len(value)==2) or (tag in ('imp','and','or') and len(value)==3),'known connective/arity')
            for child in value[1:]:self.formula(child,depth+1)

    def term_names(self,value):
        self.tick()
        return {value[1]} if value[0]=='var' else set().union(*(self.term_names(t) for t in value[2]))

    def free(self,value,all_names=False):
        self.tick();tag=value[0]
        if tag=='all':
            result=self.free(value[2],all_names)
            return result|{value[1]} if all_names else result-{value[1]}
        if tag=='eq':return self.term_names(value[1])|self.term_names(value[2])
        if tag=='pred':return set().union(*(self.term_names(t) for t in value[2]))
        if tag=='bot':return set()
        return set().union(*(self.free(f,all_names) for f in value[1:]))

    def substitute_term(self,value,variable,replacement):
        self.tick()
        if value[0]=='var':return copy.deepcopy(replacement if value[1]==variable else value)
        return ['fun',value[1],[self.substitute_term(t,variable,replacement) for t in value[2]]]

    def substitute(self,value,variable,replacement):
        """Free occurrences only; literal alpha-renaming, no alpha-code merging."""
        self.tick();tag=value[0]
        if tag=='all':
            binder,body=value[1:]
            if binder==variable or variable not in self.free(body):return copy.deepcopy(value)
            if binder in self.term_names(replacement):
                used=self.free(body,True)|self.term_names(replacement)|{variable,binder}
                suffix=0
                while 'fresh'+str(suffix) in used:
                    self.tick();suffix+=1
                if suffix>=self.maximum_fresh:raise BudgetExceeded('fresh namespace unresolved; no incomplete catalogue')
                new='fresh'+str(suffix);body=self.substitute(body,binder,['var',new]);binder=new
            return ['all',binder,self.substitute(body,variable,replacement)]
        if tag=='eq':return ['eq',self.substitute_term(value[1],variable,replacement),self.substitute_term(value[2],variable,replacement)]
        if tag=='pred':return ['pred',value[1],[self.substitute_term(t,variable,replacement) for t in value[2]]]
        if tag=='bot':return ['bot']
        return [tag]+[self.substitute(f,variable,replacement) for f in value[1:]]

    def command(self,command,prior):
        self.tick();require(type(command) is dict,'literal primitive command')
        fields={'axiom':{'name'},'assumption':{'index'},'instantiate':{'universal','term'},
            'eq_subst':{'variable','template','left','right'},'mp':{'antecedent','implication'},'generalize':{'variable','source'}}
        rule=command.get('rule');require(rule in fields and set(command)=={'rule','formula'}|fields[rule],'exact six-rule fields')
        formula=command['formula'];self.formula(formula)
        require(self.free(formula)<=set(self.parameters),'output formula has only declared open parameters')
        def source(index):
            require(type(index) is int and 0<=index<len(prior),'strict-prior ordered source index')
            return prior[index]
        if rule=='axiom':require(self.theory['axioms'].get(name(command['name']))==formula,'exact named original axiom')
        elif rule=='assumption':
            index=command['index'];require(type(index) is int and 0<=index<len(self.gamma)
                and self.gamma[index]==formula,'original indexed context occurrence only')
        elif rule=='instantiate':
            universal,term=command['universal'],command['term'];self.formula(universal);self.term(term)
            require(universal[0]=='all' and self.free(universal)<=set(self.parameters)
                and self.term_names(term)<=set(self.parameters),'declared open instantiation scope')
            require(formula==['imp',universal,self.substitute(universal[2],universal[1],term)],'capture-safe exact implication schema')
        elif rule=='eq_subst':
            variable=name(command['variable']);template=command['template'];self.formula(template)
            self.term(command['left']);self.term(command['right'])
            require(variable not in self.parameters and template[0] in ('eq','pred')
                and self.free(template)<=set(self.parameters)|{variable}
                and self.term_names(command['left'])<=set(self.parameters)
                and self.term_names(command['right'])<=set(self.parameters),'atomic equality hole distinct from all parameters')
            require(formula==['imp',['eq',command['left'],command['right']],['imp',
                self.substitute(template,variable,command['left']),self.substitute(template,variable,command['right'])]],'exact open atomic transport schema')
        elif rule=='mp':require(source(command['implication'])==['imp',source(command['antecedent']),formula],'ordered literal modus ponens')
        else:
            variable=name(command['variable'])
            require(variable in self.parameters and variable not in self.forbidden,'generalization uses full original undischarged Gamma')
            require(formula==['all',variable,source(command['source'])],'genuine unary universal introduction')
        self.tick();return copy.deepcopy(formula)

    def proof(self,commands,target):
        require(type(commands) is list and commands,'nonempty complete word')
        self.formula(target);require(not self.free(target),'exact closed final target')
        prior=[]
        for command in commands:prior.append(self.command(command,prior))
        require(prior[-1]==target,'same original target is final conclusion');self.tick()
        return {'schema':VERSION,'rows':len(prior),'original_Gamma_target_sequent_accepted':True,
            'original_ordered_Gamma':copy.deepcopy(self.gamma),'native_accepted':False,'induction_commands':0,
            'full_PA_accepted':False,'universal_compiler_accepted':False,'visits':self.visits}
