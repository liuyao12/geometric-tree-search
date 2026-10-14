'use strict';
(async () => {
  const response = await fetch('summary.json');
  if (!response.ok) throw new Error('Saved reader data unavailable');
  const data = await response.json();
  const byId = id => document.getElementById(id);
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const symbol = name => /^[A-Za-z]$/.test(name) ? name : String.raw`\mathit{${String(name).replace(/_/g, String.raw`\_`)}}`;
  const term = value => {
    if (value[0] === 'var') return symbol(value[1]);
    if (value[0] !== 'fun') throw new Error('Unsupported saved term');
    if (!value[2].length) return symbol(value[1]);
    return String.raw`\operatorname{${value[1]}}\left(${value[2].map(term).join(',')}\right)`;
  };
  const formula = value => {
    switch (value[0]) {
      case 'eq': return `${term(value[1])}=${term(value[2])}`;
      case 'pred': return String.raw`\operatorname{${value[1]}}\left(${value[2].map(term).join(',')}\right)`;
      case 'imp': return String.raw`\left(${formula(value[1])}\right)\to\left(${formula(value[2])}\right)`;
      case 'and': return String.raw`\left(${formula(value[1])}\right)\land\left(${formula(value[2])}\right)`;
      case 'or': return String.raw`\left(${formula(value[1])}\right)\lor\left(${formula(value[2])}\right)`;
      case 'not': return String.raw`\neg\left(${formula(value[1])}\right)`;
      case 'all': return String.raw`\forall ${symbol(value[1])}\,\left(${formula(value[2])}\right)`;
      default: throw new Error('Unsupported saved formula');
    }
  };
  const math = value => String.raw`\(${value}\)`;
  const num = (value, places = 3, unit = '') => math(Number(value).toFixed(places) + (unit ? String.raw`\,\mathrm{${unit}}` : ''));
  const caseName = id => id === 'fresh-inc-point-chain-w' ? 'First argument' : 'Second argument';
  const laneName = lane => lane === 'canonical' ? 'Canonical' : 'Incidence adviser';
  const originName = origin => origin === 'actual_selected' ? 'Checked selected ancestry' : 'Checked compatible proposal';
  const typeset = async root => {
    if (window.MathJax?.startup?.promise) await window.MathJax.startup.promise;
    if (window.MathJax?.typesetPromise) await window.MathJax.typesetPromise([root]);
  };
  byId('status').textContent = 'Four trials closed: three checked derivations of two statements; one preserved UNKNOWN. No RL or complete-board result.';
  byId('trials').innerHTML = '<table><thead><tr><th>Statement / lane</th><th>Logical outcome</th><th>Placements</th><th>Inner search / checking</th><th>Cold owned phase</th><th>Caller, with margin</th><th>Peak</th></tr></thead><tbody>' + data.trials.map(t => `<tr><td>${caseName(t.selector)} / ${laneName(t.lane)}</td><td><span class="outcome ${t.accepted ? '' : 'unknown'}">${t.accepted ? originName(t.origin_kind) : 'UNKNOWN: trace ceiling'}</span></td><td>${math(t.placements)}</td><td>${num(t.search_seconds,6,'s')}</td><td>${num(t.owned_postwrite_seconds,6,'s')}</td><td>${num(t.caller_seconds_with_margin,3,'s')}</td><td>${num(t.conservative_peak_bytes/1048576,2,'MiB')}</td></tr>`).join('') + '</tbody></table>';
  const adviser = data.trials.filter(t => t.adviser_work);
  byId('adviser-work').innerHTML = '<details><summary>Inspect the adviser’s charged work</summary><table><thead><tr><th>Statement</th><th>Licences / formula heads scanned</th><th>Heap pops</th><th>Eligible roots retained</th><th>Proposals checked</th><th>Construction time</th></tr></thead><tbody>' + adviser.map(t => `<tr><td>${caseName(t.selector)}</td><td>${math(t.adviser_work.all_licenses_scanned)} / ${math(t.adviser_work.atomic_formula_heads_scanned)}</td><td>${math(t.adviser_work.heap_pops)}</td><td>${math(t.adviser_work.eligible_seed_consuming_roots)}</td><td>${math(t.proposals_scanned)}</td><td>${num(t.adviser_work.total_construction_call_seconds,6,'s')}</td></tr>`).join('') + '</tbody></table><p>Minimum-tree witnesses are incomplete ordering advice. The full primitive fallback remains available; no target-specific symbolic selection or learned inventory was used.</p></details>';
  byId('raw-links').innerHTML = '<details><summary>Whole raw evidence for every trial</summary><ul>' + data.trials.map(t => `<li>${caseName(t.selector)} / ${laneName(t.lane)}: <a href="${escape(t.raw_result_url)}">whole result tape</a> · <a href="${escape(t.raw_resource_url)}">resource disposition</a>${t.raw_certificate_url ? ` · <a href="${escape(t.raw_certificate_url)}">raw checked proof</a>` : ''}</li>`).join('') + '</ul></details>';
  const choices = byId('proof-choice');
  data.proofs.forEach((p, index) => {
    const option = document.createElement('option'); option.value = String(index);
    option.textContent = `${caseName(p.selector)} · ${originName(p.origin_kind)}`; choices.append(option);
  });
  choices.disabled = false;
  const explanation = command => {
    if (command.rule === 'assumption') return `Use original hypothesis ${math(String.raw`\Gamma_{${command.index}}`)}.`;
    if (command.rule === 'eq_subst') return `Equality substitution yields this implication: if ${math(formula(command.formula[1]))}, then ${math(formula(command.formula[2][1]))} implies ${math(formula(command.formula[2][2]))}.`;
    if (command.rule === 'mp') return `Apply modus ponens to lines ${math(command.antecedent+1)} and ${math(command.implication+1)}. The first supplies the antecedent of the second, so its consequent follows.`;
    throw new Error('Unsupported saved checked command');
  };
  function geometry(proof) {
    const width=420, height=570, x=column=>70+88*column, y=row=>45+21*row;
    const occupied = new Set(proof.tiles.map(t=>t.row));
    let svg=`<svg class="diagram" viewBox="0 0 ${width} ${height}" role="img" aria-label="Actual proof ancestry point patch and long-range premise links"><title>Proof ancestry point patch and declared read addresses</title>`;
    for(let row=0;row<24;row++) svg+=`<text x="5" y="${y(row)+4}" font-size="10" fill="#657180">Row ${row}</text><line x1="55" x2="390" y1="${y(row)}" y2="${y(row)}" stroke="#e7ebef"/>`;
    proof.tiles.forEach(tile => tile.refs.forEach((ref,j)=>{
      const color=j===0?'#16887e':'#8861aa';
      svg+=`<path d="M ${x(j+2)} ${y(tile.row)} C ${x(j+2)+28} ${y(tile.row)},${x(j+2)+28} ${y(ref)},${x(1)} ${y(ref)}" fill="none" stroke="${color}" stroke-width="1.5" opacity=".68"${proof.origin_kind==='completed_source_proposal'?' stroke-dasharray="4 3"':''}/>`;
    }));
    proof.tiles.forEach(tile=>{
      svg+=`<circle cx="${x(0)}" cy="${y(tile.row)}" r="5" fill="#364250"${proof.origin_kind==='completed_source_proposal'&&tile.command.rule!=='assumption'?' fill-opacity=".3" stroke="#364250" stroke-dasharray="2 2"':''}/>`;
      tile.refs.forEach((_,j)=>{svg+=`<circle cx="${x(j+2)}" cy="${y(tile.row)}" r="5" fill="${j===0?'#16887e':'#8861aa'}"/>`;});
    });
    proof.formula_points.forEach(mark=>{svg+=`<circle cx="${x(1)}" cy="${y(mark[1])}" r="5" fill="#2472ac"/>`;});
    svg+=`<circle cx="${x(1)}" cy="${y(23)}" r="9" fill="none" stroke="#287b55" stroke-width="2"/>`;
    if(!occupied.has(23)) svg+=`<circle cx="${x(0)}" cy="${y(23)}" r="5" fill="white" stroke="#a97724"/>`;
    return svg+'</svg>';
  }
  async function render() {
    const p=data.proofs[Number(choices.value)];
    if(window.MathJax?.typesetClear) window.MathJax.typesetClear([byId('statement'),byId('origin'),byId('lines'),byId('geometry-caption')]);
    byId('statement').innerHTML=`<p class="formula">${math(p.gamma.map(formula).join(String.raw`,\quad `)+String.raw`\ \vdash\ `+formula(p.target))}</p>`;
    byId('origin').innerHTML=`<p><span class="outcome">${originName(p.origin_kind)}</span> · ${math(p.tiles.length)} proof tiles · conclusion at row ${math(p.root_row)}.</p><p class="muted">At discovery, the actual selected state occupied ${math(p.current_occupied)} rows. This ancestry patch occupies ${math(p.tiles.length)} rows. ${p.origin_kind==='actual_selected'?'Every displayed ancestry tile belonged to that selected state.':'The derived members below were a checked proposal; they had not been selected.'} No full board was accepted.</p>`;
    byId('geometry').innerHTML=geometry(p);
    byId('geometry-caption').innerHTML=`Only ancestry tiles are shown. Blue points record formula markings; green and purple curves lead to prior formula addresses. The green ring marks the fixed conclusion boundary at row ${math(23)}. ${p.origin_kind==='completed_source_proposal'?'Derived proposal members use dashed links.':''} Exterior boundary marks are retained in the raw certificate. Point spacing is for display.`;
    byId('proof-download').innerHTML=`<p><a href="${escape(p.raw_certificate_url)}">Download this original checked certificate</a></p>`;
    byId('lines').innerHTML=p.tiles.map((tile,index)=>`<article class="line ${tile.command.rule==='assumption'?'hypothesis':''} ${p.origin_kind==='completed_source_proposal'&&tile.command.rule!=='assumption'?'proposed':''}"><h3>Line ${math(index+1)} · tile at row ${math(tile.row)}</h3><div class="formula">${math(formula(tile.command.formula))}</div><p>${explanation(tile.command)}</p><div class="rule">Recorded rule: <code>${escape(tile.command.rule)}</code> · original key: <code>${escape(JSON.stringify(tile.key))}</code></div><div><span class="mark" style="--color:#364250">${math(`t(0,${tile.row})=1`)}</span><span class="mark" style="--color:#2472ac">${math(`m(1,${tile.row})=${tile.formula_code}`)}</span></div><details><summary>Inspect this tile’s exact markings</summary><table class="point-table"><thead><tr><th>Assigned point/value</th><th>Role</th></tr></thead><tbody>${tile.m.map(mark=>`<tr><td>${math(`m(${mark[0]},${mark[1]})=${mark[2]}`)}</td><td>${mark[0]===1?(mark[1]===tile.row?'Formula writer':'Remote formula read'):mark[0]===2?'First input address offset':'Second input address offset'}</td></tr>`).join('')}</tbody></table><p>Premise row addresses: <code>${escape(JSON.stringify(tile.refs))}</code>. Every omitted mark is absent, not an assigned zero.</p></details></article>`).join('');
    await typeset(byId('proof-reader'));
  }
  choices.addEventListener('change',()=>render().catch(error=>{byId('status').textContent=`Reader error: ${error.message}`;}));
  await render();
  await typeset(byId('results')); await typeset(byId('assessment'));
})().catch(error=>{document.getElementById('status').textContent=`Reader error: ${error.message}`; console.error(error);});
