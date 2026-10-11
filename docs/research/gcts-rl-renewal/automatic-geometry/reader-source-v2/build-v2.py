from pathlib import Path
root = Path('.gcts-active/automatic-geometry-reader-source-v2-20261011')
old = Path('.gcts-active/automatic-geometry-reader-source-20261011/viewer.js').read_text()
old = old.replace("const marks = p.m.filter(q => q[0] === 2 + index && q[1] === ref);\n        need(marks.length === 1 && Number.isSafeInteger(marks[0][2])\n          && same(data.formula_codes[marks[0][2]], recipe.ordered_premise_formulas[index]), 'Extended source marking does not encode its ordered premise');", "const source = p.m.filter(q => q[0] === 1 && q[1] === ref);\n        need(source.length === 1 && Number.isSafeInteger(source[0][2])\n          && same(data.formula_codes[source[0][2]], recipe.ordered_premise_formulas[index]), 'Blue source constraint does not encode its ordered premise');\n        const offsets = p.m.filter(q => q[0] === 2 + index && q[1] === row);\n        need(offsets.length === 1 && offsets[0][2] === ref - row, 'Purple ordered offset disagrees with source row');")
insert = r'''
  function snapshotRows(data, state) {
    const graph = state && state.projection && state.projection.graph;
    if (!graph) return null;
    need(Array.isArray(graph.order) && graph.order.length <= 24, 'Snapshot has at most 24 actual selected placements');
    need(Array.isArray(graph.marks) && Array.isArray(graph.totals), 'Exact snapshot marking and total arrays required');
    const marks = new Map();
    for (const q of graph.marks) {
      need(Array.isArray(q) && q.length === 4, 'Snapshot marks require [x,y,value,refcount]');
      q.forEach((value, index) => integer(value, 'Snapshot mark field ' + index));
      need(q[3] > 0, 'Assigned snapshot marks have positive reference counts');
      const point = q[0] + ',' + q[1]; need(!marks.has(point), 'Duplicate snapshot mark point'); marks.set(point, q);
    }
    const totals = new Map();
    if (graph.totals.every(value => typeof value === 'number')) {
      need(graph.totals.length <= 24, 'Row-indexed total array has at most 24 rows');
      graph.totals.forEach((value, row) => { integer(value, 'Snapshot occupancy'); need(value === 0 || value === 1, 'Exact scalar row occupancy required'); totals.set('0,' + row, [0, row, value]); });
    } else {
      pointTriples(graph.totals, 'Snapshot totals');
      graph.totals.forEach(q => { need(q[2] >= 0 && q[2] <= 1, 'Partial snapshot total lies in [0,1]'); totals.set(q[0] + ',' + q[1], q); });
    }
    const selected = new Map();
    const rows = graph.order.map((key, insertion) => {
      need(Array.isArray(key) && key.length === 3 && Array.isArray(key[2]), 'Snapshot exact recipe/row/ordered-source key required');
      const index = integer(key[0], 'Snapshot recipe index'), row = integer(key[1], 'Snapshot row');
      need(row >= 0 && row < 24 && !selected.has(row), 'Distinct snapshot row must be within the 24-row boundary');
      const recipe = data.recipes[index];
      need(recipe && recipe.primitive_witness && recipe.primitive_witness.formula
        && Array.isArray(recipe.ordered_premise_formulas), 'Snapshot recipe output and ordered premises required');
      need(key[2].length === recipe.ordered_premise_formulas.length, 'Snapshot key lists every ordered premise');
      const total = totals.get('0,' + row); need(total && total[2] === 1, 'Selected snapshot row must have exact occupancy one');
      const output = marks.get('1,' + row); need(output, 'Selected snapshot output has an assigned formula marking');
      const code = output[2]; need(code >= 0 && code < data.formula_codes.length, 'Snapshot output formula code in registry');
      const formula = data.formula_codes[code]; formulaLatex(formula);
      need(same(formula, recipe.primitive_witness.formula), 'Snapshot blue output formula must equal saved recipe output');
      const refs = key[2].map((ref, input) => {
        integer(ref, 'Snapshot strict-prior numeric source'); need(ref >= 0 && ref < row, 'Snapshot input source must have an earlier numeric row');
        const source = marks.get('1,' + ref), offset = marks.get((2 + input) + ',' + row);
        need(source && source[2] >= 0 && source[2] < data.formula_codes.length, 'Snapshot source requires its assigned blue formula constraint');
        need(same(data.formula_codes[source[2]], recipe.ordered_premise_formulas[input]), 'Snapshot source formula disagrees with ordered recipe premise');
        need(offset && offset[2] === ref - row, 'Snapshot purple offset disagrees with ordered source');
        return {row: ref, input, code: source[2], formula: data.formula_codes[source[2]], offset: ref - row, source_mark: source, offset_mark: offset};
      });
      const entry = {row, insertion, key, recipe, outputCode: code, formula, output_mark: output, refs, total};
      selected.set(row, entry); return entry;
    }).sort((a, b) => a.row - b.row);
    // Selected insertion order is not proof order. A prior numeric source may be unoccupied.
    rows.forEach(entry => entry.refs.forEach(ref => { ref.selected = selected.has(ref.row); ref.occupied = !!(totals.get('0,' + ref.row) && totals.get('0,' + ref.row)[2] === 1); }));
    for (const q of graph.marks) if (q[0] === 1) {
      need(q[2] >= 0 && q[2] < data.formula_codes.length, 'Every blue snapshot constraint uses an exact formula code'); formulaLatex(data.formula_codes[q[2]]);
    }
    return {graph, rows, selected, marks: graph.marks, totals: Array.from(totals.values())};
  }
  function deepestSelection(observation) {
    const choices = [];
    if (observation.initial_state) choices.push(['initial', observation.initial_state]);
    (Array.isArray(observation.events) ? observation.events : []).forEach((event, index) => choices.push([String(index), event.state]));
    if (observation.terminal_state) choices.push(['terminal', observation.terminal_state]);
    let best = choices.length ? choices[0][0] : '', depth = -1;
    for (const [value, state] of choices) {
      const order = state && state.projection && state.projection.graph && state.projection.graph.order;
      const length = Array.isArray(order) ? order.length : -1;
      if (length > depth) { best = value; depth = length; }
    }
    return best; // Maximum saved selection length; first tie in initial/event/terminal order.
  }
  function snapshotTile(entry, formulaLayer, referenceLayer) {
    const wrap = node('div', undefined, 'gcts-tile-panel'), square = node('div', undefined, 'gcts-literal-square');
    square.setAttribute('aria-label', 'Actual partial-state square at numeric row ' + (entry.row + 1));
    paragraph(square, 'Selected square ' + (entry.row + 1), 'gcts-tile-title');
    const occupancy = node('div', undefined, 'gcts-occupancy'); math(occupancy, 'T(0,' + entry.row + ')=' + entry.total[2]); square.append(occupancy);
    const output = node('div', undefined, 'gcts-output-layer'); paragraph(output, 'Blue assigned output'); math(output, 'm(1,' + entry.row + ')=' + entry.outputCode);
    output.hidden = !formulaLayer; square.append(output);
    const refs = node('div', undefined, 'gcts-reference-layer'); paragraph(refs, 'Purple ordered offsets');
    math(refs, '\\left(' + entry.refs.map(ref => ref.offset).join(',') + '\\right)');
    entry.refs.forEach(ref => math(refs, 'm(' + (2 + ref.input) + ',' + entry.row + ')=' + ref.offset));
    refs.hidden = !referenceLayer; square.append(refs); wrap.append(square);
    const literal = node('details'); literal.append(node('summary', 'Exact saved placement key and snapshot marks'));
    code(literal, {key: entry.key, insertion_index: entry.insertion, snapshot_total: entry.total, output_mark: entry.output_mark,
      ordered_source_marks: entry.refs.map(ref => ref.source_mark), ordered_offset_marks: entry.refs.map(ref => ref.offset_mark)}); wrap.append(literal); return wrap;
  }
  function renderSnapshot(data, state, target, formulaLayer, referenceLayer) {
    const snapshot = snapshotRows(data, state); if (!snapshot) return;
    paragraph(target, 'Partial search state: ' + snapshot.rows.length + ' selected squares. These are saved placements, not a proof or certificate.', 'gcts-pending');
    paragraph(target, 'Squares below are sorted by numeric row for reading. The saved insertion order remains inspectable. Every orientation is fixed; placements use translation only. An earlier numeric source can still be empty, with a pending formula receptor.');
    for (const entry of snapshot.rows) {
      const card = node('article', undefined, 'gcts-proof-row'); card.append(snapshotTile(entry, formulaLayer, referenceLayer));
      const words = node('div'); words.append(node('h3', 'Selected row ' + (entry.row + 1)));
      const out = node('p'); math(out, formulaLatex(entry.formula)); out.hidden = !formulaLayer; words.append(out);
      const english = paragraph(words, formulaEnglish(entry.formula)); english.hidden = !formulaLayer;
      paragraph(words, 'Saved recipe: ' + String(entry.recipe.id) + '. This is the recorded output constraint; no proof command is reconstructed.');
      entry.refs.forEach(ref => {
        const p = node('p', 'Ordered input ' + (ref.input + 1) + ': row ' + (ref.row + 1) + (ref.selected ? ' — selected source square. ' : ' — pending source receptor (not selected). '));
        math(p, formulaLatex(ref.formula)); p.hidden = !referenceLayer; words.append(p);
        const explanation = paragraph(words, formulaEnglish(ref.formula)); explanation.hidden = !referenceLayer;
      });
      const recipe = node('details'); recipe.append(node('summary', 'Exact saved recipe and primitive witness'));
      code(recipe, {id: entry.recipe.id, primitive_witness: entry.recipe.primitive_witness, ordered_premise_formulas: entry.recipe.ordered_premise_formulas}); words.append(recipe);
      card.append(words); target.append(card);
    }
    paragraph(target, 'All assigned snapshot marking points, including constraints on unoccupied rows');
    const all = node('div', undefined, 'gcts-snapshot-marks');
    for (const q of snapshot.marks) {
      const color = q[0] === 1 ? 'gcts-output-layer' : q[0] >= 2 ? 'gcts-reference-layer' : 'gcts-other-mark';
      const mark = node('div', undefined, color); math(mark, 'm(' + q[0] + ',' + q[1] + ')=' + q[2]);
      paragraph(mark, 'Saved reference count: ' + q[3]);
      if (q[0] === 1) {
        paragraph(mark, snapshot.selected.has(q[1]) ? 'Selected output constraint' : 'Pending output receptor; no selected square at this row');
        math(mark, formulaLatex(data.formula_codes[q[2]])); paragraph(mark, formulaEnglish(data.formula_codes[q[2]]));
        mark.hidden = !formulaLayer;
      } else if (q[0] >= 2) { paragraph(mark, 'Saved ordered reference-offset marking'); mark.hidden = !referenceLayer; }
      all.append(mark);
    }
    target.append(all);
    const occupancy = node('details'); occupancy.append(node('summary', 'Every saved occupancy total, including empty rows'));
    snapshot.totals.forEach(q => { const p = node('p'); math(p, 'T(' + q[0] + ',' + q[1] + ')=' + q[2]); occupancy.append(p); }); target.append(occupancy);
  }
'''
old = old.replace('  function showTrace(observation, selected, target) {', insert + '\n  function showTrace(data, observation, selected, target, formulaLayer, referenceLayer) {\n    if (global.MathJax && typeof global.MathJax.typesetClear === \'function\') global.MathJax.typesetClear([target]);')
old = old.replace("      if (graph) {\n        const declared = {};", "      if (graph) {\n        renderSnapshot(data, state, target, formulaLayer, referenceLayer);\n        const declared = {};")
old = old.replace("code(full, event || state); target.append(full);\n  }", "code(full, event || state); target.append(full);\n    return typeset([target]);\n  }")
old = old.replace("    function render() {", "    let renderedObservation = null;\n    function render() {")
start = old.index("      const selector = elements['trace-event'], events = ")
end = old.index("    const guarded =", start)
old = old[:start] + r'''      const selector = elements['trace-event'], events = Array.isArray(observation.events) ? observation.events : [];
      if (renderedObservation !== observation) {
        selector.replaceChildren();
        if (observation.initial_state) { const option = node('option', 'Initial state'); option.value = 'initial'; selector.append(option); }
        events.forEach((event, index) => { const option = node('option', 'Event ' + (index + 1) + (event.kind ? ' — ' + event.kind : '')); option.value = String(index); selector.append(option); });
        if (observation.terminal_state) { const option = node('option', 'Terminal state'); option.value = 'terminal'; selector.append(option); }
        selector.disabled = !selector.options.length; selector.value = deepestSelection(observation);
        renderedObservation = observation;
      }
      const drawTrace = () => Promise.resolve().then(() => showTrace(data, observation, selector.value, trace, elements['formula-layer'].checked, elements['reference-layer'].checked)).catch(error => {
        trace.replaceChildren(node('p', error.message, 'gcts-error'));
      });
      selector.onchange = drawTrace;
      return Promise.all([typeset([proof]), drawTrace()]);
    }
''' + old[end:]
old = old.replace('certificateRows, ruleEnglish, accepted}', 'certificateRows, ruleEnglish, accepted, snapshotRows, deepestSelection}')
old = old.replace('#reader .gcts-tile-panel details{', '#reader .gcts-snapshot-marks{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:8px}#reader .gcts-snapshot-marks>div{padding:8px;overflow:auto}#reader .gcts-tile-panel details{')
# The inserted block is raw Python text; JS strings need exactly two literal backslashes.
old = old.replace("'\\\\left('", "'\\\\left('")
(root / 'viewer.js').write_text(old)
