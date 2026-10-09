"""Verified proof-data compaction without changing inference rules or interfaces.

Check the entire supplied request first, including unused material. In a fixed
proof context, an earlier identical formula can replace a later derivation.
Keep the last formula's dependency closure and renumber only actual line refs.
Keep every block's declared premises, including unused eigenvariable blockers.
"""
import copy,json,time
from serialized_kernel import canonical,check

def references(line):
    if line['rule']=='mp':return [line['antecedent'],line['implication']]
    if line['rule']=='generalize':return [line['source']]
    if line['rule']=='block':return list(line['inputs'])
    return []

def compact_lines(lines):
    """Input is already checked in one unchanged assumptions/block context."""
    earliest={};aliases=[]
    for i,line in enumerate(lines):
        key=canonical(line['formula']);aliases.append(earliest.setdefault(key,i))
    root=aliases[-1];live=set();pending=[root]
    while pending:
        i=pending.pop()
        if i in live:continue
        live.add(i);pending.extend(aliases[j] for j in references(lines[i]))
    retained=sorted(live);positions={old:new for new,old in enumerate(retained)};out=[]
    for i in retained:
        line=copy.deepcopy(lines[i]);rule=line['rule']
        for key in ('antecedent','implication') if rule=='mp' else ('source',) if rule=='generalize' else ():
            line[key]=positions[aliases[line[key]]]
        if rule=='block':line['inputs']=[positions[aliases[j]] for j in line['inputs']]
        out.append(line)
    return out,dict(original_lines=len(lines),retained_lines=len(out),aliases=aliases,
        retained=retained,old_to_new=[positions.get(j) for j in aliases],root=root,
        duplicates=sum(i!=j for i,j in enumerate(aliases)))

def compact(payload,expected_problem_sha256,max_work=2000000,max_bytes=10000000):
    before=time.perf_counter();original=check(payload,max_work=max_work,max_bytes=max_bytes,expected_problem_sha256=expected_problem_sha256)
    if original['status']!='accepted':return dict(status=original['status'],input_check=original,seconds=time.perf_counter()-before)
    request=json.loads(payload);out=copy.deepcopy(request);graphs=[]
    for block in out['blocks']:
        block['proof'],graph=compact_lines(block['proof']);graphs.append(dict(name=block['name'],**graph))
    out['proof'],graph=compact_lines(out['proof']);graphs.append(dict(name='root',**graph))
    by_name={b['name']:b for b in out['blocks']};needed=set();pending=[l['name'] for l in out['proof'] if l['rule']=='block']
    while pending:
        name=pending.pop()
        if name in needed:continue
        needed.add(name);pending.extend(l['name'] for l in by_name[name]['proof'] if l['rule']=='block')
    removed=[b['name'] for b in out['blocks'] if b['name'] not in needed]
    out['blocks']=[b for b in out['blocks'] if b['name'] in needed]
    verified=check(canonical(out),max_work=max_work,max_bytes=max_bytes,expected_problem_sha256=expected_problem_sha256)
    if verified['status']!='accepted':return dict(status=verified['status'],input_check=original,output_check=verified,seconds=time.perf_counter()-before)
    return dict(status='accepted_compaction',request=out,graphs=graphs,removed_blocks=removed,
        input_check=original,output_check=verified,seconds=time.perf_counter()-before,
        method='exact earlier-formula reuse, dependency closure, reference renumbering and unreachable checked-block removal; all interfaces and eigenvariable contexts unchanged')
