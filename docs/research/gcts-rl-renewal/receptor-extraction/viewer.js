/* Evidence presentation only; no checker, extraction or search authority. */
'use strict';
const $ = id => document.getElementById(id);
const esc = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function term(v) {
  if (!Array.isArray(v)) throw Error('Malformed term');
  if (v[0] === 'meta-term' || v[0] === 'var') return esc(v[1]);
  if (v[0] === 'fun') return `\\mathrm{${esc(v[1])}}${v[2].length ? `(${v[2].map(term).join(',')})` : ''}`;
  throw Error('Unsupported term constructor');
}
function formula(v) {
  switch(v[0]) {
    case 'pred': return `\\operatorname{${esc(v[1])}}(${v[2].map(term).join(',')})`;
    case 'eq': return `${term(v[1])}=${term(v[2])}`;
    case 'imp': return `(${formula(v[1])}\\to ${formula(v[2])})`;
    case 'and': return `(${formula(v[1])}\\land ${formula(v[2])})`;
    case 'or': return `(${formula(v[1])}\\lor ${formula(v[2])})`;
    case 'not': return `\\neg ${formula(v[1])}`;
    case 'all': return `\\forall ${esc(v[1])}\\,${formula(v[2])}`;
    case 'bot': return '\\bot';
    default: throw Error('Unsupported formula constructor');
  }
}
const math = value => `\\(${value}\\)`;
const secs = n => math(`${Number(n).toFixed(3)}\\,\\mathrm{s}`);
let data, library, audit;
async function typeset(nodes) {
  if (window.MathJax?.startup?.promise) {
    await MathJax.startup.promise;
    await MathJax.typesetPromise(nodes);
  }
}
function draw(body, derivation) {
  const keys = derivation.original_keys;
  const wanted = new Set(body.body_command_indices);
  const incoming = new Set(body.ordered_external_command_indices);
  const y = row => 35 + row * 52;
  const height = y(Math.max(...keys.map(key=>key[1])))+35;
  const parts = [`<svg class="diagram" viewBox="0 0 350 ${height}" role="img" aria-label="Original donor tiles with extracted body and long-range marking receptors">`];
  keys.forEach((key,i) => {
    if (!wanted.has(i)) return;
    key[2].forEach((row,port) => {
      const color = port === 0 ? '#16887e' : '#8861aa';
      const x = 205 + port * 65;
      parts.push(`<path d="M 145 ${y(key[1])} H ${x} V ${y(row)} H 145" fill="none" stroke="${color}" stroke-width="2"/>`);
      parts.push(`<circle cx="145" cy="${y(row)}" r="4" fill="#2472ac"/>`);
      parts.push(`<circle cx="${x}" cy="${y(key[1])}" r="5" fill="${color}"/>`);
    });
  });
  keys.forEach((key,i) => {
    const active = wanted.has(i), input = incoming.has(i), color = active ? '#16887e' : input ? '#2472ac' : '#a0a8af';
    parts.push(`<g opacity="${active || input ? 1 : .42}"><text x="18" y="${y(key[1])+5}" font-size="12" fill="#586575">row ${key[1]}</text><rect x="90" y="${y(key[1])-22}" width="44" height="44" rx="2" fill="white" stroke="${color}" stroke-width="${active ? 3 : 1.5}"/><circle cx="112" cy="${y(key[1])}" r="4" fill="#364250"/><circle cx="145" cy="${y(key[1])}" r="5" fill="#2472ac"/><text x="96" y="${y(key[1])-9}" font-size="9" fill="#586575">L${i+1}</text></g>`);
  });
  parts.push('</svg>'); return parts.join('');
}
function showOrigin() {
  const family = library.families[Number($('family-choice').value)];
  const body = family.evidence[Number($('origin-choice').value)];
  const ground = audit.open_ground_body_checks.find(g => g.family_id === family.family_id && g.command_root === body.origin.command_root && g.certificate.sha256 === body.origin.certificate.sha256);
  const derivation = library.derivations.find(d => d.certificate.sha256 === body.origin.certificate.sha256);
  if (!ground || !derivation) throw Error('Missing complete origin or independent ground check');
  MathJax?.typesetClear?.([$ ('lines'), $('family-formula'), $('origin')]);
  $('origin').innerHTML = `<p>Source: ${esc(body.origin.origin === 'actual_selected' ? 'actual selected proof' : 'checked proposed proof')}; original command root ${math(String(body.origin.command_root+1))}. The original donor has ${math(String(derivation.original_commands.length))} lines.</p>`;
  $('geometry').innerHTML = draw(body, derivation);
  $('geometry-caption').innerHTML = `The extracted body occupies its three original donor rows. Blue input tiles expose its two receptors; faded tiles retain the surrounding proof. Horizontal spacing is schematic. Row addresses are source evidence, not a new recipient placement.`;
  $('lines').innerHTML = ground.commands.map((command,i) => {
    const words = command.rule === 'assumption' ? `Expose receptor ${i+1} as a local hypothesis.` : command.rule === 'eq_subst' ? 'Use the licensed equality-substitution instance.' : command.rule === 'mp' ? `Apply modus ponens to local lines ${command.antecedent+1} and ${command.implication+1}.` : `Apply ${command.rule}.`;
    return `<article class="line ${i<2 ? 'input' : 'body'}"><h3>Local line ${i+1}</h3><div class="formula">${math(formula(command.formula))}</div><p>${esc(words)}</p></article>`;
  }).join('');
  $('shape').textContent = JSON.stringify(family.shape, null, 2);
  $('physical').textContent = JSON.stringify({body_keys:body.source_body_keys, ordered_receptor_ancestor_rows:body.ordered_receptor_ancestor_rows, original_parameters:body.original_parameters, original_ordered_Gamma:body.ambient_original_ordered_Gamma}, null, 2);
  typeset([$ ('lines'), $('origin')]).catch(error => { $('status').textContent = `Typesetting failed: ${error.message}`; });
}
function showFamily() {
  const family = library.families[Number($('family-choice').value)];
  MathJax?.typesetClear?.([$ ('family-formula')]);
  const sequent = String.raw`${family.shape.input_receptors.map(formula).join(',\\quad ')}\ \vdash\ ${formula(family.shape.output)}`;
  $('family-formula').innerHTML = `<div class="formula">${math(sequent)}</div><p>Parameterized display; finite ground checks only. The equality changes incidence argument ${math(String(family.shape.slot+1))}.</p>`;
  $('origin-choice').innerHTML = family.evidence.map((body,i) => `<option value="${i}">Origin ${i+1}: ${esc(body.origin.origin)}, source line ${body.origin.command_root+1}</option>`).join('');
  $('origin-choice').disabled = false;
  showOrigin();
  typeset([$ ('family-formula')]).catch(error => { $('status').textContent = `Typesetting failed: ${error.message}`; });
}
async function main() {
  [data,library,audit] = await Promise.all(['summary.json','candidate-library.json','independent-audit.json'].map(async path => { const response=await fetch(path); if(!response.ok) throw Error(`HTTP ${response.status}: ${path}`); return response.json(); }));
  $('status').textContent = data.completed ? 'The complete extraction and independent ground audit passed their resource qualification. The library remains a candidate.' : 'The stage is incomplete; no usable candidate prefix is admitted.';
  $('counts').innerHTML = `<p>${math(String(library.families.length))} normalized families from ${math(String(library.derivations.length))} retained proofs and ${math(String(Object.keys(library.correlated_sequents).length))} distinct sequents. ${math(String(library.complete_origin_census.length))} source roots were examined; ${math(String(library.complete_origin_census.filter(x=>x.eligible).length))} were eligible.</p><p>The independent audit completed ${math(String(audit.metrics.primitive_commands_completed))} primitive-interface checks, ${math(String(audit.metrics.certificate_proofs_completed))} whole donor proof checks and ${math(String(audit.metrics.open_ground_bodies_completed))} exposed-body ground checks.</p>`;
  $('costs').innerHTML = `<table><thead><tr><th>Measured scope</th><th>Actual cost</th></tr></thead><tbody><tr><td>Complete inner extraction, audit and successful preparation</td><td>${secs(data.costs.inner_complete_seconds)}</td></tr><tr><td>Cold owned lifetime through post-write observation</td><td>${secs(data.costs.owned_seconds)}</td></tr><tr><td>Caller interval, before its separate finish margin</td><td>${secs(data.costs.caller_seconds)}</td></tr><tr><td>Conditional conservative owned memory peak</td><td>${math(`${(data.costs.peak_bytes/1048576).toFixed(2)}\\,\\mathrm{MiB}`)}</td></tr></tbody></table>`;
  $('donors').innerHTML = `<table><thead><tr><th>Donor origin</th><th>All roots</th><th>Eligible</th><th>Correlation</th></tr></thead><tbody>${audit.census.map((row,i)=>`<tr><td>Donor ${i+1}: ${esc(row.origin)}</td><td>${math(String(row.command_roots))}</td><td>${math(String(row.eligible_roots))}</td><td><code>${row.correlated_sequent_id.slice(0,12)}</code></td></tr>`).join('')}</tbody></table>`;
  $('root-census').innerHTML = `<details><summary>Complete eligible and ineligible root census</summary><pre>${esc(JSON.stringify(library.complete_origin_census,null,2))}</pre></details>`;
  $('family-choice').innerHTML = library.families.map((family,i)=>`<option value="${i}">Family ${i+1}: equality transport in incidence argument ${family.shape.slot+1}; ${family.evidence.length} retained origins</option>`).join('');
  $('family-choice').disabled = library.families.length === 0;
  $('family-choice').addEventListener('change',showFamily);
  $('origin-choice').addEventListener('change',showOrigin);
  await typeset([document.querySelector('main')]);
  if (library.families.length) showFamily();
  else {
    $('family-formula').textContent = 'The complete scan found no family within this extraction language.';
    $('origin-choice').disabled = true;
  }
}
main().catch(error => { $('status').textContent = `Evidence display failed: ${error.message}`; console.error(error); });
