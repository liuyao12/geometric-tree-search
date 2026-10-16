'use strict';
// Saved presentation metadata only. No scientific module, model or API is loaded.
const byId = id => document.getElementById(id);
const MODES = ['router-protocol', 'global-forced-dead', 'singleton-transfer', 'two-transfer', 'short-EOF', 'child-UNKNOWN'];
const unavailable = 'Unavailable';
function element(tag, text, className) {
  const value = document.createElement(tag);
  if (text !== undefined) value.textContent = text;
  if (className) value.className = className;
  return value;
}
function requireData(value, message) {
  if (!value) throw new Error(message);
}
function whole(value, maximum) {
  return Number.isInteger(value) && value >= 0 && value <= maximum;
}
function optionalNumber(value) {
  return value === null || (typeof value === 'number' && Number.isFinite(value) && value >= 0);
}
function seconds(value) {
  return value === null ? unavailable : `\\(${value.toFixed(3)}\\,\\mathrm{s}\\)`;
}
function memory(value) {
  return value === null ? unavailable : `\\(${(value / 1048576).toFixed(2)}\\,\\mathrm{MiB}\\)`;
}
function safeHref(value) {
  requireData(typeof value === 'string' && value.length > 0, 'A saved evidence link is missing.');
  const href = new URL(value, document.baseURI);
  requireData(href.protocol === 'https:' || href.protocol === 'http:', 'An evidence link has an unsupported protocol.');
  return href.href;
}
function link(label, href) {
  const value = element('a', label);
  value.href = safeHref(href);
  if (new URL(value.href).origin !== location.origin) value.rel = 'noopener noreferrer';
  return value;
}
function validate(data) {
  requireData(data && data.schema === 'ROOT-fresh-projection-public-report-v1', 'The saved report schema is unavailable or unexpected.');
  for (const field of ['title', 'date', 'reader_scope', 'next_step']) {
    requireData(typeof data[field] === 'string', `Missing saved ${field}.`);
  }
  requireData(data.total_required === 12 && whole(data.prior_qualified, 12) && whole(data.current_qualified, 12), 'The declared twelve-case summary is inconsistent.');
  requireData(typeof data.all_current_controls_qualified === 'boolean', 'The saved qualification flag is unavailable.');
  requireData(data.limits?.joint_seconds === 20 && data.limits?.aggregate_owned_bytes === 536870912, 'The declared limits differ from this reader scope.');
  requireData(Array.isArray(data.endpoints) && data.endpoints.length === 6, 'All six saved endpoint scopes are required.');
  requireData(new Set(data.endpoints.map(endpoint => endpoint.mode)).size === 6, 'An endpoint mode is duplicated.');
  let qualified = 0;
  const cases = new Set();
  for (const endpoint of data.endpoints) {
    requireData(MODES.includes(endpoint.mode) && typeof endpoint.label === 'string', 'An endpoint mode or label is unexpected.');
    requireData(Array.isArray(endpoint.case_names) && endpoint.case_names.length === 2 && endpoint.case_names.every(value => typeof value === 'string'), 'Each endpoint must list its two declared cases.');
    for (const name of endpoint.case_names) {
      requireData(!cases.has(name), 'A declared case appears more than once.');
      cases.add(name);
    }
    requireData(whole(endpoint.qualified_case_count, 2) && whole(endpoint.unqualified_case_count, 2) && endpoint.qualified_case_count + endpoint.unqualified_case_count === 2, 'An endpoint case summary is inconsistent.');
    requireData(endpoint.reported_case_count === null || whole(endpoint.reported_case_count, 2), 'Reported counts must remain literal or unavailable.');
    requireData(typeof endpoint.complete_returned_record === 'boolean', 'The returned-record flag is unavailable.');
    requireData(optionalNumber(endpoint.prior_seconds) && optionalNumber(endpoint.current_seconds), 'An elapsed value is unavailable or malformed.');
    requireData(endpoint.aggregate_B_bytes === null || (Number.isSafeInteger(endpoint.aggregate_B_bytes) && endpoint.aggregate_B_bytes > 0), 'An owned-memory value is malformed.');
    safeHref(endpoint.disposition_href);
    if (endpoint.expanded_href !== null) safeHref(endpoint.expanded_href);
    qualified += endpoint.qualified_case_count;
  }
  requireData(qualified === data.current_qualified && data.all_current_controls_qualified === (qualified === data.total_required), 'The saved overall and endpoint qualification summaries disagree.');
  requireData(Array.isArray(data.evidence), 'The evidence list is unavailable.');
  for (const item of data.evidence) {
    requireData(typeof item.label === 'string' && typeof item.sha256 === 'string' && /^[0-9a-f]{64}$/.test(item.sha256) && Number.isSafeInteger(item.bytes) && item.bytes >= 0, 'A saved evidence pin is malformed.');
    safeHref(item.href);
  }
  return data;
}
function renderCounts(data) {
  byId('report-title').textContent = data.title;
  document.title = `${data.title} · GCTS research`;
  byId('report-date').textContent = data.date;
  byId('prior-count').textContent = `\\(${data.prior_qualified}\\,/\\,${data.total_required}\\)`;
  byId('current-count').textContent = `\\(${data.current_qualified}\\,/\\,${data.total_required}\\)`;
  byId('current-status').textContent = data.all_current_controls_qualified ? 'All current controls qualified' : 'Current qualification remains incomplete';
  byId('current-status').parentElement.dataset.complete = String(data.all_current_controls_qualified);
  byId('outcome-copy').textContent = data.all_current_controls_qualified
    ? 'All declared essential cases qualified across six separately closed windows. This is scoped control evidence.'
    : 'Unqualified cases remain open. A missing returned record supplies no reported case count or semantic progress.';
  byId('reader-scope').textContent = data.reader_scope;
  byId('next-step').textContent = data.next_step;
}
function renderChart(data) {
  const chart = byId('comparison-chart');
  chart.replaceChildren();
  const readings = data.endpoints.flatMap(endpoint => [endpoint.prior_seconds, endpoint.current_seconds]).filter(value => value !== null);
  const maximum = Math.max(data.limits.joint_seconds * 1.12, ...readings.map(value => value * 1.05));
  chart.style.setProperty('--limit', `${100 * data.limits.joint_seconds / maximum}%`);
  const axis = element('div', undefined, 'chart-axis');
  axis.append(element('span', '\\(0\\)', 'zero'), element('span', seconds(data.limits.joint_seconds), 'deadline-label'));
  chart.append(axis);
  for (const mode of MODES) {
    const endpoint = data.endpoints.find(value => value.mode === mode);
    const row = element('div', undefined, 'endpoint-chart-row');
    const name = element('div', endpoint.label, 'chart-name');
    name.append(element('small', `${endpoint.qualified_case_count} of ${endpoint.case_names.length} current cases qualified`));
    const pair = element('div', undefined, 'bar-pair');
    for (const [version, value] of [['previous', endpoint.prior_seconds], ['current', endpoint.current_seconds]]) {
      const barRow = element('div', undefined, 'bar-row');
      barRow.setAttribute('aria-label', `${version}: ${value === null ? 'unavailable' : `${value.toFixed(3)} seconds`}`);
      if (value === null) {
        barRow.append(element('span', `${version === 'previous' ? 'Previous' : 'Current'}: ${unavailable}`, 'unavailable-bar'));
      } else {
        const bar = element('div', undefined, `bar ${version}`);
        bar.style.width = `${100 * value / maximum}%`;
        bar.setAttribute('aria-hidden', 'true');
        barRow.append(bar, element('span', seconds(value), 'bar-value'));
      }
      pair.append(barRow);
    }
    row.append(name, pair);
    chart.append(row);
  }
}
function addStat(container, label, value) {
  const box = element('div');
  box.append(element('dt', label), element('dd', value));
  container.append(box);
}
function renderEndpoints(data) {
  const container = byId('endpoint-details');
  container.replaceChildren();
  for (const mode of MODES) {
    const endpoint = data.endpoints.find(value => value.mode === mode);
    const card = element('details', undefined, 'endpoint-card');
    const summary = element('summary');
    summary.append(element('span', endpoint.label));
    summary.append(element('span', endpoint.qualified_case_count === 2 ? 'Qualified' : endpoint.qualified_case_count ? 'Partial' : 'Unqualified', `badge${endpoint.qualified_case_count === 2 ? ' qualified' : ''}`));
    const body = element('div', undefined, 'endpoint-body');
    body.append(element('p', endpoint.complete_returned_record ? 'Complete returned record retained.' : 'No complete returned record. Missing results remain unavailable.'));
    const list = element('ul', undefined, 'case-list');
    for (const name of endpoint.case_names) list.append(element('li', name));
    body.append(list);
    const stats = element('dl', undefined, 'detail-stats');
    addStat(stats, 'Qualified / unqualified', `\\(${endpoint.qualified_case_count}\\,/\\,${endpoint.unqualified_case_count}\\)`);
    addStat(stats, 'Reported case count', endpoint.reported_case_count === null ? unavailable : String(endpoint.reported_case_count));
    addStat(stats, 'Previous elapsed', seconds(endpoint.prior_seconds));
    addStat(stats, 'Current elapsed', seconds(endpoint.current_seconds));
    addStat(stats, 'Aggregate owned memory', memory(endpoint.aggregate_B_bytes));
    body.append(stats);
    const links = element('div', undefined, 'record-links');
    links.append(link('Saved disposition', endpoint.disposition_href));
    links.append(endpoint.expanded_href === null ? element('span', 'Expanded record unavailable', 'missing-link') : link('Full expanded record', endpoint.expanded_href));
    body.append(links);
    const raw = element('details');
    raw.append(element('summary', 'Endpoint metadata'), element('pre', JSON.stringify(endpoint, null, 2)));
    body.append(raw);
    card.append(summary, body);
    container.append(card);
  }
}
function renderEvidence(data) {
  const list = byId('evidence-list');
  list.replaceChildren();
  for (const item of data.evidence) {
    const row = element('li', undefined, 'evidence-item');
    const pin = element('span', undefined, 'evidence-pin');
    pin.append(element('code', item.sha256), element('span', `${item.bytes.toLocaleString('en-US')} bytes`, 'evidence-bytes'));
    row.append(link(item.label, item.href), pin);
    list.append(row);
  }
  byId('report-metadata').textContent = JSON.stringify(data, null, 2);
}
async function loadReport() {
  const response = await fetch('report-data.json', {cache: 'no-store'});
  requireData(response.ok, 'Saved report-data.json is unavailable.');
  const data = validate(await response.json());
  renderCounts(data);
  renderChart(data);
  renderEndpoints(data);
  renderEvidence(data);
  if (window.MathJax?.startup?.promise) await window.MathJax.startup.promise;
  if (window.MathJax?.typesetPromise) await window.MathJax.typesetPromise();
  byId('load-status').textContent = 'Saved report loaded. Expand an endpoint to inspect its declared cases and raw-record links.';
  document.body.dataset.currentControlsQualified = String(data.all_current_controls_qualified);
  document.body.dataset.savedReaderReady = 'true';
}
loadReport().catch(error => {
  document.body.dataset.savedReaderFailed = 'true';
  const status = byId('load-status');
  status.classList.add('error');
  status.textContent = `Saved reader could not finish: ${error.message}`;
});
