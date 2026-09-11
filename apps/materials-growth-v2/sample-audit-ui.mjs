import { sampleCatalog } from "./samples.mjs?v=sample-families-1";
const target = document.getElementById("sample-audit-table");
try {
  const response = await fetch(
    "strict-sample-results.json?v=sample-families-1",
  );
  if (!response.ok) throw Error("Audit unavailable");
  const report = await response.json();
  const table = document.createElement("table");
  const head = table.createTHead().insertRow();
  for (const label of [
    "Sample",
    "Result",
    "Atoms",
    "Corona",
    "RDF error",
    "Reference sites",
    "Point / overlap audit",
  ]) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = label;
    head.append(th);
  }
  const body = table.createTBody();
  for (const r of report.results) {
    const row = body.insertRow();
    for (const value of [
      sampleCatalog.find((s) => s[0] === r.id)?.[1] || r.id,
      (r.outcome || r.status) +
        (r.outcome !== "finite growth verified"
          ? ` · ${r.message || r.status}`
          : ""),
      r.atoms ?? "—",
      r.completedCorona ?? "—",
      Number.isFinite(r.metrics?.rdfError)
        ? r.metrics.rdfError.toFixed(3)
        : "—",
      r.periodicReference
        ? `${r.periodicReference.matched}/${r.periodicReference.total}`
        : "Not tested",
      r.legal && r.overlapsLegal ? "Pass" : "Not established",
    ])
      row.insertCell().textContent = String(value);
  }
  target.replaceChildren(table);
} catch {
  target.textContent =
    "The current audit could not be loaded. Please retry or download the report.";
}
