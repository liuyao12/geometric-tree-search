const generate = document.querySelector("#generate");
const download = document.querySelector("#download");
const status = document.querySelector("#status");
let exportJSON = null, exportRadius = null;
const worker = new Worker(new URL("./worker.js", import.meta.url), { type: "module" });

const texScalar = ([a, b, d]) => {
  let numerator = a === "0" ? "" : a;
  if (b !== "0") numerator += `${b.startsWith("-") || !numerator ? "" : "+"}${b}\\tau`;
  numerator ||= "0";
  return d === "1" ? numerator : `\\frac{${numerator}}{${d}}`;
};
const texPoint = p => `\\left(${p.map(texScalar).join(",\\;")}\\right)`;

generate.onclick = () => {
  exportJSON = null;
  generate.disabled = true; download.disabled = true;
  document.querySelector("#summary").replaceChildren();
  document.querySelector("#sample-details").hidden = true;
  status.textContent = "Constructing triple intersections with exact arithmetic…";
  exportRadius = Number(document.querySelector("#radius").value);
  worker.postMessage({ radius: exportRadius });
};

worker.onmessage = async ({ data }) => {
  generate.disabled = false;
  if (!data.ok) { status.textContent = data.error; return; }
  exportJSON = data.json; download.disabled = false;
  status.textContent = "Exact finite patch generated. All coefficients are preserved in the download.";
  const fields = [["Tiles", data.count], ["Prolate", data.counts.prolate], ["Oblate", data.counts.oblate],
    ["Global grid regularity", data.regular ? "Certified" : "Inconclusive"]];
  const summary = document.querySelector("#summary");
  for (const [label, value] of fields) {
    const dt = document.createElement("dt"), dd = document.createElement("dd");
    dt.textContent = label; dd.textContent = String(value); summary.append(dt, dd);
  }
  const sample = document.querySelector("#sample");
  sample.textContent = `\\[\\begin{aligned}${data.sample.vertices.map((p, i) => `v_{${i}}&=${texPoint(p)}`).join("\\\\")}\\end{aligned}\\]`;
  document.querySelector("#sample-details").hidden = false;
  // MathJax may still be loading from the shared CDN on first generation.
  if (window.MathJax?.typesetPromise) await window.MathJax.typesetPromise([sample]);
};
worker.onerror = () => {
  generate.disabled = false; download.disabled = true;
  status.textContent = "The construction worker could not load. Reload the page to retry.";
};

document.querySelector("#sample-details").ontoggle = async event => {
  if (event.target.open && window.MathJax?.typesetPromise) await window.MathJax.typesetPromise([document.querySelector("#sample")]);
};
download.onclick = () => {
  if (!exportJSON) return;
  const url = URL.createObjectURL(new Blob([exportJSON], { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = `icosahedral-exact-radius-${exportRadius}.json`;
  anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
};
