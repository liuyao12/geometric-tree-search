"use strict";
const data = JSON.parse(document.getElementById("saved-data").textContent);
const picker = document.getElementById("audit-picker");
const chart = document.getElementById("row-chart");
const body = document.getElementById("row-table");
const status = document.getElementById("audit-status");
const math = value => `\\(${value}\\)`;
const cell = value => { const td = document.createElement("td"); td.textContent = value; return td; };
const names = ["Pristine boundary", "After first legal placement", "After exact rollback", "Pending reader transaction — incomplete"];
data.audits.forEach((audit, i) => { const option = document.createElement("option"); option.value = i; option.textContent = names[i]; picker.appendChild(option); });
let rendering = Promise.resolve();
function render() {
  const audit = data.audits[Number(picker.value)];
  rendering = rendering.then(async () => {
    if (window.MathJax?.startup?.promise) await MathJax.startup.promise;
    if (window.MathJax?.typesetClear) MathJax.typesetClear([chart, body, status]);
    chart.replaceChildren(); body.replaceChildren();
    const scale = Math.max(...audit.rows.map(row => row.row_inclusive_before_checkpoint_ns));
    for (let r = 0; r < 24; r++) {
      const row = audit.rows.find(x => x.row === r);
      const line = document.createElement("div"); line.className = "chart-row";
      const label = document.createElement("span"); label.textContent = math(`r=${r}`);
      const bar = document.createElement("div"); bar.className = "bar";
      const duration = document.createElement("span");
      if (row) {
        for (const [key, color] of [["candidate_enumeration_ns", "blue"], ["point_and_identity_comparison_ns", "orange"], ["factor_comparison_ns", "purple"]]) {
          const segment = document.createElement("span"); segment.className = color; segment.style.width = `${100 * row[key] / scale}%`; bar.appendChild(segment);
        }
        duration.textContent = math(`${(row.row_inclusive_before_checkpoint_ns / 1e9).toFixed(3)}\\,\\mathrm{s}`);
        const tr = document.createElement("tr");
        for (const text of [math(r), math(row.observed_keys), math((row.candidate_enumeration_ns / 1e6).toFixed(3)), math((row.point_and_identity_comparison_ns / 1e6).toFixed(3)), math((row.factor_comparison_ns / 1e6).toFixed(3))]) tr.appendChild(cell(text));
        body.appendChild(tr);
      } else { bar.classList.add("missing"); duration.textContent = "No EOF"; }
      line.append(label, bar, duration); chart.appendChild(line);
    }
    status.textContent = audit.completed
      ? `Saved complete audit: ${math("24")} rows, ${math(audit.summary.keys)} candidate placements, ${math((audit.summary.inclusive_before_checkpoint_ns / 1e9).toFixed(3) + "\\,\\mathrm{s}")}. Diagnostic completion within an unqualified experiment.`
      : `Saved partial audit: ${math(audit.rows.length)} row EOF records. Missing rows have no inferred duration or result. The entire experiment remains UNKNOWN.`;
    if (window.MathJax?.typesetPromise) await MathJax.typesetPromise([chart, body, status]);
  }).catch(error => { document.getElementById("render-status").textContent = `Display error: ${error.message}`; });
}
picker.addEventListener("change", render);
render();
