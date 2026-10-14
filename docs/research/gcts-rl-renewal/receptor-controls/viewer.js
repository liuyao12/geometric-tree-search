/* Saved presentation only. No scientific implementation, authority or tests. */
'use strict';
const byId = id => document.getElementById(id);
const escapeText = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const math = value => `\\(${escapeText(value)}\\)`;
const pending = text => `<p class="pending">${escapeText(text)}</p>`;
function safeLink(value) {
  const url = new URL(value, location.href);
  if (url.origin !== location.origin || !['http:', 'https:'].includes(url.protocol)) throw Error('Evidence link must stay on the report origin');
  return escapeText(url.href);
}
function shownValue(row) {
  if (row.value === null || row.value === undefined) return 'Unavailable';
  if (typeof row.value !== 'number' || !Number.isFinite(row.value)) return escapeText(row.value);
  return math(`${row.value}${row.unit_latex ? `\\,${row.unit_latex}` : ''}`);
}
function table(rows, heading) {
  if (!rows.length) return pending(`${heading}: pending attachment.`);
  return `<table><thead><tr><th>Saved scope</th><th>Recorded result</th><th>Qualification</th></tr></thead><tbody>${rows.map(row => `<tr><td>${escapeText(row.label)}</td><td>${shownValue(row)}</td><td>${escapeText(row.scope || '')}</td></tr>`).join('')}</tbody></table>`;
}
function renderAttempts(rows) {
  if (!rows.length) return pending('Saved attempt records have not been attached.');
  const number = (value, unit = '') => value === null || value === undefined ? 'Pending' : math(`${value}${unit ? `\\,${unit}` : ''}`);
  const overview = `<table><thead><tr><th>Version</th><th>Status</th><th>Whole owned</th><th>Caller</th><th>Observed peak</th><th>Completed cases</th></tr></thead><tbody>${rows.map(row => `<tr><td>${escapeText(row.version)}</td><td>${escapeText(row.status)}</td><td>${number(row.owned_seconds, '\\mathrm{s}')}</td><td>${number(row.caller_seconds, '\\mathrm{s}')}</td><td>${number(row.peak_MiB, '\\mathrm{MiB}')}</td><td>${number(row.completed_cases)}</td></tr>`).join('')}</tbody></table>`;
  return overview + rows.map(row => `<details><summary>${escapeText(row.label)}</summary><p>${escapeText(row.explanation || '')}</p><pre>${escapeText(JSON.stringify(row.saved_scope || {}, null, 2))}</pre></details>`).join('');
}
function drawGroundRows(rows) {
  const y = row => 35 + row * 52;
  const height = y(Math.max(...rows.map(row=>row.physical_row))) + 40;
  const parts = [`<svg class="diagram" viewBox="0 0 350 ${height}" role="img" aria-label="Six actual saved point-tile placements and their ordered remote formula reads">`];
  rows.forEach(row => row.ordered_prior_rows.forEach((ref,port) => {
    const color=port===0?'#16887e':'#8861aa', x=205+port*65;
    parts.push(`<path d="M ${x} ${y(row.physical_row)} V ${y(ref)} H 145" fill="none" stroke="${color}" stroke-width="2"/><path d="M 145 ${y(row.physical_row)} H ${x}" fill="none" stroke="${color}" stroke-width="2"/><circle cx="${x}" cy="${y(row.physical_row)}" r="5" fill="${color}"/>`);
  }));
  rows.forEach(row => {
    const cy=y(row.physical_row), color=row.command.rule==='assumption'?'#2472ac':'#16887e';
    parts.push(`<text x="10" y="${cy+4}" font-family="system-ui,sans-serif" font-size="12" fill="#586575">${escapeText(row.label)}</text><rect x="95" y="${cy-22}" width="44" height="44" fill="white" stroke="${color}" stroke-width="2"/><circle cx="117" cy="${cy}" r="4" fill="#364250"/><circle cx="145" cy="${cy}" r="5" fill="#2472ac"/>`);
  });
  parts.push('</svg>');
  return `<figure id="ground-geometry">${parts.join('')}<figcaption>Actual saved primitive placements. Blue points carry formula codes; green and purple links follow the ordered prior-row reads. Squares illustrate unit point supports; horizontal spacing is schematic. This ground expansion was checked, with no macro execution or completed board.</figcaption></figure>`;
}
function renderGroundRows(rows) {
  if (!rows.length) return pending('No complete ground-row display is attached at this checkpoint; inspect the raw controls and earlier donor reader.');
  return drawGroundRows(rows) + rows.map(row => `<article class="line"><h3>${escapeText(row.label)}</h3><div class="formula">${math(row.formula_latex)}</div><p>${escapeText(row.formula_english)}</p><p>${escapeText(row.derivation_english)}</p><p class="muted">${escapeText(row.origin_scope)}</p><details><summary>Exact saved command, point values and ordered reads</summary><pre>${escapeText(JSON.stringify({command:row.command, physical_row:row.physical_row, ordered_prior_rows:row.ordered_prior_rows, t:row.t, m:row.m, dependency_consumed_original_Gamma:row.original_Gamma_occurrences}, null, 2))}</pre></details></article>`).join('');
}
async function typeset() {
  if (window.MathJax?.startup?.promise) {
    await MathJax.startup.promise;
    await MathJax.typesetPromise([document.querySelector('main')]);
  }
}
async function main() {
  // Only ROOT-supplied saved display data are attached; no new scientific calls.
  const response = await fetch('summary.json');
  if (!response.ok) throw Error(`Display packet HTTP ${response.status}`);
  const packet = await response.json();
  if (packet.schema !== 'Notebook158-saved-display-packet-v1' || packet.notebook !== 158 || packet.presentation_only !== true) throw Error('Unexpected display packet');
  if (!['pending','actual'].includes(packet.display_state)) throw Error('Unknown display state');
  if (packet.display_state === 'pending') {
    byId('status').textContent = 'SOURCE scaffold. Actual control records and measured values are pending attachment.';
    byId('result-lead').textContent = packet.lead;
    await typeset();
    return;
  }
  // These are saved ROOT presentation fields, never fresh checker acceptance.
  for (const field of ['control_results','costs','attempts','ground_rows','evidence_links']) if (!Array.isArray(packet[field])) throw Error(`Missing whole display array: ${field}`);
  byId('status').textContent = packet.status_text || 'Saved actual records attached. Each outcome retains its own scope.';
  byId('result-lead').textContent = packet.lead;
  byId('control-results').innerHTML = table(packet.control_results, 'Control outcomes');
  byId('control-costs').innerHTML = table(packet.costs, 'Measured costs');
  byId('attempt-records').innerHTML = renderAttempts(packet.attempts);
  byId('ground-rows').innerHTML = renderGroundRows(packet.ground_rows);
  byId('evidence-links').innerHTML = packet.evidence_links.length ? `<p>${packet.evidence_links.map(row => `<a href="${safeLink(row.href)}">${escapeText(row.label)}</a>`).join(' · ')}</p>` : pending('No frozen evidence links have been attached.');
  await typeset();
}
main().catch(error => { byId('status').textContent = `Display unavailable: ${error.message}. No runtime result is inferred.`; });
