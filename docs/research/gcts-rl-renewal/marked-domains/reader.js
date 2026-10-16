'use strict';
// Presentation of saved JSON only. No primitive, point matcher or proof code.
const $ = id => document.getElementById(id);
const math = value => `\\(${value}\\)`;
const latexName = value => String(value).replace(/[\\{}_%&#$^~]/g, ch => ({'\\':'\\backslash{}','^':'\\hat{}','~':'\\tilde{}'}[ch] || '\\'+ch));
const node = (tag, value, className) => {
  const el = document.createElement(tag);
  if (value !== undefined) el.textContent = value;
  if (className) el.className = className;
  return el;
};
const list = value => Array.isArray(value) ? value : [];
let data, activeRun = 0, activeCase = -1, mathQueue = Promise.resolve();

function term(value) {
  if (!Array.isArray(value)) return '\\text{unavailable term}';
  if (value[0] === 'var') return latexName(value[1]);
  if (value[0] !== 'fun' || !Array.isArray(value[2])) return '\\text{unavailable term}';
  const args = value[2].map(term), name = value[1];
  if ((name === 'zero' || name === '0') && !args.length) return '0';
  if ((name === 'succ' || name === 'S') && args.length === 1) return `S(${args[0]})`;
  if ((name === 'add' || name === '+') && args.length === 2) return `(${args[0]}+${args[1]})`;
  return `\\operatorname{${latexName(name)}}${args.length ? '('+args.join(',')+')' : ''}`;
}

function formula(value) {
  if (!Array.isArray(value)) return '\\text{unavailable formula}';
  if (value[0] === 'not') {
    let body = value, count = 0;
    while (Array.isArray(body) && body[0] === 'not' && count < 256) { count++; body = body[1]; }
    return count === 1 ? `\\neg\\bigl(${formula(body)}\\bigr)` :
      `\\underbrace{\\neg\\cdots\\neg}_{${count}\\ \\text{literal negations}}\\bigl(${formula(body)}\\bigr)`;
  }
  switch (value[0]) {
    case 'bot': return '\\bot';
    case 'eq': return `${term(value[1])}=${term(value[2])}`;
    case 'pred': return `\\operatorname{${latexName(value[1])}}${list(value[2]).length ? '('+list(value[2]).map(term).join(',')+')' : ''}`;
    case 'all': return `\\forall ${latexName(value[1])}\\;\\bigl(${formula(value[2])}\\bigr)`;
    case 'imp': return `\\bigl(${formula(value[1])}\\bigr)\\Rightarrow\\bigl(${formula(value[2])}\\bigr)`;
    case 'and': return `\\bigl(${formula(value[1])}\\bigr)\\land\\bigl(${formula(value[2])}\\bigr)`;
    case 'or': return `\\bigl(${formula(value[1])}\\bigr)\\lor\\bigl(${formula(value[2])}\\bigr)`;
    default: return '\\text{unavailable formula}';
  }
}

function markText(value) {
  if (Array.isArray(value) && value[0] === 'formula' && typeof value[1] === 'string') {
    try { return math(formula(JSON.parse(value[1]))); } catch (_) { return 'Saved formula label unavailable'; }
  }
  if (Array.isArray(value) && value[0] === 'offset') return math(`\\operatorname{offset}(${value[1]})`);
  if (Array.isArray(value) && value[0] === 'outside') return 'Outside sentinel';
  if (typeof value === 'number') return math(String(value));
  return JSON.stringify(value);
}

function typeset(nodes) {
  mathQueue = mathQueue.then(async () => {
    if (window.MathJax?.startup?.promise) {
      await window.MathJax.startup.promise;
      window.MathJax.typesetClear(nodes);
      await window.MathJax.typesetPromise(nodes);
    }
  }).catch(() => { document.body.dataset.mathFailed = 'true'; });
  return mathQueue;
}

function appendLinks(container, links) {
  container.replaceChildren();
  for (const item of list(links)) {
    if (!item || typeof item.href !== 'string') continue;
    let url;
    try { url = new URL(item.href, document.baseURI); } catch (_) { continue; }
    if (!['http:', 'https:'].includes(url.protocol)) continue;
    const anchor = node('a', item.label || item.href); anchor.href = item.href;
    const li = node('li'); li.append(anchor); container.append(li);
  }
  if (!container.children.length) container.append(node('li', 'No evidence links supplied.'));
}

function summary(label, value, detail) {
  const el = node('div', undefined, 'summary-card');
  el.append(node('span', label, 'eyebrow'), node('strong', value), node('span', detail, 'caption'));
  $('receipt-summary').append(el);
}

function selectedEvidence(run, control) {
  const own = control && ['state','proposal','receipt','record'].some(key => Object.prototype.hasOwnProperty.call(control, key));
  return own ? {state:control.state, proposal:control.proposal, receipt:control.receipt, record:control.record,
    scope:'This control has its own saved evidence.', links:control.links || run.links} :
    {state:run.state, proposal:run.proposal, receipt:run.receipt, record:run.record,
      scope:control ? 'The selected control has an outcome summary only. The receipt below belongs to the endpoint primary evidence, not to that control.' : 'Endpoint primary saved evidence.', links:run.links};
}

function showState(state, query) {
  $('state').replaceChildren();
  if (!state || !Array.isArray(state.t) || !Array.isArray(state.m)) {
    $('state').append(node('p', 'No complete saved point state is available.', 'empty')); return;
  }
  const marks = new Map(state.m.filter(entry => Array.isArray(entry[0]) && entry[0][0] === 1).map(([point,value]) => [point[1],value]));
  const added = new Map(state.m.filter(entry => Array.isArray(entry[0]) && entry[0][0] === 4).map(([point,value]) => [point[1],value]));
  const table = node('table', undefined, 'state-table'), head = node('tr');
  for (const label of ['Saved row','Support total','Assigned output','Added marking']) head.append(node('th', label));
  table.append(head);
  for (const [point, value] of state.t) {
    const tr = node('tr');
    tr.append(node('td', math(String(point[1]))+(query === point[1] ? ' · queried' : '')),
      node('td', math(String(value))), node('td', marks.has(point[1]) ? markText(marks.get(point[1])) : 'Absent'),
      node('td', added.has(point[1]) ? markText(added.get(point[1])) : 'Absent'));
    table.append(tr);
  }
  $('state').append(table);
}

function pointMap(packet) {
  const support = list(packet.global_t_values), marks = list(packet.global_m_values);
  const points = [...support, ...marks].filter(entry => Array.isArray(entry) && Array.isArray(entry[0]));
  if (!points.length) return node('p', 'No point arrays saved for this packet.', 'empty');
  const rows = [...new Set(points.map(([point]) => point[1]))].sort((a,b) => a-b);
  const channels = [...new Set(points.map(([point]) => point[0]))].sort((a,b) => a-b);
  const table = node('table', undefined, 'point-map'), head = node('tr');
  head.append(node('th', 'row / channel'));
  for (const ch of channels) head.append(node('th', math(String(ch))));
  table.append(head);
  for (const row of rows) {
    const tr = node('tr'); tr.append(node('th', math(String(row))));
    for (const ch of channels) {
      const td = node('td');
      for (const [point,value] of support.filter(([p]) => p[0] === ch && p[1] === row)) {
        const square = node('span', math(String(value)), 'tile-support');
        square.title = `Saved t at ${JSON.stringify(point)}`; td.append(square);
      }
      for (const [point,value] of marks.filter(([p]) => p[0] === ch && p[1] === row)) {
        const dot = node('span', undefined, 'mark-dot ch'+ch+(value === 0 ? ' zero' : ''));
        dot.title = `Saved m at ${JSON.stringify(point)}: ${JSON.stringify(value)}`;
        dot.setAttribute('aria-label', dot.title); td.append(dot);
      }
      tr.append(td);
    }
    table.append(tr);
  }
  const wrap = node('div', undefined, 'point-scroll'); wrap.append(table);
  wrap.append(node('p','Only rows with saved entries are listed; spacing is compacted. Repeated point occurrences remain repeated dots and are listed below.','caption'));
  return wrap;
}

function candidate(packet, index) {
  const box = node('article', undefined, 'candidate');
  const key = packet.placement_key || {}, pre = key.type_preimage?.base_type_preimage || key.type_preimage || {};
  const witness = pre.primitive_witness;
  const positive = list(packet.global_t_values).find(entry=>Array.isArray(entry[0]) && entry[1]>0);
  if(positive){const portrait=node('div',undefined,'tile-portrait');portrait.append(node('strong',(witness?.rule||'tile').toUpperCase()),node('span',math('t('+positive[0].join(',')+')='+positive[1])),node('small','Translation only'));box.append(portrait);}
  box.append(node('h3', `Packet ${math(String(index+1))} · ${witness?.rule || 'rule unavailable'}`));
  box.append(node('p', witness ? math(formula(witness.formula)) : 'No saved primitive formula.', 'formula'));
  if (Array.isArray(key.translation)) box.append(node('p', `Saved translation ${math('('+key.translation.join(',')+')')}.`, 'caption'));
  box.append(pointMap(packet));
  const obligations = list(packet.read_obligations);
  if (obligations.length) {
    const inputs = node('ol', undefined, 'obligations');
    for (const obligation of obligations) inputs.append(node('li', `Requires ${math(formula(obligation.formula))} at row ${math(String(obligation.row))}; ${obligation.occupied === true ? 'occupied output' : obligation.occupied === false ? 'unoccupied pending obligation' : 'occupancy unavailable'}. Fact acceptance: ${String(obligation.fact_accepted)}.`));
    box.append(inputs);
  } else box.append(node('p', 'No ordered premise obligations saved.', 'caption'));
  const details = node('details'), title = node('summary', 'Actual point layers and full placement identity');
  const table = node('table'), header = node('tr');
  for (const label of ['Layer','Point','Saved value']) header.append(node('th',label));
  table.append(header);
  for (const [layer, entries] of [['t',packet.global_t_values],['m',packet.global_m_values]]) {
    for (const [point,value] of list(entries)) {
      const tr = node('tr'); tr.append(node('td', math(layer)), node('td', math('('+point.join(',')+')')), node('td', markText(value))); table.append(tr);
    }
  }
  const scroll = node('div',undefined,'table-scroll'); scroll.append(table);
  details.append(title,scroll,node('pre',JSON.stringify(key,null,2)));box.append(details);return box;
}

function showCoverage(receipt, proposal) {
  $('coverage').replaceChildren();
  const checked = receipt?.checked_fibre_cover;
  const census = checked || proposal?.fibre_cover;
  if (!census) { $('coverage').append(node('p','No finite-fibre census was saved. Absence does not establish an empty domain.','empty')); return; }
  $('coverage').append(node('p', checked && receipt.complete_cover_checked === true ?
    'The receipt contains an independently completed census.' : 'Submitted census or prefix only; no independent completion is displayed.'));
  if (Number.isInteger(census.output_nodes)) $('coverage').append(node('p',`Output constructors ${math(String(census.output_nodes))}; MP antecedent bound ${math('|A|\\leq '+census.MP_antecedent_max_nodes)}.`));
  const table = node('table'), header = node('tr');
  for (const label of ['Fibre','Case','Examined','Completed']) header.append(node('th',label));table.append(header);
  for (const fibre of [...list(census.UG_fibres),...list(census.ordered_MP_fibres)]) {
    const rows = fibre.rows || (Number.isInteger(fibre.row) ? [fibre.row] : []);
    const tr = node('tr');tr.append(node('td',`${fibre.inverse || 'Saved'} ${math('('+rows.join(',')+')')}`), node('td',({FINITE_AST_OCCURS_CHECK_EMPTY:'Same row cannot supply both premises.',not_universal_or_assigned_body_mismatch:'Output is not universal, or its body differs.',missing_or_matching_body:'Missing or matching body.',only_implication_assigned:'Implication fixed; infer antecedent.',antecedent_assigned:'Antecedent fixed; infer implication.',both_absent_full_scoped_carrier:'Both inputs missing; enumerate the bounded carrier.'})[fibre.case] || fibre.case || 'Unavailable'), node('td',Number.isInteger(fibre.examined) ? math(String(fibre.examined)) : 'Unavailable'), node('td',String(fibre.completed)));table.append(tr);
  }
  const wrap = node('div',undefined,'table-scroll');wrap.append(table);$('coverage').append(wrap);
}

async function showEvidence() {
  const run = list(data.runs)[activeRun];
  if (!run) return;
  const control = list(run.cases)[activeCase], evidence = selectedEvidence(run,control), receipt = evidence.receipt;
  $('case-outcome').textContent = control ? `${control.name || 'Unnamed control'} · ${control.status || 'Outcome unavailable'}` : 'Endpoint primary evidence. Choose a recorded control to inspect its outcome.';
  $('receipt-summary').replaceChildren();
  summary('Receipt status', receipt?.status || 'No returned receipt', run.qualified === true ? 'Endpoint qualified in the saved report.' : 'Endpoint not qualified or qualification unavailable.');
  summary('Complete cover', receipt ? String(receipt.complete_cover_checked) : 'Unavailable', 'Completion is distinct from a two-witness lower bound.');
  summary('Exact degree', Number.isInteger(receipt?.degree_exact) ? math(String(receipt.degree_exact)) : 'Not established', 'A missing exact count is not zero.');
  summary('Saved candidate keys', receipt && Array.isArray(receipt.candidate_keys) ? math(String(receipt.candidate_keys.length)) : 'Unavailable', 'Length of the saved receipt key list only.');
  $('evidence-scope').textContent = evidence.scope+(run.qualified === true ? '' : ' This endpoint is not qualified; displayed details do not imply an accepted result.');
  showState(evidence.state || receipt?.state, receipt?.row ?? evidence.proposal?.row);
  $('candidates').replaceChildren();
  const packets = list(receipt?.checked_candidates);
  for (const [index, packet] of packets.entries()) $('candidates').append(candidate(packet,index));
  if (!packets.length) $('candidates').append(node('p',receipt?.status === 'ZERO' && receipt?.complete_cover_checked === true ?
    'The saved completed receipt has no surviving candidate packets.' : 'No checked candidate packets are available. This does not establish a zero degree.','empty'));
  showCoverage(receipt,evidence.proposal);
  $('record').textContent = JSON.stringify({state:evidence.state ?? null,proposal:evidence.proposal ?? null,receipt:receipt ?? null,record:evidence.record ?? null},null,2);
  appendLinks($('run-links'),evidence.links);
  await typeset([$('case-outcome'),$('receipt-summary'),$('state'),$('candidates'),$('coverage')]);
  document.body.dataset.savedRun = String(run.id || activeRun);document.body.dataset.savedCase = String(activeCase);
}

async function selectRun(index) {
  activeRun=index;activeCase=-1;const run=data.runs[index];
  for (const [i,card] of [...$('runs').children].entries()) card.classList.toggle('active',i === index);
  $('run-select').value=String(index);$('case-select').replaceChildren();
  const primary=node('option','Endpoint primary evidence');primary.value='-1';$('case-select').append(primary);
  for (const [i,control] of list(run.cases).entries()) { const option=node('option',`${control.name || 'Control'} · ${control.status || 'Unavailable'}`);option.value=String(i);$('case-select').append(option); }
  $('case-select').disabled=!list(run.cases).length;
  await showEvidence();
}

async function main() {
  const response=await fetch('report-data.json?v=df73185965a8');if(!response.ok) throw new Error('Saved report data unavailable');
  data=await response.json();$('lead').textContent=typeof data.lead === 'string' ? data.lead : 'No report lead supplied.';
  $('outcome').textContent=typeof data.outcome === 'string' ? data.outcome : 'No outcome statement supplied.';
  appendLinks($('links'),data.links);
  for(const [i,run] of list(data.runs).entries()) {
    const card=node('div',undefined,'run-card'),button=node('button',run.label || run.id || 'Saved endpoint');
    button.type='button';button.addEventListener('click',()=>selectRun(i));card.append(button,node('strong',run.status || 'Status unavailable','status'));
    card.append(node('p',run.qualified === true ? 'Qualified in saved report' : run.qualified === false ? 'Not qualified' : 'Qualification unavailable',run.qualified === true ? 'qualified' : 'unqualified'));
    card.append(node('p',typeof run.seconds === 'number' && Number.isFinite(run.seconds) ? math(run.seconds.toFixed(6)+'\\,\\mathrm{s}') : 'Timing unavailable'));
    card.append(node('p','Native launch through postprobe; each endpoint separate.','caption'));$('runs').append(card);
    const option=node('option',run.label || run.id || 'Saved endpoint');option.value=String(i);$('run-select').append(option);
  }
  $('run-select').addEventListener('change',()=>selectRun(Number($('run-select').value)));
  $('case-select').addEventListener('change',()=>{activeCase=Number($('case-select').value);showEvidence();});
  if(list(data.runs).length) await selectRun(Math.max(0,data.runs.findIndex(run=>run.id==='singleton')));
  else { $('runs').append(node('p','No measured endpoints supplied.','empty'));$('run-select').disabled=$('case-select').disabled=true;$('candidates').append(node('p','No saved receipt or candidates.','empty')); }
  await typeset([document.querySelector('header'),$('results'),$('meaning')]);
  document.body.dataset.savedReaderReady='true';
}
main().catch(error=>{$('lead').textContent='Saved report unavailable: '+error.message;$('lead').classList.add('failure');document.body.dataset.savedReaderFailed='true';});
