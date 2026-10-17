'use strict';

const byId = id => document.getElementById(id);
const exactCount = value => Number.isSafeInteger(value) && value >= 0;
function escapeName(value) { return String(value).replace(/_/g, '\\_'); }
function term(t) {
  if (t[0] === 'var') return escapeName(t[1]);
  if (t[0] === 'fun') return '\\operatorname{' + escapeName(t[1]) + '}' +
    (t[2].length ? '(' + t[2].map(term).join(',') + ')' : '');
  throw Error('Unknown term in display');
}
function formula(f) {
  if (f[0] === 'all') return '\\forall ' + escapeName(f[1]) + '\\, ' + formula(f[2]);
  if (f[0] === 'eq') return term(f[1]) + '=' + term(f[2]);
  if (f[0] === 'bot') return '\\bot';
  if (f[0] === 'not') return '\\neg(' + formula(f[1]) + ')';
  if (f[0] === 'pred') return '\\operatorname{' + escapeName(f[1]) + '}' +
    (f[2].length ? '(' + f[2].map(term).join(',') + ')' : '');
  const connective = {imp: '\\to', and: '\\land', or: '\\lor'}[f[0]];
  if (connective) return '(' + formula(f[1]) + ')' + connective + '(' + formula(f[2]) + ')';
  throw Error('Unknown formula in display');
}
function math(el, source, display = false) {
  el.textContent = (display ? '\\[' : '\\(') + source + (display ? '\\]' : '\\)');
}
function measured(el, value, divisor, places, unit) {
  if (Number.isFinite(value) && value >= 0) math(el, (value / divisor).toFixed(places) + '\\;\\mathrm{' + unit + '}');
  else el.textContent = 'Not returned';
}
function svgElement(svg, tag, attrs, text) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  if (text !== undefined) el.textContent = text;
  svg.appendChild(el);
  return el;
}
function graph(data) {
  const svg = byId('dependency-view'), n = data.rows.length, height = Math.max(180, n * 96 + 40);
  svg.setAttribute('viewBox', '0 0 650 ' + height);
  svg.style.maxHeight = Math.min(height, 650) + 'px';
  const defs = svgElement(svg, 'defs', {});
  const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
  for (const [key, value] of Object.entries({id: 'dependency-arrow', markerWidth: '8', markerHeight: '8', refX: '7', refY: '4', orient: 'auto'})) marker.setAttribute(key, value);
  const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  arrow.setAttribute('d', 'M 0 0 L 8 4 L 0 8 z'); arrow.setAttribute('fill', '#c68b2d');
  marker.appendChild(arrow); defs.appendChild(marker);
  const y = i => 48 + i * 96;
  for (const edge of data.edges) {
    const a = y(edge.source_node_index), b = y(edge.consumer_node_index);
    svgElement(svg, 'path', {d: 'M 275 ' + a + ' C 500 ' + a + ', 500 ' + b + ', 275 ' + b, fill: 'none', stroke: '#c68b2d', 'stroke-width': 3, 'marker-end': 'url(#dependency-arrow)'});
  }
  data.rows.forEach((row, i) => {
    svgElement(svg, 'rect', {x: 65, y: y(i) - 27, width: 210, height: 54, rx: 7, fill: '#e5f0f7', stroke: '#3075a7', 'stroke-width': 2});
    svgElement(svg, 'text', {x: 170, y: y(i) + 6, 'text-anchor': 'middle'}, row.label);
    for (let k = 0; k < row.open_premises.length; k++) {
      const a = y(i) + 14 + k * 8;
      svgElement(svg, 'line', {x1: 20, y1: a, x2: 65, y2: a, stroke: '#8b9ba1', 'stroke-width': 2, 'stroke-dasharray': '4 4'});
      svgElement(svg, 'circle', {cx: 20, cy: a, r: 5, fill: 'white', stroke: '#8b9ba1'});
    }
  });
}

