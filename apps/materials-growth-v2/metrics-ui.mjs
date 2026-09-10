const $ = (id) => document.getElementById(id),
  format = (x) => (Number.isFinite(x) ? x.toFixed(3) : "not available");
let metrics = null;
export function renderMetrics(value) {
  metrics = value;
  const select = $("rdf-channel"),
    selected = select.value,
    keys = ["total", ...Object.keys(value?.reference?.partials || {})];
  if (
    JSON.stringify([...select.options].map((o) => o.value)) !==
    JSON.stringify(keys)
  ) {
    select.replaceChildren();
    for (const key of keys) {
      const o = document.createElement("option");
      o.value = key;
      o.textContent = key === "total" ? "Total RDF" : JSON.parse(key).join("–");
      select.append(o);
    }
    if (keys.includes(selected)) select.value = selected;
  }
  select.onchange = draw;
  const out = $("metric-stats");
  out.replaceChildren();
  if (value?.status === "measured") {
    for (const [label, text] of [
      [
        "Window",
        `${value.dimension}D · radius ${value.radius.toFixed(2)} Å · ${value.reference.atoms} reference / ${value.generated.atoms} grown atoms`,
      ],
      ["RDF relative L1 error", format(value.rdfError)],
      ["Composition total variation", format(value.compositionTV)],
      ["Four-neighbor angular TV", format(value.angleTV)],
      [
        "Median nearest-neighbor distance",
        `${format(value.reference.nearMedian)} → ${format(value.generated.nearMedian)} Å`,
      ],
      [
        "Mean coordination",
        `${format(value.reference.coordinationMean)} → ${format(value.generated.coordinationMean)} (cutoff ${value.coordCutoff.toFixed(2)} Å)`,
      ],
    ]) {
      const p = document.createElement("p");
      p.textContent = `${label}: ${text}`;
      out.append(p);
    }
  } else
    out.textContent =
      value?.status ||
      "Waiting for at least 24 grown atoms. No score is assigned to a single atom.";
  draw();
}
function draw() {
  const canvas = $("rdf-chart"),
    c = canvas.getContext("2d");
  c.clearRect(0, 0, canvas.width, canvas.height);
  c.font = "16px system-ui";
  c.fillStyle = "#657d85";
  if (metrics?.status !== "measured") {
    c.fillText("RDF appears when the common window has enough atoms.", 28, 110);
    return;
  }
  const key = $("rdf-channel").value,
    a =
      key === "total" ? metrics.reference.rdf : metrics.reference.partials[key],
    b =
      key === "total" ? metrics.generated.rdf : metrics.generated.partials[key];
  if (!a || !b) {
    c.fillText("Insufficient pairs for this label channel.", 28, 110);
    return;
  }
  const max = Math.max(...a, ...b, 0.001),
    left = 48,
    right = 695,
    top = 24,
    bottom = 207;
  c.strokeStyle = "#c9d8db";
  c.beginPath();
  c.moveTo(left, top);
  c.lineTo(left, bottom);
  c.lineTo(right, bottom);
  c.stroke();
  c.fillText("g(r)", 5, 20);
  c.fillText(max.toFixed(1), 5, top + 20);
  c.fillText("0", 20, bottom + 4);
  c.fillText(`${metrics.rmax.toFixed(2)} Å`, right - 55, bottom + 28);
  for (const [series, color] of [
    [a, "#147c7c"],
    [b, "#ce8e27"],
  ]) {
    c.strokeStyle = color;
    c.lineWidth = 2;
    c.beginPath();
    series.forEach((v, i) => {
      const x = left + ((right - left) * (i + 0.5)) / series.length,
        y = bottom - (v / max) * (bottom - top);
      i ? c.lineTo(x, y) : c.moveTo(x, y);
    });
    c.stroke();
  }
  c.fillStyle = "#657d85";
  c.fillText(
    `Channel relative L1: ${format(key === "total" ? metrics.rdfError : metrics.partialErrors[key])}`,
    300,
    18,
  );
}
export async function loadBenchmarks() {
  try {
    const response = await fetch("benchmark-results.json");
    if (!response.ok) throw Error(response.status);
    const report = await response.json(),
      table = document.createElement("table"),
      head = document.createElement("tr");
    for (const label of [
      "Material",
      "Atoms",
      "RDF error",
      "Composition TV",
      "Angular TV",
      "Result",
    ]) {
      const th = document.createElement("th");
      th.textContent = label;
      head.append(th);
    }
    table.append(head);
    for (const row of report.results) {
      const tr = document.createElement("tr");
      for (const text of [
        row.name,
        row.atoms,
        format(row.rdfError),
        format(row.compositionTV),
        format(row.angleTV),
        row.status === "searching" ? "step/time checkpoint" : row.status,
      ]) {
        const td = document.createElement("td");
        td.textContent = text;
        tr.append(td);
      }
      table.append(tr);
    }
    $("benchmark-table").replaceChildren(table);
  } catch (error) {
    $("benchmark-table").textContent =
      "Benchmark artifact unavailable; live comparisons still work.";
  }
}
