"""Exact row/witness-to-request decoder; no search or inference oracle.

Independent symbolic validity and shared native acceptance remain separate.
All rows, repeated commands and ordered MP references are preserved.
"""
import copy
import hashlib
import json
import time


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('ascii')


def decode(graph, certificate, core):
    started = time.perf_counter()
    if (certificate['model_epoch'] != graph.model_epoch
            or certificate['source_bindings'] != graph.source_bindings
            or certificate['native_accepted'] is not False
            or certificate['native_authority_activated'] is not False
            or certificate['compiler_correspondence'] != 'open'):
        raise ValueError('wrong source model/authority label')
    placements = certificate['placements']
    if len(placements) != graph.height:
        raise ValueError('one primitive placement per declared row required')
    by_row = {}
    marking, totals = dict(graph.initial_marks), {}
    commands, provenance = [], []
    for placement in placements:
        pre = placement['identity_preimage']
        row = pre['transform'][1]
        core.integer(row)
        if not 0 <= row < graph.height or row in by_row or pre['transform'] != [0, row]:
            raise ValueError('duplicate/outside/rotated row')
        recipe_id = pre['prototype_preimage']['recipe_id']
        recipe = graph.recipe_index[recipe_id]
        refs = tuple(pre['ordered_input_rows'])
        key = core.Key(recipe, row, refs)
        expected = graph.decorate(key)
        if placement != expected:
            raise ValueError('source complete decorated placement/command/key differs')
        if any(type(ref) is not int or not 0 <= ref < row for ref in refs):
            raise ValueError('strict-prior ordered references required')
        by_row[row] = (key, placement)
        for x, y, value in expected['t']:
            totals[x, y] = totals.get((x, y), 0) + value
        for x, y, value in expected['m']:
            if (x, y) in marking and marking[x, y] != value:
                raise ValueError('reconstructed marking disagreement')
            marking[x, y] = value
    if totals != {(0, row): 1 for row in range(graph.height)} or marking != graph.marks:
        raise ValueError('full point certificate union differs')
    for row in range(graph.height):
        key, placement = by_row[row]
        recipe = graph.recipes[key.recipe]
        command = copy.deepcopy(recipe.witness)
        if recipe.inputs:
            if command['rule'] != 'mp' or len(key.refs) != 2:
                raise ValueError('only ordered literal MP has primitive ports')
            command.update(antecedent=key.refs[0], implication=key.refs[1])
            if [commands[i]['formula'] for i in key.refs] != recipe.formulas:
                raise ValueError('prior row formulas differ from exact ordered interface')
        if command != placement['identity_preimage']['primitive_command']:
            raise ValueError('native command fields differ from full point identity')
        commands.append(command)
        provenance.append({'row': row, 'key': key.data(), 'placement_id': placement['id'],
                           'recipe_id': recipe.identifier, 'ordered_refs': list(key.refs),
                           'command_sha256': hashlib.sha256(canonical(command)).hexdigest()})
    # The target comes solely from the original immutable point boundary.
    target_code = graph.initial_marks[1, graph.height - 1]
    target = copy.deepcopy(graph.formulas[target_code])
    if commands[-1]['formula'] != target:
        raise ValueError('last logical row differs from fixed original target')
    theory = copy.deepcopy(graph.context['theory'])
    premises = copy.deepcopy(graph.context['ordered_local_premises'])
    local_certificate = {'theory': copy.deepcopy(theory), 'ordered_local_premises': premises,
                         'proof': copy.deepcopy(commands), 'target': target}
    hypotheses = []
    for index, formula in enumerate(premises):
        name = 'hypothesis-' + str(index)
        if name in theory['axioms']:
            raise ValueError('hypothesis axiom name collision')
        theory['axioms'][name] = copy.deepcopy(formula)
        hypotheses.append({'index': index, 'name': name, 'formula': copy.deepcopy(formula)})
    native_proof = copy.deepcopy(commands)
    for command in native_proof:
        if command['rule'] == 'assumption':
            index = command['index']; core.integer(index)
            if not 0 <= index < len(premises) or command['formula'] != premises[index]:
                raise ValueError('assumption is not an exact retained hypothesis')
            command.clear()
            command.update(rule='axiom', name=hypotheses[index]['name'], formula=copy.deepcopy(premises[index]))
    request = {'protocol': 'gcts-fol-1', 'theory': theory, 'blocks': [],
               'proof': native_proof, 'target': target}
    payload = canonical(request)
    problem = {key: request[key] for key in ('protocol', 'theory', 'target')}
    return {'status': 'decoded_exact_primitive_ground_certificate_pending_independent_symbolic_check',
            'model_epoch': graph.model_epoch, 'point_certificate': certificate,
            'local_certificate': local_certificate, 'flat_request': request,
            'request_ascii': payload.decode('ascii'), 'request_bytes': len(payload),
            'request_sha256': hashlib.sha256(payload).hexdigest(),
            'problem_sha256': hashlib.sha256(canonical(problem)).hexdigest(),
            'rows': graph.height, 'provenance': provenance, 'retained_hypotheses': hypotheses,
            'native_queries': 0, 'native_accepted': False,
            'decoder_seconds': time.perf_counter() - started,
            'logical_scope': 'Original ground sequent relative to all ordered hypotheses; no discharge, universal closure or proof-command removal.'}
