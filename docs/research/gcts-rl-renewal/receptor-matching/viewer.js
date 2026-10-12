(function (global) {
  'use strict';

  const IDs = ['observation', 'trace-event', 'proof-view', 'trace-view', 'formula-layer', 'reference-layer', 'reader'];
  const same = (a, b) => canonical(a) === canonical(b);
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
    return JSON.stringify(value);
  }
  function need(condition, message) { if (!condition) throw new Error(message); }
  function integer(value, label) { need(Number.isSafeInteger(value), label + ' must be an exact safe integer'); return value; }
  function escapeTex(value) {
    need(typeof value === 'string', 'Mathematical identifier must be a string');
    return value.replace(/[\\{}_$&#%~^]/g, ch => ({'\\': '\\backslash{}', '{': '\\{', '}': '\\}', '_': '\\_', '$': '\\$', '&': '\\&', '#': '\\#', '%': '\\%', '~': '\\textasciitilde{}', '^': '\\textasciicircum{}'})[ch]);
  }
  function shape(ast, length, tag) { need(Array.isArray(ast) && ast.length === length && ast[0] === tag, 'Malformed ' + tag + ' AST'); }
  function termLatex(ast) {
    need(Array.isArray(ast) && ast.length, 'Term AST required');
    if (ast[0] === 'var') { shape(ast, 2, 'var'); return '\\mathit{' + escapeTex(ast[1]) + '}'; }
    if (ast[0] === 'fun') {
      shape(ast, 3, 'fun'); need(Array.isArray(ast[2]), 'Function arguments must be an AST array');
      const name = '\\operatorname{' + escapeTex(ast[1]) + '}';
      return name + (ast[2].length ? '\\left(' + ast[2].map(termLatex).join(',') + '\\right)' : '');
    }
    throw new Error('Unknown term AST tag ' + String(ast[0]));
  }
  function formulaLatex(ast) {
    need(Array.isArray(ast) && ast.length, 'Formula AST required');
    const tag = ast[0];
    if (tag === 'pred') {
      shape(ast, 3, tag); need(Array.isArray(ast[2]), 'Predicate arguments must be an AST array');
      return '\\operatorname{' + escapeTex(ast[1]) + '}' + (ast[2].length ? '\\left(' + ast[2].map(termLatex).join(',') + '\\right)' : '');
    }
    if (tag === 'eq') { shape(ast, 3, tag); return termLatex(ast[1]) + '=' + termLatex(ast[2]); }
    if (tag === 'not') { shape(ast, 2, tag); return '\\neg\\left(' + formulaLatex(ast[1]) + '\\right)'; }
    if (tag === 'all') { shape(ast, 3, tag); return '\\forall ' + '\\mathit{' + escapeTex(ast[1]) + '}\\;\\left(' + formulaLatex(ast[2]) + '\\right)'; }
    if (tag === 'and' || tag === 'imp') {
      shape(ast, 3, tag);
      return '\\left(' + formulaLatex(ast[1]) + (tag === 'and' ? '\\land ' : '\\Rightarrow ') + formulaLatex(ast[2]) + '\\right)';
    }
    if (tag === 'bot') { shape(ast, 1, tag); return '\\bot'; }
    throw new Error('Unknown formula AST tag ' + String(tag));
  }
  function englishMath(value, command) {
    return '\\(\\' + command + '{' + escapeTex(value) + '}\\)';
  }
  function termEnglish(ast) {
    termLatex(ast); // Same fail-closed grammar, no ad-hoc word interpretation.
    if (ast[0] === 'var') return 'the object ' + englishMath(ast[1], 'mathit');
    return ast[2].length ? 'the value of ' + englishMath(ast[1], 'operatorname') + ' on ' + ast[2].map(termEnglish).join(', ') : 'the constant ' + englishMath(ast[1], 'operatorname');
  }
  function formulaEnglish(ast) {
    formulaLatex(ast);
    switch (ast[0]) {
      case 'pred': return 'The predicate ' + englishMath(ast[1], 'operatorname') + ' holds' + (ast[2].length ? ' for ' + ast[2].map(termEnglish).join(', ') : '');
      case 'eq': return termEnglish(ast[1]) + ' equals ' + termEnglish(ast[2]);
      case 'not': return 'It is not the case that (' + formulaEnglish(ast[1]) + ')';
      case 'all': return 'For every choice of object ' + englishMath(ast[1], 'mathit') + ', ' + formulaEnglish(ast[2]);
      case 'and': return '(' + formulaEnglish(ast[1]) + ') and (' + formulaEnglish(ast[2]) + ')';
      case 'imp': return 'If ' + formulaEnglish(ast[1]) + ', then ' + formulaEnglish(ast[2]);
      case 'bot': return 'A contradiction';
      default: throw new Error('Unknown formula AST tag');
    }
  }
  function pointTriples(values, label) {
    need(Array.isArray(values), label + ' array required');
    const seen = new Set();
    for (const point of values) {
      need(Array.isArray(point) && point.length === 3, label + ' requires exact [x,y,value] triples');
      integer(point[0], label + ' x'); integer(point[1], label + ' y');
      need(typeof point[2] === 'number' && Number.isFinite(point[2]), label + ' finite value required');
      const key = point[0] + ',' + point[1]; need(!seen.has(key), 'Duplicate ' + label + ' point ' + key); seen.add(key);
    }
  }
  function certificateRows(data, observation) {
    if (observation.point_certificate == null) return null;
    const placements = observation.point_certificate.placements;
    need(Array.isArray(placements) && placements.length > 0, 'Nonempty certificate placements array required');
    const rows = placements.map(p => ({placement: p, row: integer(p.key && p.key[1], 'Placement row')})).sort((a, b) => a.row - b.row);
    const rowMap = new Map();
    for (const entry of rows) {
      const p = entry.placement, row = entry.row, pre = p.identity_preimage, proto = pre && pre.prototype_preimage;
      need(row >= 0 && !rowMap.has(row), 'Repeated or negative proof row');
      need(Array.isArray(p.key) && p.key.length === 3 && Array.isArray(p.key[2]), 'Exact recipe/row/source key required');
      const recipeIndex = integer(p.key[0], 'Recipe index'), recipe = data.recipes[recipeIndex];
      need(recipe && proto && pre, 'Recipe and full decorated provenance required');
      need(recipe.primitive_witness !== undefined && Array.isArray(recipe.ordered_premise_formulas), 'Complete recipe witness and ordered premises required');
      need(recipe.id === proto.recipe_id && same(recipe.primitive_witness, proto.primitive_witness)
        && same(recipe.ordered_premise_formulas, proto.ordered_premise_formulas), 'Recipe prototype correspondence');
      need(proto.orientation === 'identity' && same(pre.transform, [0, row]), 'Translation-only identity orientation required');
      need(same(p.key[2], pre.ordered_input_rows), 'Ordered input rows disagree with key');
      need(same(p.command, pre.primitive_command) && same(p.t, pre.t) && same(p.m, pre.m), 'Absolute command/t/m provenance disagreement');
      need(Array.isArray(pre.ordered_input_rows) && pre.ordered_input_rows.length === recipe.ordered_premise_formulas.length,
        'Every ordered premise requires its saved source row');
      const refs = pre.ordered_input_rows;
      refs.forEach(ref => { integer(ref, 'Strict-prior source row'); need(ref >= 0 && ref < row, 'Input must strictly precede current row'); });
      need(same(proto.relative_ordered_input_offsets, refs.map(ref => ref - row)), 'Relative ordered negative offsets disagree');
      pointTriples(p.t, 't'); pointTriples(p.m, 'm');
      need(Array.isArray(proto.t) && Array.isArray(proto.m)
        && same(p.t, proto.t.map(q => [q[0], q[1] + row, q[2]]))
        && same(p.m, proto.m.map(q => [q[0], q[1] + row, q[2]])), 'Exact translated t/m supports required');
      const output = p.m.filter(q => q[0] === 1 && q[1] === row);
      need(output.length === 1, 'Exactly one output marking at (1,row) required');
      const code = integer(output[0][2], 'Output formula code');
      need(code >= 0 && code < data.formula_codes.length && same(data.formula_codes[code], p.command.formula), 'Output formula-code/command mismatch');
      formulaLatex(p.command.formula);
      refs.forEach((ref, index) => {
        need(rowMap.has(ref) && same(rowMap.get(ref).placement.command.formula, recipe.ordered_premise_formulas[index]), 'Ordered premise disagrees with prior output');
        const source = p.m.filter(q => q[0] === 1 && q[1] === ref);
        need(source.length === 1 && Number.isSafeInteger(source[0][2])
          && same(data.formula_codes[source[0][2]], recipe.ordered_premise_formulas[index]), 'Blue source constraint does not encode its ordered premise');
        const offsets = p.m.filter(q => q[0] === 2 + index && q[1] === row);
        need(offsets.length === 1 && offsets[0][2] === ref - row, 'Purple ordered offset disagrees with source row');
      });
      entry.recipe = recipe; entry.refs = refs; entry.offsets = proto.relative_ordered_input_offsets; entry.outputCode = code;
      rowMap.set(row, entry);
    }
    rows.forEach((entry, index) => need(entry.row === index, 'Complete certificate rows must start at zero without gaps'));
    need(same(rows[rows.length - 1].placement.command.formula, data.target), 'Last displayed output must equal the root target');
    return rows;
  }
  function ruleEnglish(command, refs, recipe) {
    const cited = refs.map(n => 'row ' + (n + 1)).join(', ');
    const rule = command.rule;
    if (rule === 'axiom') return 'Use the declared hypothesis or axiom' + (command.name === undefined ? '.' : ' ' + englishMath(String(command.name), 'text') + '.');
    if (rule === 'refl') return 'Assert reflexive equality by the saved reflexivity rule.';
    if (rule === 'mp') return 'Apply modus ponens using ' + cited + ': the antecedent and the implication yield this conclusion.';
    if (rule === 'generalize') return 'Universally generalize ' + cited + ' over ' + englishMath(String(command.variable), 'mathit') + '; freshness and assumption conditions belong to the independent checker.';
    if (rule === 'block') return 'Apply the declared recipe ' + englishMath(String(command.name), 'text') + (refs.length ? ' to ' + cited + ' in that order.' : ', with no input rows.');
    if (rule === 'tautology') return 'Use the saved propositional tautology command.';
    return 'Use the saved primitive rule ' + englishMath(String(rule), 'text') + (refs.length ? ' with ' + cited + ' in the displayed order.' : ', with no prior input rows.') + ' Its exact command is shown below.';
  }
  function accepted(data, observation) {
    return observation.independent_certificate_accepted === true;
  }
  function node(tag, content, className) {
    const n = document.createElement(tag); if (content !== undefined) n.textContent = String(content);
    if (className) n.className = className; return n;
  }
  function math(parent, latex, display) { parent.append(node('span', (display ? '\\[' : '\\(') + latex + (display ? '\\]' : '\\)'), 'gcts-math')); }
  function code(parent, value) { parent.append(node('pre', JSON.stringify(value, null, 2), 'gcts-exact-json')); }
  function paragraph(parent, value, cls) { const n = node('p', value, cls); parent.append(n); return n; }
  function tile(entry, formulaLayer, referenceLayer) {
    const p = entry.placement, wrap = node('div', undefined, 'gcts-tile-panel');
    const square = node('div', undefined, 'gcts-literal-square');
    square.setAttribute('aria-label', 'Translation-only tile at proof row ' + (entry.row + 1));
    paragraph(square, 'Square tile ' + (entry.row + 1), 'gcts-tile-title');
    const occupancy = node('div', undefined, 'gcts-occupancy');
    math(occupancy, 't: ' + p.t.map(q => '(' + q[0] + ',' + q[1] + ')\\mapsto ' + q[2]).join(',\\;'));
    square.append(occupancy);
    const output = node('div', undefined, 'gcts-output-layer');
    paragraph(output, 'Blue output marking'); math(output, 'm(1,' + entry.row + ')=' + entry.outputCode);
    output.hidden = !formulaLayer; square.append(output);
    const sources = node('div', undefined, 'gcts-reference-layer');
    paragraph(sources, 'Purple ordered reference offsets'); math(sources, '\\left(' + entry.offsets.join(',') + '\\right)');
    p.m.filter(q => q[0] >= 2).forEach(q => math(sources, 'm(' + q[0] + ',' + q[1] + ')=' + q[2]));
    sources.hidden = !referenceLayer; square.append(sources); wrap.append(square);
    const details = node('details'); details.append(node('summary', 'All literal point values and identity'));
    code(details, {id: p.id, key: p.key, orientation: 'identity', transform: p.identity_preimage.transform, t: p.t, m: p.m});
    wrap.append(details); return wrap;
  }
  function typeset(targets) {
    if (global.MathJax && typeof global.MathJax.typesetPromise === 'function') {
      const ready = global.MathJax.startup && global.MathJax.startup.promise || Promise.resolve();
      return ready.then(() => global.MathJax.typesetPromise(targets)).catch(error => { throw new Error('MathJax typesetting failed: ' + error.message); });
    }
    return Promise.resolve(); // Root supplies the established renderer.
  }
  function installStyle() {
    if (document.getElementById('gcts-geometry-reader-style')) return;
    const style = node('style', '#reader .gcts-proof-row{display:grid;grid-template-columns:210px minmax(0,1fr);gap:18px;margin:18px 0;padding:14px;border:1px solid #c9d1dd;border-radius:8px}#reader .gcts-literal-square{box-sizing:border-box;width:190px;height:190px;border:2px solid #263448;padding:8px;display:flex;flex-direction:column;justify-content:space-between;overflow:auto;background:white}#reader .gcts-literal-square p{margin:2px 0;font-size:11px}#reader .gcts-literal-square .gcts-math{font-size:12px}#reader .gcts-output-layer{border-left:4px solid #2463b8;background:#eaf2ff;padding:4px}#reader .gcts-reference-layer{border-left:4px solid #8651bd;background:#f3eafb;padding:4px}#reader .gcts-exact-json{white-space:pre-wrap;overflow-wrap:anywhere;max-height:24rem;overflow:auto;font-size:12px}#reader .gcts-pending{border-left:4px solid #b57600;padding:8px;background:#fff6df}#reader .gcts-error{color:#991b1b;border:1px solid #991b1b;padding:10px}#reader .gcts-math{overflow-wrap:anywhere}#reader .gcts-snapshot-marks{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:8px}#reader .gcts-snapshot-marks>div{padding:8px;overflow:auto}#reader .gcts-tile-panel details{font-size:12px;margin-top:7px}@media(max-width:640px){#reader .gcts-proof-row{grid-template-columns:1fr}#reader .gcts-literal-square{width:190px;height:190px}}');
    style.id = 'gcts-geometry-reader-style'; document.head.append(style);
  }

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
      if (q[1] < 0) {
        need(q[2] === -1, 'Exterior blue boundary mark must be the exact exclusion sentinel -1');
      } else {
        need(q[2] >= 0 && q[2] < data.formula_codes.length, 'Every interior blue snapshot constraint uses an exact formula code'); formulaLatex(data.formula_codes[q[2]]);
      }
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
      math(mark, '\\operatorname{refcount}(' + q[0] + ',' + q[1] + ')=' + q[3]);
      if (q[0] === 1) {
        if (q[1] < 0) {
          paragraph(mark, 'Exterior boundary exclusion sentinel');
          // This literal assigned mark is not a formula code. Keep every exterior point visible.
        } else {
          paragraph(mark, snapshot.selected.has(q[1]) ? 'Selected output constraint' : 'Pending output receptor; no selected square at this row');
          math(mark, formulaLatex(data.formula_codes[q[2]])); paragraph(mark, formulaEnglish(data.formula_codes[q[2]]));
          mark.hidden = !formulaLayer;
        }
      } else if (q[0] >= 2) { paragraph(mark, 'Saved ordered reference-offset marking'); mark.hidden = !referenceLayer; }
      all.append(mark);
    }
    target.append(all);
    const occupancy = node('details'); occupancy.append(node('summary', 'Every saved occupancy total, including empty rows'));
    snapshot.totals.forEach(q => { const p = node('p'); math(p, 'T(' + q[0] + ',' + q[1] + ')=' + q[2]); occupancy.append(p); }); target.append(occupancy);
  }

  function showTrace(data, observation, selected, target, formulaLayer, referenceLayer) {
    if (global.MathJax && typeof global.MathJax.typesetClear === 'function') global.MathJax.typesetClear([target]);
    target.replaceChildren();
    const events = Array.isArray(observation.events) ? observation.events : [];
    let event = null, state, title;
    if (selected === 'initial') { state = observation.initial_state; title = 'Saved initial state'; }
    else if (selected === 'terminal') { state = observation.terminal_state; title = 'Saved terminal state'; }
    else {
      const index = Number(selected);
      event = events[index];
      if (!event) { paragraph(target, 'No saved trace event is supplied for this observation.'); return; }
      state = event.state; title = 'Saved trace event ' + (index + 1) + ' of ' + events.length;
    }
    paragraph(target, title + '. This is a search-state projection, not a proof.');
    paragraph(target, observation.independent_trace_accepted === true ? 'Root flags this trace as independently accepted.' : 'Independent trace acceptance is pending.');
    if (state && state.projection) {
      const projection = state.projection, graph = projection.graph;
      paragraph(target, 'Exact saved state digest: ' + String(state.full_semantic_sha256));
      if (graph) {
        renderSnapshot(data, state, target, formulaLayer, referenceLayer);
        const declared = {};
        for (const key of ['order', 'totals', 'marks', 'selected_generations', 'roots', 'excluded', 'domains']) {
          if (Object.prototype.hasOwnProperty.call(graph, key)) declared[key] = graph[key];
        }
        code(target, declared);
      } else paragraph(target, 'This event has no graph projection.');
      if (Object.prototype.hasOwnProperty.call(projection, 'hint_states')) { paragraph(target, 'Saved hint states'); code(target, projection.hint_states); }
    } else paragraph(target, 'This event has no saved state projection.');
    if (event) {
      const decision = {};
      for (const key of Object.keys(event)) if (key !== 'state') decision[key] = event[key];
      paragraph(target, 'Saved decision/event fields'); code(target, decision);
    }
    const full = node('details'); full.append(node('summary', event ? 'Complete saved event (all fields)' : 'Complete saved state (all fields)')); code(full, event || state); target.append(full);
    return typeset([target]);
  }
  function mount(data) {
    need(data && Array.isArray(data.formula_codes) && Array.isArray(data.recipes)
      && Array.isArray(data.hypotheses) && Array.isArray(data.observations), 'Root visual-data schema required');
    // Decode only displayed formulas; the full registry is not eagerly typeset.
    data.hypotheses.forEach(formulaLatex); formulaLatex(data.target);
    const elements = {};
    IDs.forEach(id => { elements[id] = document.getElementById(id); need(elements[id], 'Missing reader element #' + id); });
    need(elements.observation.tagName === 'SELECT' && elements['trace-event'].tagName === 'SELECT', 'Reader selectors must be SELECT elements');
    installStyle();
    elements.observation.replaceChildren();
    data.observations.forEach((o, index) => { const option = node('option', o.id + ' — ' + o.mode); option.value = String(index); elements.observation.append(option); });
    let renderedObservation = null;
    function render() {
      const observation = data.observations[Number(elements.observation.value) || 0];
      need(observation, 'No supplied observation');
      const proof = elements['proof-view'], trace = elements['trace-view'];
      if (global.MathJax && typeof global.MathJax.typesetClear === 'function') global.MathJax.typesetClear([proof]);
      proof.replaceChildren(); trace.replaceChildren();
      const supplied = value => value === undefined ? 'not supplied' : JSON.stringify(value);
      paragraph(proof, 'Observation ' + observation.id + ': ' + observation.status + '. Attempts: ' + supplied(observation.attempts) + '; saved seconds: ' + supplied(observation.seconds) + '.');
      if (data.scope) paragraph(proof, data.scope);
      if (observation.independent_scope) paragraph(proof, observation.independent_scope);
      const metrics = node('details'); metrics.append(node('summary', 'Exact saved node count, graph metrics and limits'));
      code(metrics, {node_count: observation.node_count, graph_metrics: observation.graph_metrics, limits: observation.limits}); proof.append(metrics);
      paragraph(proof, 'Hypotheses'); data.hypotheses.forEach(f => { const p = node('p'); math(p, formulaLatex(f)); proof.append(p); });
      paragraph(proof, 'Target'); const goal = node('p'); math(goal, formulaLatex(data.target)); proof.append(goal);
      const rows = certificateRows(data, observation);
      if (rows === null) {
        paragraph(proof, 'No point certificate was supplied. The recorded status and trace below do not establish a proof.', 'gcts-pending');
      } else {
        paragraph(proof, accepted(data, observation) ? 'Root supplied an explicit independent-acceptance flag for this certificate.' : 'Literal certificate supplied; independent acceptance is pending. These display checks do not replace the proof checker.', 'gcts-pending');
        paragraph(proof, 'Each square is one actual placement, ordered by saved row. All orientations are identity; tiles move by translation only. Blue marks carry the output formula code. Purple marks carry ordered references to earlier rows and their negative relative offsets.');
        for (const entry of rows) {
          const card = node('article', undefined, 'gcts-proof-row'); card.append(tile(entry, elements['formula-layer'].checked, elements['reference-layer'].checked));
          const words = node('div'); words.append(node('h3', 'Row ' + (entry.row + 1)));
          const f = node('p'); math(f, formulaLatex(entry.placement.command.formula)); words.append(f);
          paragraph(words, formulaEnglish(entry.placement.command.formula));
          paragraph(words, ruleEnglish(entry.placement.command, entry.refs, entry.recipe));
          if (entry.refs.length) {
            paragraph(words, 'Ordered receptor premises:'); entry.refs.forEach((ref, index) => {
              const p = node('p', 'Input ' + (index + 1) + ' from row ' + (ref + 1) + ': '); math(p, formulaLatex(entry.recipe.ordered_premise_formulas[index])); words.append(p);
            });
          }
          const commands = node('details'); commands.append(node('summary', 'Exact saved command and primitive recipe witness'));
          code(commands, {command: entry.placement.command, recipe_id: entry.recipe.id, primitive_witness: entry.recipe.primitive_witness}); words.append(commands);
          card.append(words); proof.append(card);
        }
        const local = observation.decoded_certificate && observation.decoded_certificate.local_certificate;
        if (local && Array.isArray(local.proof)) {
          const expansion = node('details'); expansion.append(node('summary', 'Exact decoded local certificate commands'));
          local.proof.forEach((command, index) => {
            const row = node('div'); paragraph(row, 'Primitive command ' + (index + 1));
            if (command.formula) math(row, formulaLatex(command.formula));
            code(row, command); expansion.append(row);
          });
          proof.append(expansion);
        }
      }
      const selector = elements['trace-event'], events = Array.isArray(observation.events) ? observation.events : [];
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
    const guarded = () => Promise.resolve().then(render).catch(error => {
      elements['proof-view'].replaceChildren(node('p', error.message, 'gcts-error'));
      elements['trace-view'].replaceChildren();
    });
    elements.observation.onchange = guarded;
    elements['formula-layer'].onchange = guarded; elements['reference-layer'].onchange = guarded;
    return guarded();
  }
  async function start(options) {
    const url = options && options.url || 'visual-data.json';
    const response = await fetch(url, {cache: 'no-store'});
    need(response.ok, 'Could not load root visual-data.json: HTTP ' + response.status);
    return mount(await response.json());
  }
  global.GCTSGeometryReader = Object.freeze({start, mount, formulaLatex, formulaEnglish, certificateRows, ruleEnglish, accepted, snapshotRows, deepestSelection});
  if (typeof document !== 'undefined' && !global.GCTS_GEOMETRY_READER_NO_AUTOSTART) {
    const automatic = () => {
      const reader = document.getElementById('reader');
      if (!reader) return;
      start({url: reader.dataset.visualUrl || 'visual-data.json'}).catch(error => {
        const destination = document.getElementById('proof-view') || reader;
        destination.replaceChildren(node('p', error.message, 'gcts-error'));
      });
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', automatic, {once: true});
    else automatic();
  }
})(typeof window === 'undefined' ? globalThis : window);
