import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  samplePatch,
  sampleCatalog,
  sampleFamilies,
  samplesInFamily,
} from "./samples.mjs?v=sample-families-1";
import "./sample-audit-ui.mjs?v=sample-families-1";
import { centralSeed } from "./seed.mjs";
import { renderMetrics, loadBenchmarks } from "./metrics-ui.mjs";
import { parseStructureText } from "../iqc-growth-live/structure-io.js";
const $ = (id) => document.getElementById(id),
  worker = new Worker(
    new URL("./worker.mjs?v=sample-audit-1", import.meta.url),
    {
      type: "module",
    },
  );
let atoms = [],
  latestAtoms = null,
  grammar,
  marking,
  sections = [],
  curve = [],
  overlapCurve = [],
  stage = 0,
  busy = false,
  growthRunning = false,
  highlight = new Set();
const palette = {
    H: "#e6e9ed",
    D: "#cdd6df",
    O: "#e35050",
    C: "#505e70",
    B: "#e49a9a",
    N: "#3050f8",
    Si: "#d9b58f",
    Fe: "#d86c37",
    Cs: "#7650bd",
    Na: "#aa79df",
    Cl: "#62b969",
    Cd: "#d4b862",
    Yb: "#579eae",
    Cu: "#bc8559",
    Zr: "#78aaa8",
  },
  color = (s) => palette[s] || "#739cc3";
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setClearColor(0xf6f9fa);
$("scene").append(renderer.domElement);
const scene = new THREE.Scene(),
  camera = new THREE.PerspectiveCamera(40, 1, 0.05, 10000),
  controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x8da4b4, 2.7));
const light = new THREE.DirectionalLight(0xffffff, 2);
light.position.set(20, 30, 40);
scene.add(light);
let group = new THREE.Group();
scene.add(group);
const sphere = new THREE.SphereGeometry(1, 16, 12);
function showAtoms(list, fit = false) {
  scene.remove(group);
  group.traverse((x) => x.material?.dispose());
  group = new THREE.Group();
  scene.add(group);
  const buckets = new Map();
  list.forEach((a, i) => {
    const k = highlight.has(i) ? "#f2ac44" : color(a.species);
    if (!buckets.has(k)) buckets.set(k, []);
    buckets.get(k).push(a);
  });
  for (const [tint, rows] of buckets) {
    const mesh = new THREE.InstancedMesh(
        sphere,
        new THREE.MeshStandardMaterial({ color: tint, roughness: 0.42 }),
        rows.length,
      ),
      dummy = new THREE.Object3D();
    rows.forEach((a, i) => {
      dummy.position.set(...a.position);
      dummy.scale.setScalar(0.27);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    });
    group.add(mesh);
  }
  if (fit && list.length) {
    const box = new THREE.Box3().setFromObject(group),
      center = box.getCenter(new THREE.Vector3()),
      size = Math.max(12, box.getSize(new THREE.Vector3()).length());
    controls.target.copy(center);
    camera.position
      .copy(center)
      .add(
        new THREE.Vector3(0.7, 0.45, 1).normalize().multiplyScalar(size * 1.45),
      );
    camera.far = Math.max(10000, size * 20);
    camera.updateProjectionMatrix();
    controls.update();
  }
}
const resize = new ResizeObserver(() => {
  const b = $("scene").getBoundingClientRect();
  if (b.width && b.height) {
    renderer.setSize(b.width, b.height, false);
    camera.aspect = b.width / b.height;
    camera.updateProjectionMatrix();
  }
});
resize.observe($("scene"));
function status(text) {
  $("status").textContent = text;
}
function setStage(n) {
  stage = n;
  document
    .querySelectorAll("[data-stage]")
    .forEach((b) => b.classList.toggle("active", +b.dataset.stage === n));
  document
    .querySelectorAll("[data-panel]")
    .forEach((p) => (p.hidden = +p.dataset.panel !== n));
  $("scene").hidden = n === 2;
  $("gallery").hidden = n !== 2 && !(n === 1 && grammar);
  $("scene").classList.toggle("with-clusters", n === 1 && !!grammar);
  $("evaluation").hidden = n !== 3;
  $("view-label").textContent = [
    "OBSERVED PATCH",
    "REGISTRATION IN PROGRESS",
    "ONE SCENE PER LOCAL SUPPORT",
    "CURRENT SEARCH BRANCH",
  ][n];
  $("view-title").textContent = [
    "Atoms, before assumptions.",
    "Repetition under rotation.",
    "Markings over neighborhoods.",
    "One seed. Geometry-led growth.",
  ][n];
  if (n < 2) {
    highlight.clear();
    showAtoms(atoms, true);
  }
  if (n === 2 || (n === 1 && grammar)) gallery();
  if (n === 3) {
    highlight.clear();
    showAtoms(latestAtoms || [centralSeed(atoms).atom], true);
  }
}
document
  .querySelectorAll("[data-stage]")
  .forEach((b) => (b.onclick = () => setStage(+b.dataset.stage)));
