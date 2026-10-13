/* SOURCE draft: presentation of a future ROOT-sanitized saved record only.
   No graph/catalog/checker/search/learner code and no data-derived legality. */
(() => {
  'use strict';
  const EXPECTED_SCHEMA = 'sanitized-row-mask-runtime-outcome-v1';
  const CASE_IDS = ['tiny-pred-branch','tiny-pred-forced','tiny-pred-dead',
    'tiny-eq-branch','tiny-eq-forced','tiny-eq-dead',
    'tiny-and-branch','tiny-and-forced','tiny-and-dead',
    'tiny-all-branch','tiny-all-forced','tiny-all-dead'];
  const byId = id => document.getElementById(id);
  const text = (tag, value, className) => {
    const element = document.createElement(tag);
    element.textContent = value;
    if (className) element.className = className;
    return element;
  };
  const integer = value => Number.isSafeInteger(value);
  const count = value => integer(value) && value >= 0;
  const maybeCount = value => value === null || count(value);
  const scalar = value => typeof value === 'number' && Number.isFinite(value);
  const shortText = value => typeof value === 'string' && value.length > 0 && value.length <= 240;
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const need = (value, label) => { if (!value) throw new Error(label); };
  const math = value => {
    if (value === null || value === undefined) return 'Not recorded';
    const rendered = String(value).replace(/^(.+)[eE]([+-]?\d+)$/, '$1\\times10^{$2}');
    return '\\(' + rendered + '\\)';
  };
  let mathQueue = Promise.resolve();
  const typeset = () => {
    mathQueue = mathQueue.then(async () => {
      if (window.MathJax && window.MathJax.startup) {
        await window.MathJax.startup.promise;
        if (window.MathJax.typesetPromise) await window.MathJax.typesetPromise([byId('runtime')]);
      }
    }).catch(() => {});
    return mathQueue;
  };
  const clear = element => {
    if (window.MathJax && window.MathJax.typesetClear) window.MathJax.typesetClear([element]);
    element.replaceChildren();
  };
  const flag = value => value === true ? 'Recorded complete' : value === false ? 'Not recorded complete' : 'Not recorded';

  function validateSnapshot(snapshot) {
    need(object(snapshot) && shortText(snapshot.label), 'saved snapshot label');
    need(Array.isArray(snapshot.totals) && snapshot.totals.length === 24 && snapshot.totals.every(scalar), 'all24 saved occupancy values');
    need(Array.isArray(snapshot.marks) && snapshot.marks.length <= 4096, 'bounded saved marking projection');
    const locations = new Set();
    for (const mark of snapshot.marks) {
      need(Array.isArray(mark) && mark.length === 4 && mark.every(integer) && mark[3] > 0, 'saved marking tuple with positive reference count');
      const key = mark[0] + ':' + mark[1];
      need(!locations.has(key), 'one displayed value per saved coordinate');
      locations.add(key);
    }
    need(Array.isArray(snapshot.class_signature) && snapshot.class_signature.every(count), 'saved assigned-code signature');
    need(Array.isArray(snapshot.rows) && snapshot.rows.length === 24, 'all24 saved row receipts');
    snapshot.rows.forEach((row, index) => {
      need(object(row) && row.row === index && [row.base_count,row.count,row.factor_count,row.excluded_legal_count].every(count), 'ordered complete row display fields');
      need(typeof row.factor_EOF === 'boolean' && typeof row.kernel_key_EOF === 'boolean', 'explicit saved EOF flags');
    });
    need(Array.isArray(snapshot.decision) && snapshot.decision.length === 4 && shortText(snapshot.decision[0]) && snapshot.decision.slice(1).every(maybeCount), 'saved scheduler decision fields');
  }

  function validateView(view) {
    need(object(view) && view.schema === EXPECTED_SCHEMA && shortText(view.status), 'sanitized runtime schema/status');
    need([view.completed_cases,view.observations,view.complete_factor_EOFs,view.complete_kernel_EOFs].every(maybeCount), 'nullable actual census fields');
    need(Array.isArray(view.cases) && view.cases.length <= 12, 'bounded saved case list');
    const seen = new Set();
    for (const item of view.cases) {
      need(object(item) && CASE_IDS.includes(item.case_id) && !seen.has(item.case_id), 'unique declared saved case');
      seen.add(item.case_id);
      need(typeof item.completed === 'boolean' && count(item.case_index) && [item.observation_count,item.factor_EOF_count,item.kernel_EOF_count].every(maybeCount), 'explicit saved case closure/census');
      need(object(item.case_fingerprint) && typeof item.case_fingerprint.sha256 === 'string' && /^[a-f0-9]{64}$/.test(item.case_fingerprint.sha256) && count(item.case_fingerprint.bytes), 'sanitized saved case fingerprint');
      need(Array.isArray(item.snapshots) && item.snapshots.length <= 128, 'bounded saved snapshot list');
      item.snapshots.forEach(validateSnapshot);
    }
    need(object(view.resource), 'separate saved resource record');
    need(['full_production_qualified','proof_discovered','RL_activated','performance_advantage_established'].every(key => typeof view[key] === 'boolean'), 'explicit saved top-level scope flags');
    need(Array.isArray(view.gaps) && view.gaps.length <= 32 && view.gaps.every(shortText), 'bounded human-readable qualification gaps');
    return view;
  }

  function renderSummary(view) {
    const host = byId('runtime-summary'); clear(host); host.hidden = false;
    const table = text('table', '');
    const head = document.createElement('thead'); const hr = document.createElement('tr');
    hr.append(text('th','Saved census'),text('th','Recorded value')); head.append(hr); table.append(head);
    const body = document.createElement('tbody');
    for (const [label,key] of [['Closed cases','completed_cases'],['Saved observations','observations'],['Factor row EOFs','complete_factor_EOFs'],['Kernel row EOFs','complete_kernel_EOFs']]) {
      const row = document.createElement('tr'); row.append(text('td',label),text('td',math(view[key]))); body.append(row);
    }
    table.append(body); host.append(table);
    host.append(text('p','Observations are saved comparison points, not a count of distinct states or discovered proofs.','caption'));
  }

  function renderResources(view) {
    const host = byId('runtime-resource'); clear(host); host.hidden = false;
    host.append(text('h3','Separate saved cost scopes'));
    const grid = text('div','','runtime-costs');
    for (const [title,key,unit] of [
      ['Cold caller to observed terminal','caller_elapsed_seconds','\\mathrm{s}'],
      ['Owner main to post-write','owner_main_to_postwrite_seconds','\\mathrm{s}'],
      ['Conditional scoped peak','postwrite_peak_bytes','\\mathrm{bytes}'],
      ['Later metadata finalizer','later_finalizer_elapsed_seconds','\\mathrm{s}']]) {
      const value = view.resource[key];
      need(value === undefined || value === null || (scalar(value) && value >= 0), 'finite nonnegative saved resource display');
      const box = text('article',''); box.append(text('h4',title));
      box.append(text('p',value === null || value === undefined ? 'Not recorded' : math(value).slice(0,-2) + '\\,' + unit + '\\)'));
      grid.append(box);
    }
    host.append(grid);
    host.append(text('p','ROOT resource disposition: ' + flag(view.resource.ROOT_final_accepted) + '. Owner startup before main is in the cold caller scope. The later finalizer is separately charged. These scopes are not disjoint costs to add.','caption'));
    if (typeof view.resource.conditional_scope === 'string' && view.resource.conditional_scope.length <= 2048) host.append(text('p',view.resource.conditional_scope,'caption'));
    const gaps = byId('runtime-gaps'); clear(gaps); gaps.hidden = false;
    gaps.append(text('h3','Scope and remaining gates'));
    const list = text('ul','','runtime-gap-list'); view.gaps.forEach(gap => list.append(text('li',gap))); gaps.append(list);
    const scopeTable = text('table',''); const tbody = text('tbody','');
    for (const [label,key] of [['Full production qualification','full_production_qualified'],['New proof discovery','proof_discovered'],['RL activation','RL_activated'],['Performance advantage','performance_advantage_established'],['Independent saved-data review','independent_saved_review_passed']]) {
      const row = text('tr',''); row.append(text('td',label),text('td',flag(view[key]))); tbody.append(row);
    }
    scopeTable.append(tbody); gaps.append(scopeTable);
  }

  function renderLinks(snapshot, markMap) {
    const host = byId('runtime-links'); clear(host); host.hidden = true;
    let fill = null;
    for (let row = 23; row >= 0; row--) {
      const first = markMap.get('2:' + row); const second = markMap.get('3:' + row);
      if (snapshot.totals[row] > 0 && first && second && first[2] < 0 && second[2] < 0
          && row + first[2] >= 0 && row + second[2] >= 0) {
        fill = {row,ports:[first,second]}; break;
      }
    }
    if (!fill) return;
    host.hidden = false;
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns,'svg'); svg.setAttribute('viewBox','0 0 680 230');
    svg.setAttribute('role','img'); svg.setAttribute('aria-label','Illustrative layout of the two ordered links derived from saved negative read offsets');
    const paths = ['M306 181 C270 130 170 125 120 76','M374 181 C410 130 510 125 560 76'];
    ['var(--green)','var(--amber)'].forEach((color,index) => {
      const path = document.createElementNS(ns,'path'); path.setAttribute('d',paths[index]); path.setAttribute('fill','none'); path.setAttribute('stroke',color); path.setAttribute('stroke-width','3'); svg.append(path);
      const arrow = document.createElementNS(ns,'path'); arrow.setAttribute('d',index === 0 ? 'M114 83 L120 76 L128 83' : 'M552 83 L560 76 L566 83'); arrow.setAttribute('fill','none'); arrow.setAttribute('stroke',color); arrow.setAttribute('stroke-width','3'); svg.append(arrow);
    });
    host.append(svg);
    fill.ports.forEach((port,index) => {
      const target = fill.row + port[2]; const formula = markMap.get('1:' + target);
      const box = text('article','','runtime-link-node ' + (index === 0 ? 'runtime-link-left' : 'runtime-link-right'));
      box.append(text('p','Saved receptor row ' + math(target)),text('p','Occupancy ' + math(snapshot.totals[target])));
      box.append(text('p',formula ? 'Formula code ' + math(formula[2]) : 'Formula unassigned'));
      host.append(box);
    });
    const box = text('article','','runtime-link-node runtime-link-fill'); box.append(text('p','Saved occupied row ' + math(fill.row)));
    fill.ports.forEach((port,index) => box.append(text('p','\\(m(' + port[0] + ',' + fill.row + ')=' + port[2] + '\\)', index === 0 ? 'runtime-link-first' : 'runtime-link-second')));
    host.append(box);
    host.append(text('small','Links use only saved read offsets and row plus offset. This illustrative layout is not to lattice scale and establishes no proof.','runtime-link-caption'));
  }

  function renderSnapshot(item, snapshot, savedIndex) {
    const host = byId('runtime-rows'); clear(host);
    byId('runtime-figure').hidden = false;
    const caption = byId('runtime-snapshot-caption'); clear(caption);
    caption.append(text('span',snapshot.label + ' · saved observation '),text('span',math(savedIndex)));
    const assigned = snapshot.class_signature.length ? '\\(\\{' + snapshot.class_signature.join(',') + '\\}\\)' : '\\(\\varnothing\\)';
    caption.append(text('span',' · assigned-code signature ' + assigned));
    caption.append(text('span',' · saved scheduler kind: ' + snapshot.decision[0] + '; row: ' + math(snapshot.decision[1]) + '; degree: ' + math(snapshot.decision[2]) + '; generation: ' + math(snapshot.decision[3])));
    const markMap = new Map(snapshot.marks.map(mark => [mark[0] + ':' + mark[1],mark]));
    const prior = savedIndex > 0 ? item.snapshots[savedIndex - 1] : null;
    if (prior) caption.append(text('span',' · count comparison with preceding saved label: ' + prior.label));
    renderLinks(snapshot,markMap);
    snapshot.rows.forEach(row => {
      const tr = text('tr',''); if ([18,19,22].includes(row.row)) tr.className = 'runtime-focus';
      tr.append(text('td',math(row.row)),text('td',math(snapshot.totals[row.row]),snapshot.totals[row.row] !== 0 ? 'runtime-occupied' : ''));
      for (const [layer,className] of [[1,'runtime-formula'],[2,'runtime-first'],[3,'runtime-second']]) {
        const key = layer + ':' + row.row;
        const td = text('td','');
        if (markMap.has(key)) {
          const mark = markMap.get(key); td.className = className;
          td.append(text('span',math(mark[2])),text('small','\\(\\text{refs}=' + mark[3] + '\\)','runtime-refcount'));
        } else { td.className = 'runtime-missing'; td.textContent = 'Unassigned'; }
        tr.append(td);
      }
      const available = text('td',math(row.count));
      if (prior && prior.rows[row.row].count !== row.count) {
        available.append(text('small','Previous ' + math(prior.rows[row.row].count) + '; \\(\\Delta=' + (row.count - prior.rows[row.row].count) + '\\)','runtime-refcount'));
      }
      tr.append(text('td',math(row.base_count)),text('td',math(row.excluded_legal_count)),available,text('td',math(row.factor_count)),text('td',flag(row.factor_EOF)),text('td',flag(row.kernel_key_EOF))); host.append(tr);
    });
    const extra = snapshot.marks.filter(mark => ![1,2,3].includes(mark[0]) || mark[1] < 0 || mark[1] >= 24);
    const boundary = byId('runtime-boundary'); boundary.hidden = extra.length === 0;
    const boundaryHost = byId('runtime-boundary-marks'); clear(boundaryHost);
    extra.forEach(mark => boundaryHost.append(text('p','\\(m(' + mark[0] + ',' + mark[1] + ')=' + mark[2] + ',\\quad\\text{refs}=' + mark[3] + '\\)')));
    typeset().catch(() => {});
  }

  function selectCase(view) {
    const item = view.cases.find(record => record.case_id === byId('runtime-case').value);
    const select = byId('runtime-snapshot'); select.replaceChildren();
    const summary = byId('runtime-case-summary'); clear(summary);
    byId('runtime-figure').hidden = true;
    if (!item) { select.disabled = true; select.append(text('option','No saved case')); return; }
    summary.append(text('p','Case closure: ' + flag(item.completed) + '. Saved observations: ' + math(item.observation_count) + '; factor row EOFs: ' + math(item.factor_EOF_count) + '; kernel row EOFs: ' + math(item.kernel_EOF_count) + '.'));
    const fingerprint = text('details',''); fingerprint.append(text('summary','Saved case fingerprint'));
    const fp = text('p',''); fp.append(text('code',item.case_fingerprint.sha256),text('span',' · bytes: ' + math(item.case_fingerprint.bytes))); fingerprint.append(fp); summary.append(fingerprint);
    item.snapshots.forEach((snapshot,index) => { const option = text('option',snapshot.label); option.value = String(index); select.append(option); });
    select.disabled = item.snapshots.length === 0;
    if (!item.snapshots.length) select.append(text('option','No closed saved observation'));
    select.onchange = () => { const index = Number(select.value); renderSnapshot(item,item.snapshots[index],index); };
    if (item.snapshots.length) {
      const remoteIndex = item.snapshots.findIndex(snapshot => snapshot.label === 'remote_formula_and_read_ports');
      const index = remoteIndex >= 0 ? remoteIndex : 0; select.value = String(index);
      renderSnapshot(item,item.snapshots[index],index);
    }
    typeset().catch(() => {});
  }

  async function load() {
    try {
      const response = await fetch('runtime-outcome-v1.json',{cache:'no-store'});
      need(response.ok,'runtime saved record unavailable');
      const source = await response.text(); need(source.length <= 4194304,'bounded runtime presentation record');
      const view = validateView(JSON.parse(source));
      byId('runtime-status').textContent = 'Saved runtime disposition: ' + view.status + '. Source: runtime-outcome-v1.json.';
      renderSummary(view); renderResources(view);
      const select = byId('runtime-case'); select.replaceChildren();
      CASE_IDS.forEach(id => {
        const item = view.cases.find(record => record.case_id === id);
        const option = text('option',id + (item ? '' : ' · no saved case')); option.value = id; option.disabled = !item; select.append(option);
      });
      select.disabled = view.cases.length === 0;
      if (view.cases.length) { select.value = view.cases.some(item => item.case_id === 'tiny-pred-branch') ? 'tiny-pred-branch' : view.cases[0].case_id; select.onchange = () => selectCase(view); selectCase(view); }
      await typeset();
    } catch (_) {
      byId('runtime-status').textContent = 'No compatible saved runtime outcome is available. This section assumes no completed run or accepted result.';
      byId('runtime-summary').hidden = true; byId('runtime-resource').hidden = true; byId('runtime-gaps').hidden = true; byId('runtime-figure').hidden = true;
      byId('runtime-case').disabled = true; byId('runtime-snapshot').disabled = true;
    }
  }
  load();
})();
