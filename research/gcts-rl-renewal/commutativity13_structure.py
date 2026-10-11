"""Read-only exact comparison of visited structural tree skeletons."""
import hashlib
import json

def skeleton(tree,path,baseline=None):
    digest=hashlib.sha256();nodes=0;equal=True;stack=[tree]
    previous=open(baseline,'rb') if baseline else None
    try:
        with open(path,'wb') as sink:
            while stack:
                n=stack.pop();value=[n['kind'],n['point'],n['state_sha256'],n.get('alternatives'),[c['key'] for c in n['children']]]
                word=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()+b'\n'
                sink.write(word);digest.update(word);nodes+=1
                if previous and previous.readline()!=word:equal=False
                stack.extend(c['tree'] for c in reversed(n['children']))
        if previous and previous.read(1):equal=False
    finally:
        if previous:previous.close()
    return dict(structural_sha256=digest.hexdigest(),structural_nodes=nodes,
                exact_structural_equal_to_base=equal if baseline else True,
                structural_scope='Exactpreorder kind/point/statehash/completealternatives/visitedchildkeys bytecomparison; policyhint/event metadata deliberately excluded from this structural projection and independently checked in full tree replay.')
