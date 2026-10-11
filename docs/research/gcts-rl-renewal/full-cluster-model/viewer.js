/* Read completed point snapshots; this reader performs no proof search. */
const math = value => '\\(' + value + '\\)';
const symbol = value => '\\mathrm{' + String(value).replace(/_/g, '\\_') + '}';
function term(value) {
  if (value[0] === 'var') return symbol(value[1]);
  if (value[0] === 'fun') return symbol(value[1]) + (value[2].length ? '(' + value[2].map(term).join(',') + ')' : '');
  throw new Error('Unknown term in the frozen formula inventory');
}
function formula(value) {
  if (value[0] === 'pred') return symbol(value[1]) + '(' + value[2].map(term).join(',') + ')';
  if (value[0] === 'eq') return '(' + term(value[1]) + '=' + term(value[2]) + ')';
  if (value[0] === 'not') return '\\neg ' + formula(value[1]);
  if (value[0] === 'all') return '\\forall ' + symbol(value[1]) + '\\,(' + formula(value[2]) + ')';
  if (value[0] === 'and' || value[0] === 'imp') return '(' + formula(value[1]) + (value[0] === 'and' ? '\\land ' : '\\to ') + formula(value[2]) + ')';
  throw new Error('Unknown formula in the frozen formula inventory');
}
function explanation(witness) {
  switch (witness.rule) {
    case 'axiom': return 'Introduce the theory axiom named ' + witness.name + '.';
    case 'assumption': return 'Use a hypothesis of this symbolic context.';
    case 'instantiate': return 'Introduce the logical axiom that allows a universally quantified formula to be instantiated.';
    case 'eq_subst': return 'Introduce the logical axiom for substituting equal terms into the stated formula.';
    case 'mp': return 'Read the ordered antecedent and implication rows; infer the consequent by modus ponens.';
    default: throw new Error('Unknown primitive witness in the frozen inventory');
  }
}
const sameKey = (left, right) => JSON.stringify(left) === JSON.stringify(right);
function compatible(graph, key, preimage) {
  if (graph.excluded[key[1]].some(other => sameKey(key, other))) return false;
  if (preimage.t.some(([, row, value]) => graph.totals[row] + value > 1)) return false;
  const assigned = new Map(graph.marks.map(([x, y, value]) => [x + ',' + y, value]));
  return preimage.m.every(([x, y, value]) => !assigned.has(x + ',' + y) || assigned.get(x + ',' + y) === value);
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
async function startReader() {
  const response = await fetch('visual-data.json');
  if (!response.ok) throw new Error('Saved visual data could not be loaded');
  const data = await response.json();
  const stateSelect = document.getElementById('saved-state');
  const clusterSelect = document.getElementById('cluster');
  data.states.forEach((state, index) => { const option = element('option', state.label); option.value = index; stateSelect.append(option); });
  data.descriptors.forEach((descriptor, index) => { const option = element('option', descriptor.body_name); option.value = index; clusterSelect.append(option); });
  stateSelect.value = String(data.default_state);
  clusterSelect.value = String(data.default_cluster);
  const viewer = document.getElementById('cluster-view');
  async function render() {
    if (window.MathJax?.typesetClear) MathJax.typesetClear([viewer]);
    viewer.replaceChildren();
    const saved = data.states[Number(stateSelect.value)];
    const graph = saved.state.graph;
    const index = Number(clusterSelect.value);
    const descriptor = data.descriptors[index];
    const hint = saved.state.hint_states[index];
    viewer.append(element('p', 'Saved state: ' + saved.label + '. Selected primitive placements: ' + math(graph.order.length) + '.'));
    const assigned = element('div', undefined, 'marks');
    assigned.append(element('strong', 'Current assigned markings'));
    graph.marks.filter(([, y]) => y >= 0).forEach(([x, y, value]) => assigned.append(element('span', math('m(' + x + ',' + y + ')=' + value), 'mark ' + (x === 1 ? 'formula-mark' : 'reference-mark'))));
    viewer.append(assigned);
    const article = element('article', undefined, 'cluster ' + hint.status);
    article.append(element('h3', descriptor.body_name + ' — ' + hint.status));
    article.append(element('p', hint.reason ? 'Whole retirement reason: ' + hint.reason + '.' : 'Whole descriptor is ' + hint.status + '.'));
    descriptor.members.forEach((key, memberIndex) => {
      const preimage = descriptor.full_identity_preimages[memberIndex];
      const recipe = data.recipes[key[0]];
      const row = element('div', undefined, 'tile-row');
      const tile = element('div', math('r=' + key[1]), 'tile');
      const outputCode = data.formulas.findIndex(value => JSON.stringify(value) === JSON.stringify(recipe.primitive_witness.formula));
      tile.append(element('span', math('F_{' + outputCode + '}'), 'formula-mark tile-layer'));
      if (key[2].length) tile.append(element('span', math('(' + key[2].map(source => source - key[1]).join(',') + ')'), 'reference-mark tile-layer'));
      tile.append(element('small', 'translation only'));
      row.append(tile);
      const text = element('div', undefined, 'tile-text');
      const selected = graph.order.some(other => sameKey(key, other));
      text.append(element('p', math('t(0,' + key[1] + ')=1') + ' · ' + (selected ? 'exact placement already selected once' : compatible(graph, key, preimage) ? 'pending · compatible with saved point values' : 'pending · incompatible with saved point values')));
      text.append(element('p', explanation(recipe.primitive_witness)));
      if (key[2].length) text.append(element('p', 'Ordered source rows: ' + math('(' + key[2].join(',') + ')') + '.'));
      const details = element('details');
      details.append(element('summary', 'Read the exact symbolic formula ' + math('F_{' + outputCode + '}')));
      details.append(element('div', math(formula(recipe.primitive_witness.formula)), 'formula'));
      text.append(details);
      const marks = element('div', undefined, 'marks');
      preimage.m.forEach(([x, y, value]) => marks.append(element('span', math('m(' + x + ',' + y + ')=' + value), 'mark ' + (x === 1 ? 'formula-mark' : 'reference-mark'))));
      text.append(marks);
      row.append(text); article.append(row);
    });
    viewer.append(article);
    if (window.MathJax?.typesetPromise) await MathJax.typesetPromise([viewer]);
  }
  stateSelect.addEventListener('change', render);
  clusterSelect.addEventListener('change', render);
  for (const [id, name] of [['formula-layer', 'hide-formulas'], ['reference-layer', 'hide-references']]) document.getElementById(id).addEventListener('change', event => document.getElementById('reader').classList.toggle(name, !event.target.checked));
  if (window.MathJax?.startup?.promise) await MathJax.startup.promise;
  await render();
}
startReader().catch(error => { document.getElementById('cluster-view').textContent = error.message; });
