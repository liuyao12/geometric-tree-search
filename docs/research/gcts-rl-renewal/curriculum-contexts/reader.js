/* Display future ROOT-assembled saved records only. No search or proof oracle. */
'use strict';
(async function () {
  const order = ['donor-two-guards', 'donor-two-equalities', 'donor-repeated-guard',
    'donor-repeated-equality', 'heldout-mixed-guard-equality'];
  const names = ['Two guards', 'Two equalities', 'Repeated guard', 'Repeated equality',
    'Mixed guard and equality'];
  const escape = value => String(value).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const math = latex => '\\(' + escape(latex) + '\\)';
  const hasNumber = value => typeof value === 'number' && Number.isFinite(value);
  const count = value => hasNumber(value) ? math(String(value)) : 'Unavailable';
  const seconds = value => hasNumber(value) ? math(value.toFixed(9)) : 'Unavailable';
  const statusNames = {pending: 'Pending', prepared: 'Prepared; audit pending',
    accepted: 'Accepted', unknown: 'Unknown', failed: 'Failed', not_run: 'Not run'};
  const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const status = phase => {
    const value = phase && phase.status;
    return '<span class="status status-' + (own(statusNames, value) ? value : 'pending') +
      '">' + escape(own(statusNames, value) ? statusNames[value] : value || 'Pending') + '</span>' +
      (phase && safeHref(phase.artifact_href) ? '<span class="cell-note">' + link(phase.artifact_href, 'Saved phase record') + '</span>' : '');
  };
  const safeHref = value => typeof value === 'string' &&
    /^(?:evidence\/[A-Za-z0-9._/-]+|view\.json|origins\.json)(?:#[A-Za-z0-9_-]+)?$/.test(value) &&
    !value.split('/').includes('..') ? value : null;
  const link = (href, text) => {
    const safe = safeHref(href);
    return safe ? '<a href="' + escape(safe) + '">' + escape(text) + '</a>' : escape(text);
  };
  const qualification = phase => !phase || phase.root_resource_accepted === null ||
    phase.root_resource_accepted === undefined ? 'Unavailable' :
    phase.root_resource_accepted === true ? 'Qualified by ROOT receipt' : 'Unqualified';
  const capacityNames = {pending: 'Pending', within: 'Within frozen capacity',
    exceeded: 'Exceeds capacity; RL unresolved', unresolved: 'Unresolved'};
  const formula = item => item && typeof item.latex === 'string' ? math(item.latex) : 'Formula unavailable';
  const data = await fetch('view.json').then(response => {
    if (!response.ok) throw new Error('ROOT saved view is not available yet');
    return response.json();
  });
  // Presentation shape check only. This is not context, theorem or inventory acceptance.
  if (data.schema !== 'ROOT-assembled-frozen-curriculum-context-reader-v1' ||
      !Array.isArray(data.contexts) || data.contexts.length !== order.length ||
      data.contexts.some((context, i) => context.id !== order[i])) {
    throw new Error('Display record does not contain the exact ordered five-context schema');
  }
  const grid = document.getElementById('context-grid');
  grid.innerHTML = data.contexts.map((context, index) => {
    const hypotheses = Array.isArray(context.hypotheses) ? context.hypotheses : [];
    return '<article class="context-card"><div class="context-tag ' +
      (context.partition === 'heldout' ? 'heldout' : '') + '">' +
      math(index + 1) + ' · ' + escape(context.partition) + '</div><h3>' + names[index] + '</h3>' +
      hypotheses.map(item => '<div class="hypothesis"><span class="occurrence">Occurrence ' +
        count(item.occurrence_index) + ' · seed row ' + count(item.row) +
        (hasNumber(item.duplicate_of_index) ? ' · same formula as occurrence ' + count(item.duplicate_of_index) : '') +
        '</span>' + formula(item) + '</div>').join('') +
      '<div class="target-box"><span class="occurrence">Target at row ' + count(context.target && context.target.row) +
      '</span>' + formula(context.target) + '</div><p class="context-meta">' + escape(context.id) + '</p></article>';
  }).join('');
  if (typeof data.guard_definition_latex === 'string') {
    document.getElementById('guard-definition').innerHTML = math(data.guard_definition_latex);
  }
  document.getElementById('gate-rows').innerHTML = data.contexts.map((context, index) => {
    const inventory = context.inventory || {};
    const groups = inventory.complete_cluster_group_count;
    const capacity = inventory.capacity;
    const percentage = hasNumber(groups) && hasNumber(capacity) && capacity > 0 ?
      Math.max(0, Math.min(100, 100 * groups / capacity)) : 0;
    const capacityState = inventory.capacity_status;
    const audit = context.static_gate || {};
    const inventoryAcceptance = audit.context_inventory_accepted === true ? 'Accepted' :
      audit.context_inventory_accepted === false ? 'Not accepted' : 'Unavailable';
    const note = '<span class="cell-note">Context/inventory: ' + inventoryAcceptance +
      (typeof audit.note === 'string' ? '<br>' + escape(audit.note) : '') + '</span>';
    return '<tr><td>' + names[index] + '<span class="cell-note">' + escape(context.partition) + '</span></td><td>' +
      status(context.preparation) + '</td><td>' + status(audit) + note + '</td><td>' +
      count(inventory.initial_primitive_candidate_count) + '</td><td>' + count(groups) + ' / ' + count(capacity) +
      '<div class="capacity-bar" aria-hidden="true"><div class="capacity-fill ' +
      (capacityState === 'exceeded' ? 'exceeded' : '') + '" style="width:' + percentage + '%"></div></div></td><td>' +
      escape(own(capacityNames, capacityState) ? capacityNames[capacityState] : capacityState || 'Pending') + '</td><td>' +
      count(inventory.complete_body_count) + '</td></tr>';
  }).join('');
  document.getElementById('cost-rows').innerHTML = data.contexts.map((context, index) => {
    const prep = context.preparation || {};
    const audit = context.static_gate || {};
    return '<tr><td>' + names[index] + '</td><td>' + seconds(prep.root_full_owned_seconds) + '</td><td>' +
      seconds(audit.root_full_owned_seconds) + '</td><td>' + count(prep.peak_estimate_bytes) + '</td><td>' +
      count(audit.peak_estimate_bytes) + '</td><td><span class="cell-note">Preparation: ' +
      escape(qualification(prep)) + '<br>Static gate: ' + escape(qualification(audit)) + '</span></td></tr>';
  }).join('');
  const costs = data.costs || {};
  document.getElementById('cost-subtotal').innerHTML = hasNumber(costs.phase_subtotal_seconds) ?
    'ROOT-recorded preparation/static phase subtotal: ' + seconds(costs.phase_subtotal_seconds) + ' seconds.' :
    'No complete actual phase subtotal supplied.';
  if (typeof costs.scope === 'string' || typeof costs.additional_cost_note === 'string') {
    document.getElementById('cost-scope').textContent = [costs.scope, costs.additional_cost_note]
      .filter(value => typeof value === 'string').join(' ');
  }
  const progress = data.progress || {};
  document.getElementById('phase-progress').innerHTML = 'ROOT-recorded phase counters: new proofs ' +
    count(progress.new_proofs) + '; training episodes ' + count(progress.training_episodes) +
    '; sampled RNG draws ' + count(progress.RNG_draws) + '; native proof queries ' + count(progress.native_queries) + '.';
  const evidence = Array.isArray(data.evidence) ? data.evidence : [];
  const links = evidence.map(item => link(item.href, item.label));
  links.unshift(link('view.json', 'ROOT-assembled display view'));
  document.getElementById('evidence-links').innerHTML = links.join(' · ');
  const select = document.getElementById('context-select');
  select.innerHTML = data.contexts.map((context, index) => '<option value="' + index + '">' + names[index] + '</option>').join('');
  select.disabled = false;
  const showRaw = () => {
    document.getElementById('raw-context').textContent = JSON.stringify(data.contexts[Number(select.value)], null, 2);
  };
  select.addEventListener('change', showRaw);
  showRaw();
  document.getElementById('load-status').textContent = typeof data.status_note === 'string' ?
    data.status_note : 'Saved context records loaded. Gate dispositions are reproduced from ROOT data.';
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
  document.getElementById('load-status').textContent = 'Saved context view unavailable: ' + String(error) +
    '. No outcomes have been substituted.';
});
