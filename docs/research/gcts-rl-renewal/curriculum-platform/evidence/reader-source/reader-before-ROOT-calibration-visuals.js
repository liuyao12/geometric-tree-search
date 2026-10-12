/* Display ROOT-supplied saved platform evidence only. No process or scientific call. */
'use strict';
(async function () {
  const escape = value => String(value).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const math = value => '\\(' + escape(value) + '\\)';
  const numeric = value => typeof value === 'number' && Number.isFinite(value);
  const number = value => numeric(value) ? math(String(value)) : 'Unavailable';
  const seconds = value => numeric(value) ? math(value.toFixed(9)) : 'Unavailable';
  const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const states = {pending: 'Pending', not_run: 'Not run', pass: 'Raw checks passed',
    accepted: 'Accepted', unknown: 'Unknown', failed: 'Failed'};
  const status = value => '<span class="status status-' + (own(states, value) ? value : 'pending') +
    '">' + escape(own(states, value) ? states[value] : value || 'Pending') + '</span>';
  const safeHref = value => typeof value === 'string' &&
    /^(?:evidence\/[A-Za-z0-9._/-]+|view\.json|origins\.json)(?:#[A-Za-z0-9_-]+)?$/.test(value) &&
    !value.split('/').includes('..') ? value : null;
  const link = (href, label) => safeHref(href) ? '<a href="' + escape(href) + '">' + escape(label) + '</a>' :
    escape(label || 'No evidence link');
  const data = await fetch('view.json').then(response => {
    if (!response.ok) throw new Error('ROOT saved platform view is not available yet');
    return response.json();
  });
  if (data.schema !== 'ROOT-assembled-curriculum-platform-reader-v1') {
    throw new Error('Unsupported display schema');
  }
  const actors = Array.isArray(data.actors) ? data.actors : [];
  const roles = {scientific_worker: 'Scientific worker', owner: 'Owner',
    dispatcher: 'Dispatcher', launcher: 'Launcher', leaf_observer: 'Leaf observer'};
  const roleKeys = Object.keys(roles);
  roles.calibration_worker = 'Calibration worker (non-scientific)';
  roleKeys.forEach(role => {
    const saved = actors.filter(actor => actor.role === role);
    document.getElementById(role).innerHTML = saved.length ? saved.map(actor =>
      escape(actor.label) + ': PID ' + number(actor.pid) +
      (typeof actor.scope_note === 'string' ? ' · ' + escape(actor.scope_note) : '')).join('<br>') :
      'No saved actor record supplied.';
  });
  document.getElementById('actor-rows').innerHTML = actors.length ? actors.map(actor =>
    '<tr><td>' + escape(actor.label) + '</td><td>' + escape(own(roles, actor.role) ? roles[actor.role] : actor.role) +
    '</td><td>' + number(actor.pid) + '</td><td>' + number(actor.parent_pid) +
    '</td><td>' + escape(actor.scope_note || 'Scope unavailable') + '</td><td>' +
    link(actor.evidence_href, 'Saved actor scope') + '</td></tr>').join('') :
    '<tr><td colspan="6">No actual actor records supplied.</td></tr>';
  const memory = Array.isArray(data.memory_observations) ? data.memory_observations : [];
  document.getElementById('memory-rows').innerHTML = memory.length ? memory.map(item =>
    '<tr><td>' + escape(item.label) + '</td><td>' + escape(item.method) + '</td><td>' +
    number(item.value_bytes) + '</td><td>' + number(item.original_value) + ' ' +
    escape(item.original_unit || 'Unit unavailable') + '</td><td>' +
    escape(item.scope_note || 'Scope unavailable') + '</td><td>' +
    link(item.evidence_href, 'Saved observation') + '</td></tr>').join('') :
    '<tr><td colspan="6">No actual memory observations supplied.</td></tr>';
  const phases = Array.isArray(data.phases) ? data.phases : [];
  document.getElementById('gate-rows').innerHTML = phases.length ? phases.map(phase =>
    '<tr><td>' + escape(phase.label) + '<span class="cell-note">' + escape(phase.version || 'Version unavailable') +
    '</span></td><td>' + status(phase.semantic_status) + '</td><td>' + status(phase.resource_status) +
    '</td><td>' + seconds(phase.root_full_owned_seconds) + '</td><td>' +
    escape(phase.disposition_note || 'No complete disposition supplied') + '</td><td>' +
    link(phase.evidence_href, 'Saved phase receipt') + '</td></tr>').join('') :
    '<tr><td colspan="6">No actual phase dispositions supplied.</td></tr>';
  const milestone = data.milestone || {};
  const calibration = milestone.calibration || {};
  const donor = milestone.next_donor || {};
  document.getElementById('calibration-status').innerHTML = status(calibration.status);
  document.getElementById('donor-status').innerHTML = status(donor.status);
  if (typeof calibration.note === 'string') document.getElementById('calibration-note').textContent = calibration.note;
  if (typeof donor.note === 'string') document.getElementById('donor-note').textContent = donor.note;
  const basis = milestone.claim_basis;
  const suppliedBasis = basis === 'actual_calibration' || basis === 'new_unexecuted_donor_progress' ||
    basis === 'both';
  document.getElementById('milestone-disposition').textContent = milestone.ROOT_qualified === true && suppliedBasis ?
    'ROOT-recorded milestone basis: ' + basis.replaceAll('_', ' ') + '. ' + (milestone.note || '') :
    'No qualified milestone claim supplied. ' + (milestone.note || 'Actual calibration and/or new donor evidence is required.');
  const evidence = Array.isArray(data.evidence) ? data.evidence : [];
  document.getElementById('evidence-links').innerHTML = [link('view.json', 'ROOT-assembled display view')]
    .concat(evidence.map(item => link(item.href, item.label))).join(' · ');
  document.getElementById('raw-view').textContent = JSON.stringify(data, null, 2);
  document.getElementById('load-status').textContent = typeof data.status_note === 'string' ? data.status_note :
    'Saved display records loaded. Semantic and resource dispositions remain separately labeled.';
  let typeset = Promise.resolve();
  function renderMath() {
    if (window.MathJax && window.MathJax.typesetPromise) {
      typeset = typeset.then(() => window.MathJax.typesetPromise()).catch(error => {
        document.getElementById('load-status').dataset.mathError = String(error);
      });
    }
  }
  window.addEventListener('load', renderMath, {once: true});
  renderMath();
})().catch(error => {
  document.getElementById('load-status').textContent = 'Saved platform view unavailable: ' + String(error) +
    '. No observations or outcomes have been substituted.';
});