$("to-clusters").onclick = () => setStage(1);
$("to-learning").onclick = () => setStage(2);
$("to-growth").onclick = () => setStage(3);
function invalidate() {
  growthRunning = false;
  $("grow").textContent = "Run";
  latestAtoms = null;
  grammar = marking = null;
  $("gallery").replaceChildren();
  $("gallery").hidden = stage !== 2;
  $("scene").classList.remove("with-clusters");
  sections = [];
  curve = [];
  overlapCurve = [];
  worker.postMessage({ kind: "reset" });
  for (const id of ["learn", "to-learning", "grow", "to-growth", "export"])
    $(id).disabled = true;
  $("cluster-stats").textContent = "Not yet identified";
  $("learning-stats").textContent = "No training samples yet";
  $("growth-stats").textContent = "No placements yet";
  renderMetrics(null);
}
function load(data) {
  invalidate();
  atoms = data.atoms;
  $("source").textContent = data.source || "Imported atomic coordinates";
  $("sample-count").textContent =
    `${atoms.length} observed atoms · ${new Set(atoms.map((a) => a.species)).size} label channels`;
  $("legend").replaceChildren();
  for (const s of new Set(atoms.map((a) => a.species))) {
    const span = document.createElement("span"),
      dot = document.createElement("i");
    dot.style.background = color(s);
    span.append(dot, document.createTextNode(s));
    $("legend").append(span);
  }
  highlight.clear();
  showAtoms(atoms, true);
  status(data.name || "Imported sample");
}
$("sample").onchange = () => load(samplePatch($("sample").value));
$("file").onchange = async () => {
  try {
    const f = $("file").files[0];
    if (!f) return;
    const raw = parseStructureText(await f.text(), f.name);
    load({ ...raw, atoms: raw.atoms || raw.sites, name: f.name });
  } catch (e) {
    status(e.message);
  }
};
for (const name of ["epsilon", "error"])
  $(name).oninput = () => {
    $(`${name}-label`).value = $(name).value;
  };
$("epsilon").onchange = $("neighbors").onchange = () => invalidate();
$("boundary-policy").onchange = () => invalidate();
$("error").onchange = () => {
  latestAtoms = null;
  renderMetrics(null);
  $("growth-stats").textContent = "No placements yet";
  $("export").disabled = true;
  marking = null;
  worker.postMessage({ kind: "reset" });
  $("grow").disabled = $("to-growth").disabled = true;
};
function lock(value) {
  busy = value;
  for (const id of [
    "discover",
    "sample",
    "sample-family",
    "file",
    "epsilon",
    "neighbors",
    "boundary-policy",
    "learn",
    "error",
  ])
    $(id).disabled = value || (id === "learn" && !grammar);
}
$("discover").onclick = () => {
  invalidate();
  lock(true);
  status("Registering observed neighborhoods…");
  worker.postMessage({
    kind: "discover",
    atoms,
    options: {
      epsilon: +$("epsilon").value,
      neighbors: +$("neighbors").value,
      boundaryPolicy: $("boundary-policy").value,
    },
  });
};
$("learn").onclick = () => {
  overlapCurve = [];
  latestAtoms = null;
  renderMetrics(null);
  $("growth-stats").textContent = "No placements yet";
  $("export").disabled = true;
  marking = null;
  $("grow").disabled = $("to-growth").disabled = true;
  curve = [];
  lock(true);
  status("Fitting empirical local sections…");
  worker.postMessage({
    kind: "learn",
    options: { error: +$("error").value, epochs: 24, observedOnly: true },
  });
};
$("grow").onclick = () => {
  if (growthRunning) {
    $("grow").disabled = true;
    status("Pausing after the current search transaction…");
    worker.postMessage({ kind: "pause" });
    return;
  }
  lock(true);
  growthRunning = true;
  $("grow").textContent = "Pause";
  $("grow").disabled = false;
  for (const id of ["marking", "angle"]) $(id).disabled = true;
  status("Searching; automatic pauses at completed coronas 3, 5, 7, …");
  worker.postMessage({
    kind: "grow",
    options: {
      marked: $("marking").value === "yes",
      angularReach: +$("angle").value,
      seedMode: "single",
      maximumPoints: 20000,
      maximumCandidates: 40000,
      softMemory: true,
    },
  });
};
$("reset").onclick = () => {
  growthRunning = false;
  $("grow").textContent = "Run";
  latestAtoms = null;
  $("growth-stats").textContent = "No placements yet";
  worker.postMessage({ kind: "reset" });
  lock(false);
  for (const id of ["marking", "angle"]) $(id).disabled = false;
  $("grow").disabled = !marking;
  $("export").disabled = true;
  highlight.clear();
  showAtoms([centralSeed(atoms).atom], true);
  renderMetrics(null);
  status("Search reset; the learned marking is retained");
};
for (const id of ["marking", "angle"])
  $(id).onchange = () => $("reset").click();
