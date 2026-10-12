/* Display saved observations only. This code runs no search or proof checker. */
'use strict';
(async function () {
  const data = await fetch('trace-view.json').then(response => {
    if (!response.ok) throw new Error('Saved display record unavailable');
    return response.json();
  });
  const selector = document.getElementById('case-select');
  const range = document.getElementById('event-range');
  const board = document.getElementById('rows');
  const wires = document.getElementById('wires');
  const note = document.getElementById('event-note');
  const hint = document.getElementById('hint-line');
  const facts = document.getElementById('fact-line');
  const escape = value => String(value).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const math = latex => '\\(' + latex + '\\)';
  const formulas = ['P', 'Q', 'P\\Rightarrow Q', 'C'];
  const labels = {
    initial_snapshot: 'Initial engine state', prepare: 'Prepare the complete proposal menu',
    choose: 'Validate and select continuation order', primitive_apply: 'Place one primitive tile',
    controller_resync: 'Revalidate every registered cluster',
    overlay_after_resync: 'Update the active proposal after revalidation',
    available_facts: 'Read dependency-complete fixture outputs',
    checkpoint: 'Save a paired checkpoint', paired_rollback: 'Restore the paired checkpoint',
    invalid_registration: 'Reject a changed whole cluster',
    zero_attempt_unknown: 'Return unknown with no exclusion',
    prepare_rejected_global_dead: 'Reject proposal preparation at a global dead end',
    explicit_negative_weight_mutation: 'Apply an intentional invalid weight change'
  };
  let typeset = Promise.resolve();
  function renderMath() {
    if (window.MathJax && window.MathJax.typesetPromise) {
      typeset = typeset.then(() => window.MathJax.typesetPromise([board, note, hint, facts,
        document.getElementById('event-position')])).catch(error => {
        note.dataset.mathError = String(error);
      });
    }
  }
  function draw() {
    if (window.MathJax && window.MathJax.typesetClear) {
      window.MathJax.typesetClear([board, note, hint, facts, document.getElementById('event-position')]);
    }
    const record = data.cases.find(item => item.id === selector.value);
    const index = Math.max(0, Math.min(record.events.length - 1, Number(range.value)));
    const event = record.events[index];
    range.max = record.events.length - 1;
    range.value = index;
    document.getElementById('previous').disabled = index === 0;
    document.getElementById('next-step').disabled = index === record.events.length - 1;
    document.getElementById('event-position').innerHTML = 'Saved event ' + math(index) + ' of ' + math(record.events.length - 1);
    const [kind, row, count, generation] = event.decision;
    note.innerHTML = '<strong>' + escape(labels[event.op] || event.op) + '.</strong> ' +
      (event.error ? 'Rejected: ' + escape(event.error.message) + '. ' : '') +
      'Next global decision: ' + escape(kind) + (row === null ? '' : ' at ' + math('r_{' + row + '}') +
      ', ' + math('d=' + count) + ', generation ' + math(generation)) + '.';
    const selected = new Map(event.order.map(key => [key[1], key]));
    const markValues = new Map(event.marks.map(mark => [mark[0] + ',' + mark[1], mark[2]]));
    board.innerHTML = event.totals.map((total, rowIndex) => {
      const key = selected.get(rowIndex);
      const code = markValues.get('1,' + rowIndex);
      const output = code === undefined ? 'No assigned formula' :
        math(formulas[code] === undefined ? '\\mathrm{code}\\,' + code : formulas[code]);
      const recipe = key ? data.recipes[key[0]].id : 'Empty required point';
      return '<div class="row-card"><div class="row-label">' + math('r_{' + rowIndex + '}') +
        ' · ' + math('d=' + event.domains[rowIndex]) + '</div><div class="tile ' + (total ? 'filled' : 'empty') +
        '"><div>' + math('t=' + total) + '</div><div class="formula-mark">' + output + '</div>' +
        (key && key[2].length ? '<i class="port port-a"></i><i class="port port-b"></i>' : '') +
        '</div><div class="key-label">' + escape(recipe) + '</div></div>';
    }).join('');
    const links = [];
    event.order.forEach(key => key[2].forEach((source, port) => {
      const start = (key[1] + 0.5) * 150 + (port ? 12 : -12);
      const end = (source + 0.5) * 150;
      const level = 35 + port * 30;
      const color = port ? '#438c78' : '#c58530';
      links.push('<path d="M' + start + ',0 V' + level + ' H' + end + ' V0" fill="none" stroke="' + color +
        '" stroke-width="2.5"><title>' + escape('Ordered source port ' + (port + 1) + ', offset ' + (source - key[1])) +
        '</title></path><circle cx="' + end + '" cy="0" r="4" fill="' + color + '"/>');
    }));
    wires.innerHTML = links.join('');
    hint.innerHTML = event.hints.length ? event.hints.map((value, i) => {
      const descriptor = record.descriptors[i];
      const active = descriptor.descriptor_id === event.active_id;
      return escape(descriptor.body_name) + ': <strong class="status-' + escape(value.status) + '">' +
        escape(value.status) + '</strong>' + (active ? ' · active selection' : '');
    }).join(' | ') : 'No cluster is registered in this case; the primitive domains remain complete.';
    hint.innerHTML += ' · paired trail depths: ' + math('(' + event.trails.graph + ',' + event.trails.controller + ',' + event.trails.overlay + ')') + '.';
    facts.innerHTML = event.recorded_fact_sample ? 'Recorded dependency-complete fixture potential: ' +
      math('F=' + event.recorded_fact_sample.fact_potential) + '. This value comes from the accepted saved operation; assigned marks on pending sources do not count.' :
      'No fact-potential sample is recorded at this operation. An assigned output mark or occupied row alone does not establish dependency completeness.';
    document.getElementById('raw-event').textContent = JSON.stringify(event, null, 2);
    renderMath();
  }
  selector.innerHTML = data.cases.map(record => '<option value="' + escape(record.id) + '">' +
    escape(record.id.replaceAll('-', ' ')) + '</option>').join('');
  selector.value = 'pending-source-not-fact';
  selector.addEventListener('change', () => { range.value = 0; draw(); });
  range.addEventListener('input', draw);
  document.getElementById('previous').addEventListener('click', () => { range.value = Number(range.value) - 1; draw(); });
  document.getElementById('next-step').addEventListener('click', () => { range.value = Number(range.value) + 1; draw(); });
  window.addEventListener('load', renderMath, {once: true});
  draw();
})().catch(error => {
  document.getElementById('event-note').textContent = 'Saved record could not be displayed: ' + String(error);
});
