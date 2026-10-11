"""Generic bijective renaming of internal lemma declarations, not formulas."""
import copy


def shorten(request):
    result = copy.deepcopy(request)
    old = [block['name'] for block in result['blocks']]
    if len(old) != len(set(old)):
        raise ValueError('distinct block declaration identities required')
    names = {name: 'b' + str(index) for index, name in enumerate(old)}
    for block in result['blocks']:
        block['name'] = names[block['name']]
    for proof in [block['proof'] for block in result['blocks']] + [result['proof']]:
        for command in proof:
            if command['rule'] == 'block':
                if command['name'] not in names:
                    raise ValueError('undeclared block reference')
                command['name'] = names[command['name']]
    return result, [{'old': name, 'new': names[name]} for name in old]
