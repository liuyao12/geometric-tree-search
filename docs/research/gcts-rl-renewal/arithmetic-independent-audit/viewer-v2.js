"use strict";
(() => {
  const SCHEMA = "Notebook161-saved-arithmetic-audit-display-packet-v1";
  const phases = [
    ["raw_input", "Raw input authentication"], ["parse", "Preparation parse"],
    ["input_seal", "Complete input seal"], ["auditor", "Independent auditor"],
    ["domains", "Complete initial domains"], ["eof", "Whole witness EOF"],
    ["certificate", "Saved audit certificate"]
  ];
  const scopeLabels = [
    ["independent_audit", "Independent finite audit"],
    ["calibration", "Calibration and producer controls"],
    ["word_controls", "Unrelated primitive-word controls"],
    ["rank_proposal", "Rank marking proposal"]
  ];
  const flagLabels = [
    ["ROOT_complete_independent_audit_accepted", "Complete independent audit accepted"],
    ["mathematical_catalogue_admitted", "Mathematical catalogue admitted"],
    ["accepted_prefix", "Accepted prefix"], ["target_proofs_accepted", "Target proof accepted"],
    ["native_accepted", "Native accepted"], ["full24_accepted", "Full finite board accepted"],
    ["induction_accepted", "Induction accepted"], ["full_PA_accepted", "Full PA accepted"]
  ];
  const $ = id => document.getElementById(id);
  const node = (tag, value, cls) => {
    const item = document.createElement(tag);
    if (value !== undefined) item.textContent = String(value);
    if (cls) item.className = cls;
    return item;
  };
  const plain = value => value !== null && typeof value === "object" && !Array.isArray(value);
  const need = (condition, message) => { if (!condition) throw new Error(message); };
  const measured = value => typeof value === "number" && Number.isFinite(value) && value >= 0;
  const metric = value => measured(value) ? node("code", String(value)) : node("span", "Not supplied", "pending");
  const clear = id => $(id).replaceChildren();
  const math = value => node("span", `\\(${value}\\)`);
  const typeset = async () => {
    if (window.MathJax && MathJax.typesetPromise) {
      await MathJax.typesetPromise([$("reader")]);
    }
  };
  function publicHref(value) {
    need(typeof value === "string" && value.length > 0, "Missing publication link");
    need(!value.startsWith("/") && !value.startsWith("\\") && !value.includes("\u0000"), "Local paths are provenance, not browser routes");
    const url = new URL(value, location.href);
    need(url.protocol === "https:" || url.protocol === "http:", "Unsupported evidence route");
    return url.href;
  }
  function links(container, records) {
    container.replaceChildren();
    if (!records.length) { container.append(node("p", "No evidence routes attached.", "pending")); return; }
    const list = node("ul", undefined, "links");
    records.forEach(record => {
      need(plain(record) && typeof record.label === "string", "Invalid evidence link");
      const li = node("li");
      const a = node("a", record.label); a.href = publicHref(record.href); li.append(a);
      if (typeof record.sha256 === "string") {
        need(/^[0-9a-f]{64}$/.test(record.sha256), "Invalid raw evidence SHA");
        li.append(document.createTextNode(" · "), node("code", record.sha256, "hash"));
      }
      if (record.bytes !== undefined) { li.append(document.createTextNode(" · bytes "), metric(record.bytes)); }
      if (typeof record.source_path === "string") {
        const provenance = node("p", "Source provenance: ", "small");
        provenance.append(node("code", record.source_path)); li.append(provenance);
      }
      list.append(li);
    });
    container.append(list);
  }
  function table(headers, cls) {
    const result = node("table", undefined, cls);
    const head = node("thead"), row = node("tr");
    headers.forEach(title => row.append(node("th", title))); head.append(row); result.append(head);
    const body = node("tbody"); result.append(body); return [result, body];
  }
  function renderCosts(attempts) {
    clear("cost-table"); clear("memory-chart");
    if (!attempts.length) {
      $("cost-table").append(node("p", "No saved attempts or measurements are attached.", "pending")); return;
    }
    const [result, body] = table(["Attempt", "Recorded outcome", "Caller seconds", "Owned seconds", "Inner seconds", "Owned peak bytes", "Cap bytes"], "costs");
    attempts.forEach(attempt => {
      const d = attempt.disposition, row = node("tr");
      row.append(node("td", attempt.label), node("td", attempt.status_text));
      [d.genuine_caller_seconds, d.owned_postwrite_seconds, d.inner_seconds,
        d.observed_owned_postwrite_peak_bytes, d.limits && d.limits.owned_peak_bytes].forEach(value => {
        const cell = node("td"); cell.append(metric(value)); row.append(cell);
      });
      body.append(row);
    });
    $("cost-table").append(result);
    const samples = attempts.filter(a => measured(a.disposition.observed_owned_postwrite_peak_bytes) &&
      a.disposition.limits && measured(a.disposition.limits.owned_peak_bytes));
    if (!samples.length) { $("memory-chart").append(node("p", "No complete peak/cap pair is attached.", "pending")); return; }
    const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg");
    const height = 58 + samples.length * 62;
    svg.setAttribute("viewBox", `0 0 840 ${height}`); svg.setAttribute("role", "img");
    const title = document.createElementNS(ns, "title"); title.textContent = "Attached owned memory peaks and declared caps"; svg.append(title);
    const maximum = Math.max(...samples.flatMap(a => [a.disposition.observed_owned_postwrite_peak_bytes, a.disposition.limits.owned_peak_bytes]), 1);
    samples.forEach((attempt, i) => {
      const peak = attempt.disposition.observed_owned_postwrite_peak_bytes;
      const cap = attempt.disposition.limits.owned_peak_bytes;
      const y = 28 + i * 62;
      const label = document.createElementNS(ns, "text"); label.setAttribute("x", "8"); label.setAttribute("y", String(y + 16)); label.textContent = attempt.chart_label || attempt.id; svg.append(label);
      const rect = document.createElementNS(ns, "rect"); rect.setAttribute("x", "200"); rect.setAttribute("y", String(y));
      rect.setAttribute("width", String(peak / maximum * 580)); rect.setAttribute("height", "26");
      rect.setAttribute("fill", peak > cap ? "#af3344" : "#2868ba"); svg.append(rect);
      const line = document.createElementNS(ns, "line"); const x = 200 + cap / maximum * 580;
      line.setAttribute("x1", String(x)); line.setAttribute("x2", String(x)); line.setAttribute("y1", String(y - 5)); line.setAttribute("y2", String(y + 31));
      line.setAttribute("stroke", "#182c43"); line.setAttribute("stroke-width", "2"); svg.append(line);
      const state = document.createElementNS(ns, "text"); state.setAttribute("x", "200"); state.setAttribute("y", String(y + 45));
      state.textContent = peak > cap ? "Saved peak exceeds cap" : "Saved peak does not exceed cap; other gates remain separate"; svg.append(state);
    });
    $("memory-chart").append(svg);
  }
  function renderFlags(attempt) {
    clear("flags");
    const d = attempt.disposition;
    if (typeof d.scope === "string") $("flags").append(node("p", d.scope));
    const [result, body] = table(["Saved flag", "Recorded value"], "flags");
    flagLabels.forEach(([key, label]) => {
      const row = node("tr"), cell = node("td");
      if (typeof d[key] === "boolean") cell.append(node("code", String(d[key]), d[key] ? "flag-true" : "flag-false"));
      else cell.append(node("span", "Not supplied", "pending"));
      row.append(node("td", label), cell); body.append(row);
    });
    $("flags").append(result);
    const resource = attempt.resource_decision;
    $("flags").append(node("h3", "Saved resource qualification"));
    if (resource === null || resource === undefined) {
      $("flags").append(node("p", "No complete ROOT resource-decision record attached.", "pending"));
    } else {
      need(plain(resource) && resource.schema === "ROOT-fresh-catalog-stage-final-decision-v1" &&
        typeof resource.ROOT_final_accepted === "boolean" && plain(resource.predicates) &&
        Object.keys(resource.predicates).length === 14 && Object.values(resource.predicates).every(v => typeof v === "boolean"),
        "Complete actual ROOT resource predicates are required");
      const note = node("p", "Recorded resource acceptance: ");
      note.append(node("code", String(resource.ROOT_final_accepted))); $("flags").append(note);
      const [resourceTable, resourceBody] = table(["Original predicate", "Recorded value"], "flags");
      Object.entries(resource.predicates).forEach(([name, value]) => {
        const row = node("tr"), nameCell = node("td"), valueCell = node("td");
        nameCell.append(node("code", name)); valueCell.append(node("code", String(value), value ? "flag-true" : "flag-false"));
        row.append(nameCell, valueCell); resourceBody.append(row);
      });
      $("flags").append(resourceTable, node("p", "Resource custody does not imply mathematical catalogue or theorem acceptance.", "small"));
    }
  }
  function renderPhases(attempt) {
    clear("phases"); const list = node("ol", undefined, "phase-list");
    const entries = attempt.phase_trace || [];
    const records = new Map(entries.map(item => [item.phase, item]));
    need(records.size === entries.length && entries.every(item => phases.some(([id]) => id === item.phase)), "Duplicate or unsupported phase record");
    phases.forEach(([id, label]) => {
      const record = records.get(id), li = node("li"); li.append(node("strong", label));
      li.append(node("span", record ? record.status_text : "No saved phase state supplied", "phase-state"));
      if (record && typeof record.evidence_note === "string") li.append(node("p", record.evidence_note, "small"));
      if (record && record.evidence_href) { const a = node("a", "Phase evidence"); a.href = publicHref(record.evidence_href); li.append(a); }
      list.append(li);
    });
    $("phases").append(list);
  }
  function renderDomains(attempt) {
    clear("domain-table"); clear("certificate-meta");
    const c = attempt.audit_certificate;
    if (c === null || c === undefined) {
      $("domain-status").textContent = "No complete actual audit certificate is attached. No domain counts are shown."; return;
    }
    need(plain(c) && c.schema === "independent-complete-Q-catalogue-point-audit-v1" && c.completed === true &&
      c.all_catalogue_primitive_and_initial_domains_accepted === true && c.bounded_grammar_complete === true,
      "A partial or unrelated certificate cannot populate the domain summary");
    const p = c.initial_point_domains;
    need(plain(p) && p.all_rows === 24 && Array.isArray(p.domain_counts) && p.domain_counts.length === 24 &&
      p.domain_counts.every(n => Number.isSafeInteger(n) && n >= 0) && Array.isArray(p.domain_sha256_by_row) &&
      p.domain_sha256_by_row.length === 24 && p.domain_sha256_by_row.every(h => typeof h === "string" && /^[0-9a-f]{64}$/.test(h)),
      "Complete domain counts and row hashes are required for every row");
    const accepted = attempt.disposition.ROOT_complete_independent_audit_accepted === true;
    $("domain-status").textContent = accepted ? "Complete attached certificate; ROOT’s independent-audit flag is true. Other acceptance scopes remain separate." :
      "Complete attached certificate is displayed as provisional. ROOT acceptance is not inferred from its presence.";
    const [result, body] = table(["Physical row", "Complete legal-domain count", "Canonical domain SHA"], "domains");
    p.domain_counts.forEach((count, row) => {
      const line = node("tr"); const r = node("td"), n = node("td"), h = node("td");
      r.append(node("code", row)); n.append(node("code", count)); h.append(node("code", p.domain_sha256_by_row[row], "hash"));
      line.append(r, n, h); body.append(line);
    });
    $("domain-table").append(result);
    const note = node("p", "Registry provenance: ", "small");
    if (typeof c.formula_registry_sha256 === "string") note.append(node("code", c.formula_registry_sha256, "hash"));
    else note.append(document.createTextNode("not supplied"));
    $("certificate-meta").append(note);
  }
  function renderScopes(records) {
    clear("scopes"); const map = new Map(records.map(record => [record.id, record]));
    need(map.size === records.length && records.every(r => scopeLabels.some(([id]) => id === r.id)), "Invalid scope record");
    scopeLabels.forEach(([id, label]) => {
      const record = map.get(id), card = node("article", undefined, "scope-card");
      card.append(node("h3", label), node("p", record ? record.status_text : "No actual result attached.", record ? "" : "pending"));
      if (record && typeof record.scope_text === "string") card.append(node("p", record.scope_text, "small"));
      if (record && record.evidence_href) { const a = node("a", "Scoped evidence"); a.href = publicHref(record.evidence_href); card.append(a); }
      $("scopes").append(card);
    });
  }
  async function load() {
    const response = await fetch("display-packet-v1.json", {cache: "no-store"});
    need(response.ok, "Display packet is unavailable"); const data = await response.json();
    need(plain(data) && data.schema === SCHEMA && data.presentation_only === true && Array.isArray(data.attempts) &&
      Array.isArray(data.scopes) && Array.isArray(data.evidence_links), "Invalid presentation-only packet");
    $("lead").textContent = data.lead; $("status").textContent = data.status_text;
    if (typeof data.formula_latex === "string" && data.formula_latex.length) {
      $("statement").hidden = false; $("statement").replaceChildren(math(data.formula_latex));
    }
    data.attempts.forEach(a => need(plain(a) && typeof a.id === "string" && typeof a.label === "string" &&
      typeof a.status_text === "string" && plain(a.disposition) && Array.isArray(a.raw_closure_links), "Incomplete saved attempt attachment"));
    need(new Set(data.attempts.map(a => a.id)).size === data.attempts.length, "Repeated attempt ID");
    renderCosts(data.attempts); renderScopes(data.scopes); links($("evidence-links"), data.evidence_links);
    const select = $("attempt");
    if (data.attempts.length) {
      select.replaceChildren(); select.disabled = false;
      data.attempts.forEach((a, i) => { const option = node("option", a.label); option.value = String(i); select.append(option); });
      select.value = String(data.attempts.length - 1);
      const render = async () => {
        const a = data.attempts[Number(select.value)];
        renderFlags(a); renderPhases(a); renderDomains(a); links($("attempt-links"), a.raw_closure_links);
        await typeset();
      };
      select.addEventListener("change", () => render().catch(showError)); await render();
    } else {
      $("flags").append(node("p", "No saved flags attached.", "pending"));
      renderPhases({phase_trace: []}); links($("attempt-links"), []); await typeset();
    }
  }
  function showError(error) {
    $("status").textContent = `Display attachment failed: ${error.message}`;
    $("status").classList.add("flag-false");
    clear("domain-table"); clear("certificate-meta");
    $("domain-status").textContent = "No domain summary is accepted from this failed display attachment.";
  }
  load().catch(showError);
})();
