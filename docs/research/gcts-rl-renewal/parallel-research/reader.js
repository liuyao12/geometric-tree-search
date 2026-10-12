'use strict';

// Display projection only: no experiment, inference, resource gate or proof oracle.
(() => {
  const byId = id => document.getElementById(id);
  const literal = value => value === null || value === undefined ? 'Not supplied' : String(value);
  const textCell = (row, value) => {
    const cell = document.createElement('td');
    cell.textContent = literal(value);
    row.append(cell);
    return cell;
  };
  const safeEvidence = value => typeof value === 'string' &&
    /^evidence\/[A-Za-z0-9._/-]+$/.test(value) &&
    !value.split('/').some(part => part === '..' || part === '.' || part === '') ? value : null;
  const link = (parent, label, href) => {
    const safe = safeEvidence(href);
    if (!safe) {
      parent.append(document.createTextNode(literal(label) + ' (no supported evidence path)'));
      return;
    }
    const anchor = document.createElement('a');
    anchor.href = safe;
    anchor.textContent = literal(label);
    parent.append(anchor);
  };
  const render = view => {
    byId('raw-view').textContent = JSON.stringify(view, null, 2);
    if (!view || view.schema !== 'ROOT-assembled-parallel-research-reader-v1' || !Array.isArray(view.stages)) {
      byId('load-status').textContent = 'The saved display schema is unsupported. No source freeze, execution or qualification is inferred.';
      return;
    }
    byId('load-status').textContent = literal(view.status_note);
    const rows = byId('stage-rows');
    rows.replaceChildren();
    if (!view.stages.length) {
      const row = document.createElement('tr');
      const cell = textCell(row, 'No later stage records supplied.');
      cell.colSpan = 5;
      rows.append(row);
    }
    for (const record of view.stages) {
      const row = document.createElement('tr');
      textCell(row, record.stage);
      textCell(row, record.scope);
      textCell(row, record.disposition);
      textCell(row, record.note);
      const cell = document.createElement('td');
      link(cell, record.evidence_label || 'Saved record', record.evidence);
      row.append(cell);
      rows.append(row);
    }
    const evidence = byId('evidence-links');
    for (const record of Array.isArray(view.evidence) ? view.evidence : []) {
      const item = document.createElement('span');
      link(item, record.label, record.href);
      evidence.append(item);
    }
  };
  fetch('view.json', {cache:'no-store'})
    .then(response => {
      if (!response.ok) throw new Error('Saved display view unavailable');
      return response.json();
    })
    .then(render)
    .catch(() => {
      byId('load-status').textContent = 'No supported ROOT-assembled view loaded. The saved Notebook 115 baseline above is unchanged; no later execution or qualification is inferred.';
    });
})();