$("export").onclick = () => worker.postMessage({ kind: "export" });
worker.onmessage = ({ data: d }) => {
  if (d.kind === "error") {
    lock(false);
    growthRunning = false;
    $("grow").textContent = "Continue";
    $("grow").disabled = !marking;
    status(`Unresolved: ${d.message}`);
  }
  if (d.kind === "discovery") {
    highlight = new Set(d.ids);
    if (stage === 1) showAtoms(atoms);
    status(`Registering ${d.done} / ${d.total} observed neighborhoods`);
  }
  if (d.kind === "discovered") {
    grammar = d.grammar;
    $("channel").replaceChildren();
    for (const [i, label] of [...new Set(atoms.map((a) => a.species))]
      .sort()
      .entries()) {
      const option = document.createElement("option");
      option.value = i;
      option.textContent = label;
      $("channel").append(option);
    }
    lock(false);
    highlight.clear();
    if (stage < 2) showAtoms(atoms);
    $("to-learning").disabled = $("learn").disabled = !grammar.types.length;
    $("cluster-stats").textContent =
      `${grammar.types.length} retained motifs · ${grammar.types.reduce((n, t) => n + t.occurrences.length, 0)} complete observations · ${grammar.discovery?.partialObservations.length || 0} possible crop-fragment classes · ${grammar.residuals.length} uncovered observed atoms`;
    const coverage = grammar.discovery?.coverage;
    if (coverage)
      $("cluster-stats").textContent +=
        ` · ${grammar.types.filter((t) => t.role === "connector").length} connector motifs · atoms covered ${coverage.coveredAtoms}/${coverage.atoms} · placement anchors ${coverage.anchoredAtoms}/${coverage.atoms} · ${coverage.supportComponents} observed support components (not volume coverage)`;
    if (grammar.discovery?.contextCompletion)
      $("cluster-stats").textContent +=
        ` · ${grammar.discovery.contextCompletion.classes} broader observed context classes added for disconnected supports / missing anchors`;
    if (stage === 1) {
      $("gallery").hidden = false;
      $("scene").classList.add("with-clusters");
      gallery();
    }
    status(
      `Identification finished. ${grammar.residuals.length ? "Coverage incomplete; no reconstruction guarantee." : "Observed atoms covered; anchor-domain coverage is checked by search."}`,
    );
  }
  if (d.kind === "learning") {
    sections = d.sections;
    curve.push(d.loss);
    drawCurve();
    if (stage === 2 && !$("gallery").children.length) gallery();
    $("learning-stats").textContent =
      `Epoch ${d.epoch} / ${d.epochs} · MSE ${d.loss.toExponential(3)}`;
  }
  if (d.kind === "overlap-learning") {
    overlapCurve.push(d.classes);
    drawCurve();
    $("learning-stats").textContent =
      `${d.pairs} observed overlapping pairs · ${d.classes} geometric relation classes · ${d.done}/${d.total} occurrences processed`;
    status(
      "Learning observed-only overlap relations; unseen connections will be rejected.",
    );
  }
  if (d.kind === "learned") {
    growthRunning = false;
    $("grow").textContent = "Run";
    marking = d.marking;
    sections = marking.sections;
    lock(false);
    $("grow").disabled = $("to-growth").disabled = false;
    $("learning-stats").textContent =
      `${marking.overlapRules?.pairs || 0} observed overlapping pairs · ${marking.overlapRules?.classes || 0} geometric relation classes · observed-only connections · ${marking.labels.length} auxiliary label channels`;
    gallery();
    status(
      "Observed-only rules trained. Unseen overlapping geometries are forbidden in this computational model; no physics or chemistry is assumed.",
    );
  }
  if (d.kind === "snapshot") {
    const s = d.state;
    latestAtoms = s.atoms;
    renderMetrics(s.metrics);
    highlight.clear();
    if (stage === 3) showAtoms(s.atoms);
    $("growth-stats").textContent =
      `1 seed + ${s.atoms.length - 1} new atoms · ${s.frontier.length} frontier obligations · ${s.stats.branches} branches · ${s.stats.backtracks} backtracks · ${s.stats.forced} certified forced · ${s.unresolved} unresolved domains · ${s.candidateCount} cached candidates · independent check: ${s.validation.legal ? "legal partial assignment" : "INVALID"}`;
    $("export").disabled = false;
    if (s.overlapValidation)
      $("growth-stats").textContent +=
        ` · observed-overlap audit: ${s.overlapValidation.legal ? "pass" : "FAIL"} (${s.overlapValidation.checked} pairs) · ${s.overlapChecks.rejections} rejection evaluations`;
    status(
      `${s.status}${d.event?.message ? " — " + d.event.message : ""} · ${d.paused ? "paused" : "running"}`,
    );
    if (d.paused) {
      growthRunning = false;
      $("grow").textContent = "Continue";
      lock(false);
      $("grow").disabled = ["unknown", "exhausted", "complete"].includes(
        d.event?.kind,
      );
    }
  }
  if (d.kind === "artifact") {
    const url = URL.createObjectURL(
        new Blob([JSON.stringify(d.state)], { type: "application/json" }),
      ),
      a = document.createElement("a");
    a.href = url;
    a.download = "gcts-v2-audit.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
};
worker.onerror = (e) => {
  lock(false);
  status(`Worker error: ${e.message}`);
};
function drawCurve() {
  const c = $("curve"),
    ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.fillStyle = "#68818a";
  ctx.font = "18px system-ui";
  ctx.fillText(
    overlapCurve.length
      ? "Observed overlap classes learned"
      : "Auxiliary label fit MSE (log scale)",
    12,
    24,
  );
  ctx.strokeStyle = "#147c7c";
  ctx.lineWidth = 3;
  ctx.beginPath();
  const values = overlapCurve.length ? overlapCurve : curve;
  values.forEach((v, i) => {
    const x = 20 + (i / Math.max(1, values.length - 1)) * 475,
      y = overlapCurve.length
        ? 170 - (125 * v) / Math.max(1, ...values)
        : 45 + (Math.min(12, -Math.log10(Math.max(v, 1e-12))) / 12) * 125;
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.stroke();
}
function gallery() {
  if (!grammar) return;
  $("gallery").replaceChildren();
  for (const type of grammar.types) {
    const f = document.createElement("figure"),
      c = document.createElement("canvas"),
      cap = document.createElement("figcaption");
    c.width = 400;
    c.height = 340;
    c.dataset.type = type.id;
    c.setAttribute(
      "aria-label",
      `Rotating motif ${type.id + 1}, ${type.sites.length} atoms`,
    );
    cap.textContent = `${type.role === "connector" ? "Connector" : type.role === "context" ? "Growth context" : "Local motif"} ${type.id + 1} · ${type.sites.length} sites · ${type.occurrences.length} observations`;
    f.append(c, cap);
    if (stage === 1) {
      const select = document.createElement("button");
      select.textContent = "Highlight observations";
      select.onclick = () => {
        highlight = new Set(type.occurrences.flatMap((o) => o.ids));
        showAtoms(atoms);
      };
      f.append(select);
    }
    $("gallery").append(f);
  }
  if (!grammar.types.length)
    $("gallery").textContent =
      "No recurring motifs resolved at this tolerance.";
  if (stage === 1 && grammar.discovery?.partialObservations.length) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent =
      "Inspect possible crop fragments (not used as growth motifs)";
    details.append(summary);
    grammar.discovery.partialObservations.forEach((p, i) => {
      const f = document.createElement("figure"),
        c = document.createElement("canvas"),
        cap = document.createElement("figcaption");
      c.width = 400;
      c.height = 340;
      c.dataset.partial = i;
      cap.textContent = `${p.sites.length} sites · ${p.anchors.length} observations · possible truncation, not a certified surface classification`;
      f.append(c, cap);
      details.append(f);
    });
    $("gallery").append(details);
  }
}
function drawGallery(time) {
  for (const c of $("gallery").querySelectorAll("canvas")) {
    const partial = c.dataset.partial !== undefined,
      type = partial
        ? grammar.discovery.partialObservations[+c.dataset.partial]
        : grammar.types[+c.dataset.type],
      ctx = c.getContext("2d"),
      r = Math.max(...type.sites.map((s) => Math.hypot(...s.position)), 1),
      angle = time * 0.00018,
      co = Math.cos(angle),
      si = Math.sin(angle);
    ctx.clearRect(0, 0, 400, 340);
    const pts = type.sites
      .map((s, i) => {
        const [x, y, z] = s.position;
        return {
          i,
          s,
          x: 200 + ((co * x + si * z) / r) * 115,
          y: 160 + ((y * 0.85 + (co * z - si * x) * 0.25) / r) * 115,
          z: co * z - si * x,
        };
      })
      .sort((a, b) => a.z - b.z);
    for (const p of pts) {
      const values = sections[type.id]?.sites[p.i]?.values || [],
        v = values[+$("channel").value] ?? 0.5;
      if (stage === 2) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 18, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(28,156,157,${0.04 + v * 0.18})`;
        ctx.fill();
        ctx.strokeStyle = `rgba(28,156,157,${0.2 + v * 0.5})`;
        ctx.stroke();
      }
      ctx.beginPath();
      ctx.arc(p.x, p.y, stage === 1 ? 12 : 7, 0, Math.PI * 2);
      ctx.fillStyle = color(p.s.species);
      ctx.fill();
      ctx.strokeStyle = "#6d858d";
      ctx.stroke();
    }
    ctx.fillStyle = "#789097";
    ctx.font = "16px system-ui";
    ctx.fillText(
      stage === 2
        ? "auxiliary occupancy · rotating coordinates"
        : partial
          ? "partial observation · rotating coordinates"
          : "geometric motif · rotating coordinates",
      20,
      320,
    );
  }
}
function animate(time) {
  requestAnimationFrame(animate);
  controls.update();
  if (stage !== 2) renderer.render(scene, camera);
  if ((stage === 1 || stage === 2) && grammar) drawGallery(time);
}
requestAnimationFrame(animate);
for (const [id, name, ids] of sampleFamilies)
  $("sample-family").add(new Option(`${name} (${ids.length})`, id));
function populateSamples() {
  const previous = $("sample").value,
    family = $("sample-family").value;
  $("sample").replaceChildren();
  for (const [id, name] of sampleFamilies) {
    if (family !== "all" && family !== id) continue;
    const group = document.createElement("optgroup");
    group.label = name;
    for (const [key, label] of samplesInFamily(id))
      group.append(new Option(label, key));
    $("sample").append(group);
  }
  const available = samplesInFamily(family);
  $("sample").value = available.some((s) => s[0] === previous)
    ? previous
    : available[0][0];
  $("sample-library-count").textContent =
    `${available.length} of ${sampleCatalog.length} examples`;
  return previous !== $("sample").value;
}
populateSamples();
$("sample-family").onchange = () => {
  if (populateSamples()) load(samplePatch($("sample").value));
};
$("fit-view").onclick = () => {
  if (stage !== 2)
    showAtoms(
      stage === 3 ? latestAtoms || [centralSeed(atoms).atom] : atoms,
      true,
    );
};
loadBenchmarks();
load(samplePatch("nacl"));
