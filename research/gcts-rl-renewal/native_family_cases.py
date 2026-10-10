"""Declared native training/evaluation boundaries, no proof sequences."""
from native_wang_cases import registry
def inverse(i,height,background=1,margin=0,identity=None):
    width=2*height+1+2*margin;center=width//2;pattern=[[background] for _ in range(width)];pattern[center]={'range':[2*i.A,i.D]};top=[background]*width;top[center]=i.head(i.accept,9)
    boundary=[entry for y in range(height) for entry in ([[-1,2*y],[background,background]],[[2*width-1,2*y],[background,background]])]+[[[2*x,2*height-1],v] for x,v in enumerate(top)]
    return dict(id=identity or 'inverse-'+str(height)+'-background-'+str(background)+'-margin-'+str(margin),title='Unknown predecessor: '+str(height)+' rows, background '+str(background)+', margin '+str(margin),pattern=pattern,height=height,boundary=boundary,accepting=True,scope='A native acceptance fragment with an unknown nonaccepting source state. Not the actual program start or a mathematical proof.')
def donors(i,docs):return [registry(i,docs)[0],registry(i,docs)[2],inverse(i,3,1,identity='donor-inverse-3')]
def training(i):return [inverse(i,2,1,identity='train-short'),inverse(i,3,2,identity='train-symbol'),inverse(i,4,1,identity='train-longer'),inverse(i,3,3,1,'train-margin')]
def evaluation(i,docs):
    boot=dict(registry(i,docs)[2],id='boot-prefix-6',title='Actual boot prefix: six native rows',height=6);w=len(boot['pattern']);boot['boundary']=[entry for y in range(6) for entry in ([[-1,2*y],[1,1]],[[2*w-1,2*y],[1,1]])]
    reject=dict(registry(i,docs)[4]);zero=inverse(i,4,3,1,'zero-budget');zero.update(title='Zero placement budget',attempts=0)
    return [inverse(i,3,4,identity='new-symbol'),inverse(i,4,3,1,'new-interface'),inverse(i,5,2,identity='new-depth'),boot,reject,zero]
