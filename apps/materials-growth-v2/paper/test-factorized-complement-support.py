import importlib.util,itertools,json,pathlib,random
spec=importlib.util.spec_from_file_location('support',pathlib.Path(__file__).with_name('factorized-complement-support.py'));s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
r=random.Random(91827);clouds=[{'colors':[['x']],'vectors':[[i,0,0]]} for i in range(3)]
states=solutions=removed=0
for trial in range(100):
    blocks=[]
    for i in range(4):
        points=r.sample(['a','b','c'],2)
        blocks.append({'id':str(i),'inventory':str(r.randrange(3)),'t':[{'point':p,'value':1} for p in points],'markPoints':points,'endpointChoices':[[{'cloud':r.randrange(3)} for _ in range(2)] for side in (0,1)]})
    row={'capacity':2,'required':['a','b','c'],'cloudRadius':0,'blocks':blocks}
    result=s.prune(row,clouds);removed+=len(result['removals'])
    for assignment in itertools.product([None,(0,0),(0,1),(1,0),(1,1)],repeat=4):
        states+=1;totals=dict.fromkeys(row['required'],0);marks={};owners=set();valid=True
        for i,choices in enumerate(assignment):
            if choices is None:continue
            b=blocks[i]
            if b['inventory'] in owners:valid=False;break
            owners.add(b['inventory'])
            for t in b['t']:totals[t['point']]+=1
            for side,index in enumerate(choices):
                point=b['markPoints'][side];value=b['endpointChoices'][side][index]['cloud']
                if point in marks and marks[point]!=value:valid=False
                marks[point]=value
        if valid and all(v==2 for v in totals.values()):
            solutions+=1
            assert all(choices is None or all(index in result['allowed'][i][side] for side,index in enumerate(choices)) for i,choices in enumerate(assignment))
assert solutions>0 and removed>0
print(json.dumps({'models':100,'subsets':states,'solutionsPreserved':solutions,'endpointRemovals':removed,'scope':'Exhaustive scalar singleton-cloud controls; material proof replay separate.'}))
