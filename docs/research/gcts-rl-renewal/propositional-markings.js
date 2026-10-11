'use strict';
(() => {
  const el = id => document.getElementById(id);
  const escape = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const latex = f => f[0] === 'pred' ? f[1] : '(' + latex(f[1]) + '\\Rightarrow ' + latex(f[2]) + ')';
  const math = s => '\\(' + s + '\\)';
  let data, queue = Promise.resolve();
  const typeset = nodes => {
    queue = queue.then(async () => {
      if (window.MathJax && window.MathJax.startup) {
        await window.MathJax.startup.promise;
        await window.MathJax.typesetPromise(nodes);
      }
    }).catch(error => { el('load-status').textContent = 'Math typesetting failed: ' + error.message; });
    return queue;
  };
  function picture(a) {
    const parts = ['<defs><marker id="blue-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10" fill="#357bad"/></marker><marker id="orange-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10" fill="#c66c3b"/></marker></defs>'];
    const y = slot => 65 + 120 * slot;
    for (const row of data.proof) {
      const cy = y(row.slot), bad = row.slot === 2 && a.status !== 'compatible';
      parts.push('<text x="25" y="' + (cy + 5) + '" fill="#65716a">Line ' + (row.slot + 1) + '</text>');
      parts.push('<rect x="130" y="' + (cy - 30) + '" width="60" height="60" fill="#e5eddc" stroke="#23856b" stroke-width="2"/><text x="160" y="' + (cy + 5) + '" text-anchor="middle">C</text>');
      parts.push('<rect x="255" y="' + (cy - 30) + '" width="60" height="60" fill="' + (bad ? '#f5dfdd' : '#e5eddc') + '" stroke="' + (bad ? '#aa4650' : '#23856b') + '" stroke-width="2"/><text x="285" y="' + (cy + 5) + '" text-anchor="middle">G</text>');
      parts.push('<path d="M190 ' + cy + ' L255 ' + cy + '" stroke="#b98528" stroke-width="4" fill="none"/>');
      parts.push('<path d="M315 ' + cy + ' L455 ' + cy + '" stroke="#8654a0" stroke-width="2" fill="none"/><text x="455" y="' + (cy - 19) + '" fill="#65716a">Formula port · all bytes</text>');
      row.formula_word.forEach((v, k) => parts.push('<circle cx="' + (465 + k * 5.3) + '" cy="' + cy + '" r="2.2" fill="#8654a0" data-slot="' + row.slot + '" data-byte="' + k + '" data-value="' + v + '"><title>' + escape('slot ' + row.slot + ', byte ' + k + ', value ' + v + (v === 256 ? ' (terminator)' : '')) + '</title></circle>'));
    }
    const dashed = a.status === 'compatible' ? '' : ' stroke-dasharray="6 5"';
    parts.push('<path d="M305 275 C780 275 820 ' + y(a.antecedent) + ' 518 ' + y(a.antecedent) + '" stroke="#357bad" stroke-width="3" fill="none" marker-end="url(#blue-arrow)"' + dashed + '/>');
    parts.push('<path d="M315 298 C865 350 865 ' + (y(a.implication) + 9) + ' 518 ' + y(a.implication) + '" stroke="#c66c3b" stroke-width="3" fill="none" marker-end="url(#orange-arrow)"' + dashed + '/>');
    parts.push('<text x="130" y="375" fill="#65716a">C: command · G: inference guard · fixed orientation</text>');
    el('marking-picture').innerHTML = parts.join('');
  }
  function render() {
    const a = data.alternatives.find(r => r.antecedent === Number(el('antecedent-control').value) && r.implication === Number(el('implication-control').value));
    el('result').classList.toggle('rejected', a.status !== 'compatible');
    el('result').dataset.status = a.status;
    const requiredA = data.proof[1].command.formula, requiredB = data.proof[0].command.formula;
    let body = '<h3>' + (a.status === 'compatible' ? 'The markings agree.' : 'This attachment is rejected.') + '</h3>';
    body += '<p>The guard requires ' + math(latex(requiredA)) + ' at line ' + (a.antecedent + 1) + ' and ' + math(latex(requiredB)) + ' at line ' + (a.implication + 1) + '.</p>';
    if (a.status === 'compatible') body += '<p>Both complete formula words match, so modus ponens can produce ' + math('Q') + '.</p>';
    else if (a.status === 'internally_inconsistent_guard') body += '<p>Both inputs name the same line. The guard would assign two different complete formula words at the same port, so no internally compatible guard exists.</p>';
    else {
      const c = a.conflicts[0];
      body += '<p>At the first conflicting point ' + math('(' + c.point.join(',') + ')') + ', the earlier row assigns ' + math(String(c.assigned)) + ' but the guard requires ' + math(String(c.required)) + '. One unequal value already rejects this guard.</p>';
    }
    el('result').innerHTML = body;
    picture(a);
    el('exact-values').textContent = JSON.stringify({context:data.context, proposal:a, formula_ports:data.proof.map(r => ({slot:r.slot, formula:r.command.formula, word:r.formula_word, points:r.formula_word.map((value,k) => ({point:[4*r.slot,100+k],value}))})), actual_discovered_guards:data.proof.map(r => r.guard_tile)},null,2);
    return typeset([el('result')]);
  }
  async function start() {
    const response = await fetch('propositional-markings-note-001.json?v=20261011-pm1');
    if (!response.ok) throw new Error('Evidence request returned ' + response.status);
    data = await response.json();
    const prose = ['Given: if ' + math('P') + ' holds, ' + math('Q') + ' follows.', 'Given: ' + math('P') + ' holds.', 'From lines 2 and 1, conclude ' + math('Q') + ' by modus ponens.'];
    el('proof-lines').innerHTML = data.proof.map((r,i) => '<div class="logic-row"><span class="small">Line ' + (i+1) + '</span><p class="formula">' + math(latex(r.command.formula)) + '</p><p>' + prose[i] + '</p></div>').join('');
    el('provenance').textContent = JSON.stringify({role:data.role, native_result:data.native_result, request_sha256:data.request_sha256, original_metrics:data.original_metrics, actual_placement_order:data.actual_placement_order, key_fields:['logical slot (zero-based)','command 0 / guard 1','command catalog index','guard variant'],source_files:data.source_files,scope:data.scope},null,2);
    el('validation-summary').innerHTML = 'The recorded inventory contains ' + math(String(data.validation.original_placements)) + ' original placements. The discovered exact region uses ' + math(String(data.validation.exact_solution_placements)) + ' placements for three logical lines. Of the ' + math('4') + ' earlier-reference pairs for the last line, exactly ' + math('1') + ' is compatible in this diagnostic context.';
    el('antecedent-control').addEventListener('change',render);
    el('implication-control').addEventListener('change',render);
    el('load-status').textContent = 'Recorded native acceptance and exact point data loaded. Change either source to inspect a rejected attachment.';
    await typeset([el('proof-lines'),el('validation-summary')]);
    await render();
    document.documentElement.dataset.noteReady = 'true';
  }
  start().catch(error => { el('load-status').textContent = 'Could not load proof evidence: ' + error.message; });
})();
