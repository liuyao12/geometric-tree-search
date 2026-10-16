'use strict';
// Saved-data display only. This does not execute a proof or point checker.
const $ = id => document.getElementById(id);
const math = tex => `\\(${tex}\\)`;
const number = n => Number.isInteger(n) ? n.toLocaleString('en-US') : String(n);
const escTex = s => String(s).replace(/[\\{}_%&#$]/g, c => '\\' + c);
function term(t) {
  if (t[0] === 'var') return escTex(t[1]);
  const args = t[2].map(term);
  if (['0', 'zero'].includes(t[1]) && !args.length) return '0';
  if (['S', 'succ'].includes(t[1]) && args.length === 1) return `S(${args[0]})`;
  if (['+', 'add'].includes(t[1]) && args.length === 2) return `(${args[0]}+${args[1]})`;
  return `\\operatorname{${escTex(t[1])}}${args.length ? '(' + args.join(',') + ')' : ''}`;
}
function formula(f) {
  switch (f[0]) {
    case 'eq': return `${term(f[1])}=${term(f[2])}`;
    case 'pred': return `\\operatorname{${escTex(f[1])}}(${f[2].map(term).join(',')})`;
    case 'all': return `\\forall ${escTex(f[1])}\\;\\bigl(${formula(f[2])}\\bigr)`;
    case 'imp': return `\\bigl(${formula(f[1])}\\bigr)\\Rightarrow\\bigl(${formula(f[2])}\\bigr)`;
    case 'and': return `\\bigl(${formula(f[1])}\\bigr)\\land\\bigl(${formula(f[2])}\\bigr)`;
    case 'or': return `\\bigl(${formula(f[1])}\\bigr)\\lor\\bigl(${formula(f[2])}\\bigr)`;
    case 'not': return `\\neg\\bigl(${formula(f[1])}\\bigr)`;
    case 'bot': return '\\bot';
    default: throw new Error('Unknown saved formula constructor');
  }
}
function refs(command) {
  return command.rule === 'mp' ? [command.antecedent, command.implication]
    : command.rule === 'generalize' ? [command.source] : [];
}
function reading(command) {
  const r = command.rule;
  if (r === 'axiom') return `Use the original named axiom ${command.name}.`;
  if (r === 'assumption') return `Use occurrence ${number(command.index)} of the original hypothesis context.`;
  if (r === 'instantiate') return `License universal instantiation with ${math(escTex(command.universal[1]))} replaced by ${math(term(command.term))}. Applying this implication still requires modus ponens.`;
  if (r === 'eq_subst') return `License replacing ${math(term(command.left))} by ${math(term(command.right))} inside the displayed atomic context. The equality and original atomic statement are still required.`;
  if (r === 'mp') return `From rows ${number(command.antecedent + 1)} and ${number(command.implication + 1)}, apply the implication to its established antecedent.`;
  if (r === 'generalize') return `Generalize row ${number(command.source + 1)} over ${math(escTex(command.variable))}; that parameter is absent from every original undischarged hypothesis.`;
  return 'Unrecognized saved command.';
}
function addCard(parent, label, tex, detail) {
  const div = document.createElement('div'); div.className = 'card';
  const small = document.createElement('span'); small.className = 'eyebrow'; small.textContent = label;
  const strong = document.createElement('strong'); strong.textContent = math(tex);
  const note = document.createElement('span'); note.className = 'muted'; note.textContent = detail;
  div.append(small, strong, note); parent.append(div);
}
let mathQueue = Promise.resolve();
function typeset(nodes) {
  mathQueue = mathQueue.then(async () => {
    if (window.MathJax?.startup?.promise) {
      await MathJax.startup.promise;
      MathJax.typesetClear(nodes); await MathJax.typesetPromise(nodes);
    }
  });
  return mathQueue;
}
function cell(row, value, isMath = false) {
  const td = document.createElement('td'); td.textContent = isMath ? math(value) : value; row.append(td); return td;
}
function showBoard(board, commands) {
  if (!board) {
    $('board-intro').textContent = 'No full point board is accepted in these saved records. The converter and independent point checker have Source reviews only; the conditional correspondence argument below remains separate from runtime evidence.';
    return;
  }
  const packet = board.packet, receipt = board.receipt;
  $('board-intro').textContent = `The separate board stage reconstructs the complete saved primitive word into the original fixed-height boundary. Every physical row, unit contribution and marking occurrence is retained. Padding repeats the first zero-input primitive; it is not an additional mathematical argument.`;
  const cost = document.createElement('p'), bd = board.disposition;
  cost.textContent = `This separate cold verification stage, including fresh checks of both words and all malformed-packet controls, took ${math((bd.native_launch_to_postprobe_ns/1e9).toFixed(6)+'\\,\\mathrm{s}')} through the fresh postterminal observation, with ${math((bd.aggregate_B_bytes/1048576).toFixed(6)+'\\,\\mathrm{MiB}')} peak memory. It is an additional cost after proof discovery, not part of the search timing above.`;
  $('board-intro').after(cost);
  addCard($('board-stats'), 'Physical rows', number(receipt.tile_count), 'Every original boundary row is filled exactly once.');
  addCard($('board-stats'), 'Distinct marking points', number(receipt.marking_point_count), 'All fixed and active literal values agree.');
  addCard($('board-stats'), 'Mark occurrences', number(receipt.marking_occurrence_count), 'Repeated agreeing premise reads remain counted.');
  $('tile-inspector').hidden = false;
  const stripTitle = document.createElement('h3'); stripTitle.textContent = 'The selected tile’s actual remote reads';
  const pointStrip = document.createElement('div'); pointStrip.id = 'point-strip';
  const stripCaption = document.createElement('p'); stripCaption.className = 'caption';
  stripCaption.textContent = 'Every nonnegative physical row is shown. A teal ring is the selected tile’s premise marking meeting a purple output marking at the same point. Channels and rows are scaled independently for display; dashed connections illustrate the reach, not additional constraints. The complete outside sentinel is in the raw packet.';
  const legend = document.querySelector('#tile-inspector .legend'); legend.after(stripTitle,pointStrip,stripCaption);
  const controlDetail = document.createElement('details'), controlSummary = document.createElement('summary'), controlList = document.createElement('ul');
  controlSummary.textContent = 'All malformed-packet controls were rejected';
  for (const item of board.controls.controls) {const li=document.createElement('li');li.textContent=item.case+': '+item.observed.reason;controlList.append(li);}
  const controlNote=document.createElement('p');controlNote.className='caption';controlNote.textContent='These reject at complete independent reconstruction. The positive packet exercises the accumulator; negative accumulator-branch coverage is not claimed.';
  controlDetail.append(controlSummary,controlList,controlNote);$('tile-inspector').append(controlDetail);
  const select = $('tile-select');
  packet.tiles.forEach((tile, row) => {
    const option = document.createElement('option'); option.value = row;
    option.textContent = `Physical row ${row + 1}${row < packet.padding_rows ? ' · padding' : ' · proof row ' + (row - packet.padding_rows + 1)}`;
    select.append(option);
  });
  async function selectRow(row) {
    const tile = packet.tiles[row], cmd = packet.padded_commands[row];
    const showReads = $('show-inputs').checked, showOffsets = $('show-offsets').checked;
    $('tile-portrait').replaceChildren();
    const square = document.createElement('div'); square.className = 'tile-square';
    const center = document.createElement('span'); center.className = 'center'; center.textContent = math(String(row + 1)); square.append(center);
    for (const name of ['support', 'output', ...(showReads && refs(cmd).length ? ['input'] : []), ...(showOffsets && refs(cmd).length ? ['offset'] : [])]) {
      const dot = document.createElement('span'); dot.className = 'point ' + name; dot.title = name; square.append(dot);
    }
    if (showReads && refs(cmd).length) {const stem = document.createElement('span'); stem.className = 'remote-stem'; square.append(stem);}
    const cap = document.createElement('p'); cap.textContent = 'Schematic portrait of this actual tile. Full distances and values are listed alongside.';
    $('tile-portrait').append(square, cap);
    $('tile-title').textContent = `${row < packet.padding_rows ? 'Padding' : 'Proof'} tile · ${cmd.rule}`;
    $('tile-formula').textContent = '\\[' + formula(cmd.formula) + '\\]';
    $('tile-reading').textContent = reading(cmd);
    $('tile-ports').replaceChildren();
    if (showReads) refs(cmd).forEach((source, port) => {
      const li = document.createElement('li');
      li.textContent = `Ordered premise ${port + 1} reads physical row ${source + 1}: ` + math(formula(packet.padded_commands[source].formula)) + (showOffsets ? `; offset ${math(String(source - row))}.` : '.');
      $('tile-ports').append(li);
    });
    if (!refs(cmd).length) {const li = document.createElement('li'); li.textContent = 'This primitive has no premise ports.'; $('tile-ports').append(li);}
    $('tile-json').textContent = JSON.stringify(tile, null, 2);
    pointStrip.replaceChildren();
    const stripHead = document.createElement('div'); stripHead.className = 'strip-head';
    for (const label of ['r+1','t(0,r)','m(1,r)','m(2,r)','m(3,r)']) {const span = document.createElement('span'); span.textContent = math(label); stripHead.append(span);}
    const stripBody = document.createElement('div'); stripBody.className = 'strip-body';
    const selectedRefs = showReads ? refs(cmd) : [];
    for (let r=0;r<packet.height;r++) {
      const line = document.createElement('div'); line.className = 'strip-row' + (r === row ? ' current' : '');
      const label = document.createElement('span'); label.textContent = math(String(r+1)); line.append(label);
      for (let channel=0;channel<4;channel++) {
        const column = document.createElement('span');
        if (channel === 0 || channel === 1 || (showOffsets && r === row && channel-2 < refs(cmd).length)) {
          const mark = document.createElement('i');
          mark.className = 'strip-point ' + (channel === 0 ? 'unit' : channel === 1 ? 'formula' : 'offset')
            + (channel === 1 && selectedRefs.includes(r) ? ' read' : '')
            + (channel === 1 && r === packet.height-1 ? ' target' : '');
          if (r === row) mark.classList.add('chosen'); column.append(mark);
        }
        line.append(column);
      }
      stripBody.append(line);
    }
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox',`0 0 400 ${packet.height*28}`); svg.setAttribute('preserveAspectRatio','none'); svg.classList.add('strip-lines');
    svg.setAttribute('aria-label','Selected tile remote premise connections');
    selectedRefs.forEach((source, port) => {
      const path = document.createElementNS('http://www.w3.org/2000/svg','path');
      const reach = 220 + port*15, y = row*28+14, priorY = source*28+14;
      path.setAttribute('d',`M200 ${y} C${reach} ${y} ${reach} ${priorY} 200 ${priorY}`);
      path.setAttribute('fill','none');path.setAttribute('stroke','#178d82');path.setAttribute('stroke-width','2');path.setAttribute('stroke-dasharray','4 3');svg.append(path);
    });
    stripBody.append(svg); pointStrip.append(stripHead,stripBody);
    document.querySelectorAll('#proof-rows tr').forEach((tr, i) => tr.classList.toggle('selected', i === row - packet.padding_rows));
    await typeset([$('tile-portrait'), $('tile-formula'), $('tile-reading'), $('tile-ports'), pointStrip]);
  }
  select.addEventListener('change', () => selectRow(Number(select.value)));
  for (const id of ['show-inputs', 'show-offsets']) $(id).addEventListener('change', () => selectRow(Number(select.value)));
  packet.padded_commands.forEach((cmd, i) => {
    const row = document.createElement('div'); row.className = 'physical-row' + (i < packet.padding_rows ? ' padding' : '');
    const mini = document.createElement('div'); mini.className = 'mini'; mini.textContent = math(String(i + 1));
    const text = document.createElement('div'); const f = document.createElement('div'); f.textContent = math(formula(cmd.formula));
    const desc = document.createElement('span'); desc.className = 'desc'; desc.textContent = i < packet.padding_rows ? 'Repeated zero-input padding' : reading(cmd);
    text.append(f, desc); row.append(mini, text); $('physical-rows').append(row);
  });
  document.querySelectorAll('#proof-rows tr').forEach((tr, i) => tr.addEventListener('click', () => {
    select.value = i + packet.padding_rows; selectRow(i + packet.padding_rows); $('tiles').scrollIntoView({behavior:'smooth'});
  }));
  select.value = packet.height - 1; selectRow(packet.height - 1);
}
async function load() {
  const response = await fetch('report-data.json');
  if (!response.ok) throw new Error('Saved report data could not be loaded');
  const data = await response.json();
  $('headline').textContent = data.title;
  $('lead').textContent = data.lead;
  for (const c of data.summary) addCard($('summary'), c.label, c.tex, c.detail);
  $('result-intro').textContent = data.result_intro;
  data.attempts.forEach(attempt => {
    const d = attempt.disposition, row = document.createElement('tr');
    cell(row, attempt.name); cell(row, d.target_proof_accepted ? 'Checked positive word' : 'Unknown: ' + d.search_incompleteness.stop_reason);
    cell(row, (d.native_launch_to_postprobe_ns / 1e9).toFixed(6) + '\\,\\mathrm{s}', true);
    cell(row, (d.aggregate_B_bytes / 1048576).toFixed(6) + '\\,\\mathrm{MiB}', true);
    cell(row, d.complete_Date_seconds.toFixed(3) + '\\,\\mathrm{s}', true); $('attempts').append(row);
  });
  for (const text of data.comparison_notes) {const p = document.createElement('p'); p.textContent = text; $('comparison-notes').append(p);}
  $('counters').textContent = JSON.stringify(data.attempts.map(a => ({name:a.name,counters:a.proposal.counters,incompleteness:a.proposal.incompleteness})), null, 2);
  const commands = data.proof?.commands || [];
  $('proof-intro').textContent = commands.length ? `The complete automatically proposed primitive word is shown below. No proof word, donor library or theorem-specific intermediate sequence was supplied to the search. Select a row to inspect its physical tile when the separate board stage is available.` : 'No proof word was returned by these runs. There are no theorem-proof rows to display; an unknown result is preserved without an invented derivation.';
  commands.forEach((command, index) => {
    const row = document.createElement('tr'); cell(row, String(index + 1), true); cell(row, formula(command.formula), true);
    const td = cell(row, reading(command)); const tag = document.createElement('code'); tag.className = 'rule'; tag.textContent = command.rule; td.append(tag);
    $('proof-rows').append(row);
  });
  showBoard(data.board, commands);
  $('assessment-text').textContent = data.assessment;
  data.evidence.forEach(ref => {const li = document.createElement('li'), a = document.createElement('a'); a.href = ref.href; a.textContent = ref.label; li.append(a); $('evidence-links').append(li);});
  $('saved-data').textContent = JSON.stringify(data, null, 2);
  await typeset([document.querySelector('main')]);
  document.body.dataset.savedReaderReady = 'true';
}
load().catch(error => {$('lead').textContent = error.message; document.body.dataset.savedReaderError = 'true';});
