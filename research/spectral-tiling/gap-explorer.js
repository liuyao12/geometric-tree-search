'use strict';
(() => {
  const raw = document.getElementById('gap-data');
  const select = document.getElementById('gap-select');
  const detail = document.getElementById('gap-detail');
  if (!raw || !select || !detail) return;
  const {gaps} = JSON.parse(raw.textContent);
  const math = value => '\\(' + value + '\\)';
  const queue = {promise: Promise.resolve()};
  gaps.forEach((gap, index) => {
    const option = document.createElement('option');
    option.value = String(index);
    option.textContent = `Gap ${index + 1} · ${gap.status}`;
    select.appendChild(option);
  });
  function renderGap() {
    if (window.MathJax?.typesetClear) window.MathJax.typesetClear([detail]);
    const gap = gaps[Number(select.value)];
    const a = gap.left_q, b = gap.right_q;
    const values = gap.fine_interior_normalized_estimates;
    const ready = gap.status === 'refinement-stable estimate';
    const count = gap.counts_by_refinement['4'];
    const lo = Math.min(a, ...values), hi = Math.max(b, ...values);
    const span = hi - lo;
    const position = value => 4 + 92 * (value - lo) / span;
    let points = `<span class="gap-point anchor" style="left:${position(a)}%" aria-hidden="true"></span>`;
    points += `<span class="gap-point anchor" style="left:${position(b)}%" aria-hidden="true"></span>`;
    values.forEach((value, i) => {
      const outside = !(a < value && value < b);
      points += `<span class="gap-point" style="left:${position(value)}%;${outside ? 'background:#b58442' : ''}" title="Mode ${gap.fine_interior_ranks[i]}; see table below" aria-hidden="true"></span>`;
    });
    let rows = '';
    values.forEach((value, i) => {
      const margin = Math.min(value - a, b - value);
      const movement = gap.last_refinement_absolute_changes[i];
      const caution = margin <= movement;
      rows += `<tr><td>${math(gap.fine_interior_ranks[i])}</td><td>${math(value.toFixed(6))}</td><td>${math(movement.toFixed(6))}</td><td${caution ? ' class="pending"' : ''}>${caution ? 'Endpoint needs resolution' : 'Inside, at current resolution'}</td></tr>`;
    });
    detail.innerHTML = `<h3>${math(`${a}\\pi^2 < \\lambda < ${b}\\pi^2`)}</h3>` +
      `<p${ready ? '' : ' class="pending"'}>${ready ? 'Estimated intervening count: ' + math(count) + ', including multiplicity.' : 'Count pending. Rank tracking gives ' + math(count) + ' candidate modes, but the endpoint checks are unresolved.'}</p>` +
      `<p class="small">Constructed multiplicities at the left and right endpoints are at least ${math(gap.left_constructed_multiplicity)} and ${math(gap.right_constructed_multiplicity)}. Endpoint modes are excluded from the count.</p>` +
      `<div class="gap-track">${points}</div><div class="gap-labels"><span>${math(a)}</span><span>${math(b)}</span></div>` +
      `<p class="gap-legend">Squares: exact ladder endpoints. Dots: numerical estimates of intervening modes. The table retains every mode when dots overlap.</p>` +
      (values.length ? `<div class="scroll"><table><thead><tr><th>Mode index</th><th>${math('\\lambda/\\pi^2')}</th><th>Last-refinement movement</th><th>Endpoint check</th></tr></thead><tbody>${rows}</tbody></table></div>` : '<p>No intervening modes appear at the current resolution.</p>') +
      '<p class="small">This is a numerical observation. The algebraicity of other normalized eigenvalues is unknown.</p>';
    if (window.MathJax?.startup?.promise) {
      queue.promise = queue.promise.then(() => window.MathJax.startup.promise)
        .then(() => window.MathJax.typesetPromise([detail])).catch(error => {
          console.error('Gap explorer math rendering failed', error);
        });
    }
  }
  select.addEventListener('change', renderGap);
  renderGap();
})();
