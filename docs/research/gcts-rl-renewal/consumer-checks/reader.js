'use strict';
// Presentation of saved observations only; no search, checking, or policy runs.
const saved = JSON.parse(document.getElementById('saved-data').textContent);
const byId = id => document.getElementById(id);
function node(tag, text, klass) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (klass) el.className = klass;
  return el;
}
function math(text) { return '\\(' + text + '\\)'; }
function ast(a) {
  const head = a[0];
  if (head === 'var') return a[1];
  if (head === 'fun' || head === 'pred') {
    const name = a[1].length === 1 ? a[1] : '\\operatorname{' + a[1] + '}';
    return name + (a[2].length ? '(' + a[2].map(ast).join(',') + ')' : '');
  }
  if (head === 'eq') return ast(a[1]) + '=' + ast(a[2]);
  if (head === 'all') return '\\forall ' + a[1] + '\\,(' + ast(a[2]) + ')';
  if (head === 'and') return '(' + ast(a[1]) + '\\land ' + ast(a[2]) + ')';
  if (head === 'imp') return '(' + ast(a[1]) + '\\to ' + ast(a[2]) + ')';
  if (head === 'not') return '\\neg(' + ast(a[1]) + ')';
  throw new Error('Unsupported saved presentation AST: ' + head);
}
function typeset(elements) {
  if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.startup.promise.then(() => window.MathJax.typesetPromise(elements)).catch(err => { byId('render-status').textContent = err.message; });
  }
}
function render() {
  const c = saved.partial_case;
  const g = c.groups[Number(byId('cluster-picker').value)];
  byId('cluster-description').textContent = g.components.map(x => x.name).join(' then ') + '. ' + math(String(g.distinct_member_count)) + ' distinct placements, ' + math(String(g.component_member_occurrences)) + ' component occurrences, ' + math(String(g.shared_member_count)) + ' shared occurrences.';
  const grid = byId('cluster-grid'); grid.replaceChildren();
  ['Row', 'Occupancy', 'Formula', 'Ordered offsets'].forEach(x => grid.append(node('span', x)));
  const ts = new Map(g.aggregate_t.map(p => [p[1], p[2]]));
  const ms = new Map(g.aggregate_m.map(p => [p[0] + ':' + p[1], p[2]]));
  const rows = [...new Set([...g.aggregate_t, ...g.aggregate_m].map(p => p[1]))].sort((a,b) => a-b);
  for (const r of rows) {
    grid.append(node('div', math('r=' + r), 'point-cell'));
    grid.append(node('div', math(String(ts.get(r) || 0)), 'point-cell' + (ts.has(r) ? ' tmark' : ' absent')));
    grid.append(node('div', ms.has('1:' + r) ? math(ast(c.formulas[ms.get('1:' + r)])) : 'unassigned', 'point-cell' + (ms.has('1:' + r) ? ' fmark' : ' absent')));
    const offsets = [2,3].filter(x => ms.has(x + ':' + r)).map(x => '\\delta_{' + (x-1) + '}=' + ms.get(x + ':' + r));
    grid.append(node('div', offsets.length ? math(offsets.join(',\\;')) : 'unassigned', 'point-cell' + (offsets.length ? ' rmark' : ' absent')));
  }
  const ports = byId('ports'); ports.replaceChildren();
  for (const component of g.components) {
    for (const p of component.ordered_receptor_ports) {
      const readers = p.readers.map(x => math('r=' + x.reader_row + ',\\;\\delta_{' + (x.primitive_input_port+1) + '}=' + x.offset_value)).join('; ');
      ports.append(node('li', component.name + ': receptor ' + math('r=' + p.input_row) + ' supplies ' + math(ast(c.formulas[p.formula_code])) + '. Reader marking: ' + readers + '.'));
    }
  }
  if (!ports.children.length) ports.append(node('li', 'This zero-port control has no external receptor.'));
  const proofRows = byId('translation-rows'); proofRows.replaceChildren();
  for (const item of g.translation_rows) {
    const tr = node('tr'); tr.append(node('td', math('r=' + item.row)), node('td', math(ast(c.formulas[item.formula_code]))), node('td', item.words)); proofRows.append(tr);
  }
  typeset([byId('inspector')]);
}
const c = saved.partial_case;
c.groups.forEach((g,i) => { const option=node('option', g.components.map(x=>x.name).join(' + ')); option.value=String(i); byId('cluster-picker').append(option); });
byId('cluster-picker').value=String(c.groups.findIndex(g=>g.shared_member_count>0));
byId('cluster-picker').addEventListener('change', render);
render();