async function start() {
  const response = await fetch('report-data.json', {cache: 'no-store'});
  if (!response.ok) throw Error('Evidence fetch failed');
  const d = await response.json(), s = d.disposition;
  byId('status').textContent = d.status_text;
  measured(byId('elapsed'), s.native_launch_to_postprobe_ns, 1e9, 2, 's');
  measured(byId('memory'), s.aggregate_B_bytes, 1048576, 1, 'MiB');
  for (const [id, key] of [['result-title', 'result_title'], ['result-text', 'result_text'], ['reader-title', 'reader_title'], ['reader-intro', 'reader_intro']]) byId(id).textContent = d[key];

  if (d.rows.length) {
    byId('capture-view').hidden = false;
    graph(d);
    const controls = byId('row-controls');
    function show(index) {
      const row = d.rows[index];
      byId('row-label').textContent = row.label + ' · ' + row.rule;
      math(byId('formula'), formula(row.formula), true);
      byId('english').textContent = row.english;
      byId('raw-row').textContent = JSON.stringify(row, null, 2);
      const list = byId('premise-list'); list.replaceChildren();
      for (const premise of row.premises) {
        const el = document.createElement('p');
        el.className = premise.selected ? 'premise selected' : 'premise open';
        el.appendChild(document.createTextNode(premise.selected ? 'Selected source: ' : 'Open receptor: '));
        const span = document.createElement('span'); math(span, formula(premise.formula));
        el.appendChild(span); list.appendChild(el);
      }
      for (const button of controls.children) {
        const active = Number(button.dataset.index) === index;
        button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active));
      }
      if (window.MathJax?.typesetPromise) window.MathJax.typesetPromise([byId('formula'), list]);
    }
    d.rows.forEach((row, index) => {
      const button = document.createElement('button');
      button.dataset.index = index; button.textContent = row.label;
      button.addEventListener('click', () => show(index)); controls.appendChild(button);
    });
    show(0);
  } else {
    byId('unknown-view').hidden = false;
    const observations = Object.entries(d.last_observations || {});
    for (const [role, value] of observations) {
      const article = document.createElement('article'), title = document.createElement('h3'), p = document.createElement('p');
      title.textContent = role; article.appendChild(title);
      if (value) {
        const row = exactCount(value.row) ? String(value.row) : '\\text{not supplied}';
        const count = exactCount(value.selected_count) ? String(value.selected_count) : '\\text{not supplied}';
        math(p, '\\text{row }' + row + '\\qquad\\text{selected }' + count);
      } else p.textContent = 'No callback entry recorded.';
      article.appendChild(p); byId('last-observations').appendChild(article);
    }
    if (!observations.length) byId('last-observations').textContent = 'No callback-entry records were returned.';
  }

  byId('compare-status').textContent = d.comparison_status;
  measured(byId('compare-time'), s.native_launch_to_postprobe_ns, 1e9, 2, 's');
  measured(byId('compare-memory'), s.aggregate_B_bytes, 1048576, 1, 'MiB');
  const memo = d.structural_memo;
  let returnedMemo = false;
  for (const [id, key] of [['memo-lookups', 'lookups'], ['memo-hits', 'hits'], ['memo-inspections', 'full_inspections']]) {
    if (memo && Object.prototype.hasOwnProperty.call(memo, key) && exactCount(memo[key])) {
      math(byId(id), String(memo[key])); returnedMemo = true;
    } else byId(id).textContent = 'Not returned';
  }
  byId('memo-scope').textContent = returnedMemo
    ? 'Only counters present in the complete measured record are shown. They count structural observer work, not proofs, candidate eliminations or checked-tile savings.'
    : 'No memo counters were returned. No hit, miss or inspection count is inferred from callback-entry scalars, phase markers or elapsed time.';

  const phases = s.phase_observations || [], launch = d.native_launch_ns;
  for (const phase of phases) {
    const el = document.createElement('article'), name = document.createElement('b'), stamp = document.createElement('span');
    name.textContent = phase.stage.toLowerCase().replace(/_/g, ' ');
    if (Number.isFinite(launch) && Number.isFinite(phase.native_ns) && phase.native_ns >= launch) measured(stamp, phase.native_ns - launch, 1e9, 3, 's');
    else stamp.textContent = 'Not returned';
    el.append(name, stamp); byId('phase-list').appendChild(el);
  }
  if (!phases.length) byId('phase-list').textContent = 'No complete phase marker was retained.';
  for (const [label, key] of d.evidence_links) {
    const li = document.createElement('li'), a = document.createElement('a');
    a.href = d.links[key]; a.textContent = label; li.appendChild(a); byId('evidence-list').appendChild(li);
  }
  byId('run-details').textContent = JSON.stringify(d.run_details, null, 2);
  if (window.MathJax?.typesetPromise) await window.MathJax.typesetPromise();
  document.body.dataset.loaded = 'true';
}
start().catch(error => {
  byId('status').textContent = 'Evidence could not be loaded: ' + error.message;
  document.body.dataset.loaded = 'error';
});
