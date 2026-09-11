const $ = (id) => document.getElementById(id);
const median = (values) =>
  [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
const format = (n) => n.toLocaleString("en-US", { maximumFractionDigits: 1 });
const names = { nacl: "NaCl", ice: "Ice VIII", copper: "Copper" };
$("print").addEventListener("click", () => window.print());
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function compare(data) {
  const id = $("material").value,
    metric = $("metric").value;
  const rows = data.results.filter((r) => r.id === id);
  const values = (mode) =>
    rows
      .filter((r) => r.mode === mode)
      .map((r) => (metric === "checks" ? r.checks : r.milliseconds[metric]));
  const global = values("global"),
    local = values("local"),
    maximum = Math.max(median(global), median(local));
  const region = $("comparison");
  region.replaceChildren();
  for (const [mode, values, label] of [
    ["global", global, "Global revalidation"],
    ["local", local, "Dependency-local"],
  ]) {
    const row = el("div", "bar-row"),
      labelRow = el("div", "bar-label");
    labelRow.append(
      el("span", "", label),
      el(
        "strong",
        "",
        `${format(median(values))}${metric === "checks" ? " checks" : " ms"}`,
      ),
    );
    const track = el("div", "track"),
      bar = el("div", `bar ${mode}`);
    bar.style.width = `${(median(values) / maximum) * 100}%`;
    track.setAttribute("aria-hidden", "true");
    track.append(bar);
    row.append(labelRow, track);
    row.append(
      el(
        "div",
        "bar-note",
        metric === "checks"
          ? "Same count in all three trials"
          : `Observed range ${format(Math.min(...values))}–${format(Math.max(...values))} ms · trials: ${values.map(format).join(", ")}`,
      ),
    );
    region.append(row);
  }
  const ratio = median(global) / median(local);
  region.append(
    el(
      "p",
      "result-note",
      `${names[id]}: ${ratio.toFixed(2)}× ${metric === "checks" ? "fewer validity checks" : "baseline/local time ratio"}. All three paired trace and state comparisons match.`,
    ),
  );
}
function quality(data) {
  const atoms = [64, 128, 220][Number($("milestone").value)];
  $("atom-count").value = `${atoms} atoms`;
  const container = $("quality-chart");
  container.replaceChildren();
  const grid = el("div", "quality-grid");
  for (const strict of [false, true]) {
    const row = data.rows.find(
      (r) => r.atoms === atoms && r.observedOnly === strict,
    );
    const card = el("div", "quality-card");
    card.append(
      el("h3", "", strict ? "Observed-overlap restricted" : "Occupancy-only"),
      el("strong", "", `${(row.periodic.fraction * 100).toFixed(0)}%`),
      el(
        "small",
        "",
        `${row.periodic.matched}/${row.periodic.total} reference-compatible sites`,
      ),
    );
    const composition = el("div", "composition"),
      oxygen = el("span");
    oxygen.style.width = `${(row.counts.O / atoms) * 100}%`;
    composition.setAttribute("aria-hidden", "true");
    composition.append(oxygen);
    card.append(
      composition,
      el(
        "div",
        "legend",
        `O ${row.counts.O} (rust) · D ${row.counts.D} (blue)`,
      ),
      el("div", "legend", `Completed corona: ${row.corona}`),
    );
    grid.append(card);
  }
  container.append(grid);
}
try {
  const [benchmark, ice] = await Promise.all(
    ["results.json", "quality.json"].map(async (url) => {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`Cannot load ${url}`);
      return r.json();
    }),
  );
  if (benchmark.results.length !== 18 || ice.rows.length !== 6)
    throw new Error("Unexpected result dimensions");
  compare(benchmark);
  quality(ice);
  for (const id of ["material", "metric"])
    $(id).addEventListener("change", () => compare(benchmark));
  $("milestone").addEventListener("input", () => quality(ice));
} catch (error) {
  $("comparison").textContent =
    "Interactive data could not load. All primary results remain in Tables 1 and 2; use the raw-data links below.";
  $("quality-chart").textContent =
    "See Table 1 for the complete ice measurements.";
  console.error(error);
}
