'use strict';
// Render literal saved data only. No proof or point semantics execute here.
const $ = id => document.getElementById(id);
const math = value => `\\(${value}\\)`;
const list = value => Array.isArray(value) ? value : [];
const el = (tag, text, cls) => {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (cls) n.className = cls;
  return n;
};
const latexName = value => String(value).replace(/[\\{}_%&#$^~]/g,
  ch => ({'\\':'\\backslash{}','^':'\\hat{}','~':'\\tilde{}'}[ch] || '\\'+ch));
let data, active = 0, frame = 0, mathQueue = Promise.resolve();

function term(value) {
  if (!Array.isArray(value)) return '\\text{unavailable term}';
  if (value[0] === 'var') return latexName(value[1]);
  if (value[0] !== 'fun') return '\\text{unavailable term}';
  const args = list(value[2]).map(term);
  if (value[1] === 'zero' && !args.length) return '0';
  if (value[1] === 'succ' && args.length === 1) return `S(${args[0]})`;
  if (value[1] === 'add' && args.length === 2) return `(${args[0]}+${args[1]})`;
  return `\\operatorname{${latexName(value[1])}}${args.length ? '('+args.join(',')+')' : ''}`;
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
    case 'pred': return `\\operatorname{${latexName(value[1])}}(${list(value[2]).map(term).join(',')})`;
    case 'all': return `\\forall ${latexName(value[1])}\\;\\bigl(${formula(value[2])}\\bigr)`;
    case 'imp': return `\\bigl(${formula(value[1])}\\bigr)\\Rightarrow\\bigl(${formula(value[2])}\\bigr)`;
    case 'and': return `\\bigl(${formula(value[1])}\\bigr)\\land\\bigl(${formula(value[2])}\\bigr)`;
    case 'or': return `\\bigl(${formula(value[1])}\\bigr)\\lor\\bigl(${formula(value[2])}\\bigr)`;
    default: return '\\text{unavailable formula}';
  }
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

function links(container, values) {
  container.replaceChildren();
  for (const item of list(values)) {
    if (typeof item?.href !== 'string') continue;
    let url;
    try { url = new URL(item.href, document.baseURI); } catch (_) { continue; }
    if (!['http:','https:'].includes(url.protocol)) continue;
    const a = el('a', item.label || item.href); a.href = item.href;
    const li = el('li'); li.append(a); container.append(li);
  }
}

function classification(run) {
  return run.qualified === true ? 'QUALIFIED' : run.qualified === false ? 'UNQUALIFIED' : 'PENDING';
}

function card(label, value) {
  const n = el('div', undefined, 'summary-card');
  n.append(el('span',label,'eyebrow'),el('strong',value)); $('run-summary').append(n);
}

function keyPreimage(key) { return key?.type_preimage?.base_type_preimage; }
function ruleName(key) {
  const rule = keyPreimage(key)?.primitive_witness?.rule;
  return ({axiom:'AX',assumption:'Gamma',instantiate:'UI',eq_subst:'Eq',mp:'MP',generalize:'UG'})[rule] || 'Tile';
}

function showTimeline(run) {
  $('timeline').replaceChildren();
  const events = list(run.events).filter(e => ['DECISION','TRY','PLACE','RESTORE','EXCLUDE'].includes(e.kind));
  if (!events.length) { $('timeline').append(el('p','No returned decision, trial, placement, restore or exclusion events are supplied for this endpoint.','empty')); return; }
  for (const event of events) {
    const d = event.kind === 'DECISION' ? event.decision : null;
    const kind = d?.kind || event.kind;
    const row = d?.row ?? event.row;
    const box = el('article', undefined, 'event '+(kind === 'DEAD' ? 'dead' : kind === 'UNKNOWN' ? 'unknown' : kind === 'PLACE' ? 'place' : ''));
    const head = el('div', undefined, 'event-head');
    head.append(el('span',Number.isInteger(event.event) ? math(String(event.event)) : 'Saved event','caption'),el('strong',kind));
    if (Number.isInteger(row)) head.append(el('span',math(`r=${row}`)));
    box.append(head);
    const explanation = ({FORCED:'The global scan selected a sole candidate.',BRANCH:'The global scan selected a branch point.',DEAD:'The engine recorded a zero-candidate frontier point.',UNKNOWN:'The engine recorded unresolved local evidence.',TRY:'The search tried this actual candidate.',PLACE:'The engine placed this checked candidate.',RESTORE:'The search returned to its owned parent context.',EXCLUDE:'The engine excluded a candidate after an exhausted child.'})[kind];
    if (explanation) box.append(el('p',explanation,'caption'));
    const key = d?.candidate?.placement_key || event.key;
    if (key) {
      const tile = el('div',undefined,'tile-portrait'); tile.append(el('strong',ruleName(key)),el('small','Translation only')); box.append(tile);
      const output = keyPreimage(key)?.primitive_witness?.formula;
      if (output) box.append(el('div',math(formula(output)),'formula'));
    }
    if (event.child_status) box.append(el('p','Saved child result: '+event.child_status,'caption'));
    const details = el('details'); details.append(el('summary','Full recorded event'),el('pre',JSON.stringify(event,null,2))); box.append(details);
    $('timeline').append(box);
  }
}

function showFrame() {
  const selected = list(data.endpoints[active].frames)[frame];
  $('point-state').replaceChildren();
  $('frame-record').textContent = JSON.stringify(selected?.state ?? null,null,2);
  $('frame-note').textContent = selected?.note || 'Only a literal state included in the saved endpoint record is displayed.';
  if (!selected?.state || !Array.isArray(selected.state.t) || !Array.isArray(selected.state.m)) {
    $('point-state').append(el('p','No complete saved point state is supplied for this view.','empty')); return;
  }
  const state = selected.state;
  const marks = new Map(list(state.m).map(([p,v])=>[JSON.stringify(p),v]));
  const selectedRows = new Map(list(state.selected).map(key=>[key.translation?.[1],key]));
  const table = el('table'), head = el('thead'), hr = el('tr');
  for (const text of ['Row','Support / tile','Formula marking','Other layers']) hr.append(el('th',text));
  head.append(hr); table.append(head);
  const body = el('tbody');
  for (const [point,total] of list(state.t)) {
    if (!Array.isArray(point) || point[0] !== 0) continue;
    const row = point[1], tr = el('tr');
    tr.append(el('th',math(String(row))));
    const support = el('td'), key = selectedRows.get(row);
    support.append(el('span',math(String(total))));
    if (key) { const badge = el('span',ruleName(key),'tile-rule'); badge.title = 'Literal selected placement'; support.append(el('br'),badge); }
    tr.append(support);
    const value = marks.get(JSON.stringify([1,row]));
    const f = el('td',undefined,'formula-cell');
    if (Array.isArray(value) && value[0] === 'formula' && typeof value[1] === 'string') {
      try { f.append(el('span',math(formula(JSON.parse(value[1]))))); } catch (_) { f.textContent='Saved formula unavailable'; }
    } else f.textContent = value === undefined ? 'Unassigned' : JSON.stringify(value);
    tr.append(f);
    const layers = el('td',undefined,'layer-cell');
    for (const channel of [2,3,4]) {
      const v = marks.get(JSON.stringify([channel,row]));
      if (v === undefined) continue;
      const dot = el('span',undefined,'mark-dot ch'+channel+(v===0?' zero':''));
      dot.title = `Saved m at [${channel},${row}]: ${JSON.stringify(v)}`;
      dot.setAttribute('aria-label',dot.title); layers.append(dot,el('span',' '));
    }
    tr.append(layers); body.append(tr);
  }
  table.append(body); $('point-state').append(table);
  typeset([$('point-state')]).then(()=>{document.body.dataset.savedFrame=String(frame);});
}

async function showRun(index) {
  active=index; frame=0; const run=data.endpoints[index];
  $('run-select').value=String(index);
  document.querySelectorAll('.run-card').forEach((n,i)=>n.classList.toggle('active',i===index));
  $('run-summary').replaceChildren();
  card('Qualification',classification(run));
  card('Qualified cases',Number.isInteger(run.qualifiedCount) ? math(String(run.qualifiedCount)) : 'Not established');
  card('Native lifetime',typeof run.nativeSeconds === 'number' ? math(`${run.nativeSeconds.toFixed(6)}\\,\\mathrm{s}`) : 'Unavailable');
  card('Returned output',run.actualComplete===true ? 'Complete saved record' : 'No qualified complete record');
  $('run-scope').textContent=run.scope||'';
  $('controls').replaceChildren();
  for (const control of list(run.controls)) $('controls').append(el('li',`${control.case}: ${control.status}`));
  if (!list(run.controls).length) $('controls').append(el('li','No complete saved control outcomes are available.'));
  showTimeline(run);
  $('frame-select').replaceChildren();
  list(run.frames).forEach((v,i)=>{const option=el('option',v.label||'Saved state');option.value=String(i);$('frame-select').append(option);});
  $('frame-select').disabled=!list(run.frames).length;
  $('run-record').textContent=JSON.stringify(run.record??null,null,2);
  links($('run-links'),run.links);
  showFrame();
  await typeset([$('run-summary'),$('timeline')]);
  document.body.dataset.savedRun=run.id;
}

async function main() {
  const response=await fetch('report-data.json?v=e669993f35ae');
  if (!response.ok) throw new Error('Saved report unavailable');
  data=await response.json();
  if (!Array.isArray(data.endpoints) || !data.endpoints.length) throw new Error('No saved endpoint records');
  $('lead').textContent=data.lead;
  $('overall').textContent=data.overall;
  $('conclusion').textContent=data.conclusion;
  data.endpoints.forEach((run,i)=>{
    const option=el('option',run.title); option.value=String(i); $('run-select').append(option);
    const n=el('article',undefined,'run-card'); const button=el('button',run.title); button.addEventListener('click',()=>showRun(i));
    n.append(button,el('strong',classification(run),run.qualified===true?'qualified':'unqualified'));
    n.append(el('p',typeof run.nativeSeconds==='number'?math(`${run.nativeSeconds.toFixed(6)}\\,\\mathrm{s}`):'Native lifetime unavailable','caption'));
    $('run-cards').append(n);
  });
  $('run-select').addEventListener('change',event=>showRun(Number(event.target.value)));
  $('frame-select').addEventListener('change',event=>{frame=Number(event.target.value);showFrame();});
  links($('links'),data.links);
  const initial=data.endpoints.findIndex(r=>r.id==='child-UNKNOWN');
  await showRun(initial<0?0:initial);
  await typeset([$('lead'),$('overall'),$('run-cards'),$('scope')]);
  document.body.dataset.savedReaderReady='true';
}
main().catch(error=>{$('lead').textContent=error.message;$('overall').textContent='The saved report could not be loaded. No outcome is inferred.';document.body.dataset.savedReaderFailed='true';});
