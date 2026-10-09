"""Declared component/translation controls. No learned policy or proof search."""
import itertools,json
import wang
from stack_program import equality_program,compile_tm,encode

def words(bound=3):
    return [tuple(p) for n in range(bound+1) for p in itertools.product((0,1),repeat=n)]

def operation_cases():
    cases=[('accept-empty',( ('accept',),),(),(),(0,0),10000),
           ('reject-empty',( ('reject',),),(),(),(0,0),10000)]
    for side in ('L','R'):
        for bit in (0,1):
            p=(('push'+side+str(bit),1),('accept',))
            cases.append(('push-'+side+str(bit),p,(),(),(1,1),10000))
            cases.append(('space-'+side+str(bit),p,(),(),(0,0),10000))
        p=(('pop'+side,1,2,1),('accept',),('reject',))
        for value in ((),(0,),(1,)):
            left=value if side=='L' else (); right=value if side=='R' else ()
            cases.append(('pop-'+side+'-'+repr(value),p,left,right,(1,1),10000))
    p=(('pushL1',3),('reject',),('accept',),('popL',1,1,2))
    cases.append(('forward-backward-control',p,(),(),(1,1),10000))
    cases.append(('nonhalting-loop',( ('jump',0),),(),(),(0,0),1000))
    cases.append(('out-of-range-executed',( ('jump',2),('accept',)),(),(),(0,0),10000))
    cases.append(('unused-dangling-address',( ('accept',),('jump',100)),(),(),(0,0),10000))
    cases.append(('address-128',( ('jump',128),)+(('accept',),)*128,(),(),(0,0),500000))
    return cases

def binary_bytes(value):
    raw=json.dumps(value,ensure_ascii=True,separators=(',',':')).encode('ascii')
    return raw,tuple(int(c) for byte in raw for c in format(byte,'08b'))

def serialized_terms():
    fixtures=[('variable',['var','x']),('zero',['fun','zero',[]]),('successor',['fun','succ',[['var','n']]])]
    nested=['var','x']
    for _ in range(4): nested=['fun','f',[nested]]
    fixtures.append(('nested-term',nested))
    for name,term in fixtures:
        raw,word=binary_bytes(term)
        yield name,raw.decode('ascii'),word,word
        other=word[:-1]+(1-word[-1],)
        yield name+'-altered-bit',raw.decode('ascii'),word,other

def source_controls():
    cases=[]
    def add(name,alphabet,states,table,halt,start,initial):
        compiler=wang.Compiler(tuple(alphabet),tuple(states),table,halt)
        translation=compile_tm(compiler,start); left,right=translation.input(initial)
        source=dict(alphabet=compiler.alphabet,states=compiler.states,halt=halt,start=start,initial=initial,
                    transitions=[(q,s,out,w,d) for (q,s),(out,w,d) in sorted(table.items())])
        d=dict(program=translation.program,width=translation.width,alphabet=translation.alphabet,entries=translation.entries)
        cases.append((name,source,d,left,right))
    add('binary-right-left-stay',('B','1'),('start','walk','back','done'),
        {('start','B'):('walk','1',1),('walk','B'):('back','1',-1),('back','1'):('done','1',0)},
        'done','start',(wang.head('start','B'),))
    add('three-symbol-left-border',('B','a','b'),('q','left','right','done'),
        {('q','B'):('left','a',-1),('left','B'):('right','b',1),('right','a'):('done','b',0)},
        'done','q',(wang.head('q','B'),))
    add('five-symbol-codes',('B','a','b','c','d'),('read','done'),
        {('read',s):('done',s,0) for s in ('B','a','b','c','d')},'done','read',(wang.head('read','d'),))
    add('undefined-transition',('B','1'),('read','done'),{},'done','read',(wang.head('read','1'),))
    c=wang.addition_machine()
    initial=('B',wang.head('take','1'),'+','1','=','1','1','$','B')
    t=compile_tm(c,'take'); left,right=t.input(initial)
    source=dict(alphabet=c.alphabet,states=c.states,halt=c.halt,start='take',initial=initial,
                transitions=[(q,s,out,w,d) for (q,s),(out,w,d) in sorted(c.transitions.items())])
    cases.append(('unary-addition',source,dict(program=t.program,width=t.width,alphabet=t.alphabet,entries=t.entries),left,right))
    return cases
