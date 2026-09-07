import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { samplePatch } from "./continuous-samples.mjs";
import {
  validateAtoms,
  distance,
  sub,
  cross,
  dot,
  norm,
} from "./continuous-geometry.mjs";
import { parseStructureText } from "./structure-io.js";
import { randomNomadStructure } from "./structure-database.js";
import { PERIODIC_ELEMENTS } from "./periodic-table.js";
const $ = (id) => document.getElementById(id);
const colors = {
  Na: "#ab80ef",
  Cl: "#62d879",
  O: "#ed6266",
  H: "#e7eef4",
  D: "#bfe9ee",
  C: "#a3abb8",
  Cd: "#f1c784",
  Yb: "#71bdcb",
  Cu: "#dc9666",
  Zr: "#8dccd2",
};
const color = (s) => colors[s] || "#9fb7d8";
let patch,
  grammar,
  models = [],
  stage = 0,
  worker,
  busy = false,
  initialized = false,
  running = false,
  currentAtoms = [],
  lastReceipt = null,
  galleryViews = [],
  trainingWeights = [],
  trainingCurve = [],
  galleryPage = 0;
const renderer = new THREE.WebGLRenderer({
  canvas: $("scene"),
  antialias: true,
  alpha: true,
});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
const scene = new THREE.Scene(),
  camera = new THREE.PerspectiveCamera(38, 1, 0.01, 100000),
  controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.55;
scene.add(new THREE.HemisphereLight(0xe5f4ff, 0x314c4b, 2.5));
const light = new THREE.DirectionalLight(0xffffff, 2.5);
light.position.set(12, 18, 15);
scene.add(light);
let atomGroup = new THREE.Group(),
  overlay = new THREE.Group();
scene.add(atomGroup, overlay);
const sphere = new THREE.SphereGeometry(1, 16, 12),
  dummy = new THREE.Object3D();
const galleryRenderer = new THREE.WebGLRenderer({
  antialias: true,
  alpha: true,
  preserveDrawingBuffer: true,
});
galleryRenderer.setSize(260, 160);
function clear(group) {
  group.traverse((o) => {
    if (o.geometry && o.geometry !== sphere) o.geometry.dispose();
    if (o.material) o.material.dispose();
  });
  group.clear();
}
function buildAtoms(group, atoms, radius = 0.38, seedCount = Infinity) {
  const groups = new Map();
  atoms.forEach((s, i) => {
    const key = s.species + (i >= seedCount ? ":new" : ":seed");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(s);
  });
  for (const [key, rows] of groups) {
    const material = new THREE.MeshStandardMaterial({
      color: color(rows[0].species),
      emissive: key.endsWith(":new") ? color(rows[0].species) : "#000000",
      emissiveIntensity: 0.2,
      roughness: 0.4,
      metalness: 0.16,
    });
    const mesh = new THREE.InstancedMesh(sphere, material, rows.length);
    rows.forEach((a, i) => {
      dummy.position.set(...a.position);
      dummy.scale.setScalar(
        radius * (a.species === "H" || a.species === "D" ? 0.8 : 1),
      );
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    });
    group.add(mesh);
  }
}
function fitView(atoms) {
  const box = new THREE.Box3();
  atoms.forEach((a) => box.expandByPoint(new THREE.Vector3(...a.position)));
  const center = box.getCenter(new THREE.Vector3()),
    size = Math.max(2, box.getSize(new THREE.Vector3()).length());
  controls.target.copy(center);
  camera.position
    .copy(center)
    .add(
      new THREE.Vector3(0.68, 0.48, 1).normalize().multiplyScalar(size * 1.4),
    );
  camera.far = Math.max(1000, size * 10);
  camera.updateProjectionMatrix();
  controls.update();
}
function showAtoms(atoms, fit = false) {
  currentAtoms = atoms;
  clear(atomGroup);
  buildAtoms(
    atomGroup,
    atoms,
    (grammar?.minimum || 2.2) * 0.17,
    stage === 3 ? patch.atoms.length : Infinity,
  );
  if (fit) fitView(atoms);
  $("atomCount").textContent = atoms.length.toLocaleString();
  const counts = new Map();
  for (const atom of atoms)
    counts.set(atom.species, (counts.get(atom.species) || 0) + 1);
  $("visibleComposition").textContent = [...counts]
    .map(([species, count]) => `${species}: ${count.toLocaleString()}`)
    .join(" · ");
}
function edges(pairs) {
  clear(overlay);
  const points = [];
  for (const [a, b] of pairs || [])
    if (patch.atoms[a] && patch.atoms[b])
      points.push(...patch.atoms[a].position, ...patch.atoms[b].position);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
  overlay.add(
    new THREE.LineSegments(
      geo,
      new THREE.LineBasicMaterial({
        color: 0x91e4ca,
        transparent: true,
        opacity: 0.7,
      }),
    ),
  );
}
function settledEdges() {
  if (!grammar) return [];
  const result = new Map();
  for (const type of grammar.types)
    for (const o of type.occurrences)
      for (const i of o.ids) {
        const others = o.ids
          .filter((j) => j !== i)
          .sort(
            (a, b) =>
              distance(patch.atoms[i].position, patch.atoms[a].position) -
              distance(patch.atoms[i].position, patch.atoms[b].position),
          );
        if (others.length) {
          const j = others[0],
            pair = [i, j].sort((a, b) => a - b);
          result.set(pair.join(","), pair);
        }
      }
  return [...result.values()];
}
function hull(group, sites) {
  // Supporting planes; each coplanar face is triangulated only once.
  const faces = new Map(),
    p = sites.map((s) => s.position);
  for (let a = 0; a < p.length; a++)
    for (let b = a + 1; b < p.length; b++)
      for (let c = b + 1; c < p.length; c++) {
        let n = cross(sub(p[b], p[a]), sub(p[c], p[a]));
        if (norm(n) < 1e-6) continue;
        n = n.map((v) => v / norm(n));
        const ds = p.map((q) => dot(n, sub(q, p[a])));
        if (ds.some((d) => d > 1e-5) && ds.some((d) => d < -1e-5)) continue;
        const indices = ds
          .map((d, i) => (Math.abs(d) < 1e-5 ? i : -1))
          .filter((i) => i >= 0);
        faces.set(indices.join(","), { indices, n });
      }
  const vertices = [];
  for (const { indices, n } of faces.values()) {
    const center = [0, 1, 2].map(
      (k) => indices.reduce((s, i) => s + p[i][k], 0) / indices.length,
    );
    const u = sub(p[indices[0]], center),
      v = cross(n, u);
    indices.sort(
      (a, b) =>
        Math.atan2(dot(sub(p[a], center), v), dot(sub(p[a], center), u)) -
        Math.atan2(dot(sub(p[b], center), v), dot(sub(p[b], center), u)),
    );
    for (let i = 1; i < indices.length - 1; i++)
      vertices.push(...p[indices[0]], ...p[indices[i]], ...p[indices[i + 1]]);
  }
  if (vertices.length) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
    geo.computeVertexNormals();
    group.add(
      new THREE.Mesh(
        geo,
        new THREE.MeshStandardMaterial({
          color: 0x80c9bd,
          transparent: true,
          opacity: 0.16,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      ),
    );
    group.add(
      new THREE.LineSegments(
        new THREE.EdgesGeometry(geo),
        new THREE.LineBasicMaterial({
          color: 0x8bc1b9,
          transparent: true,
          opacity: 0.5,
        }),
      ),
    );
  }
}
function formula(sites) {
  const c = {};
  sites.forEach((s) => (c[s.species] = (c[s.species] || 0) + 1));
  return Object.entries(c)
    .map(([s, n]) => s + (n > 1 ? n : ""))
    .join(" · ");
}
function buildGallery() {
  galleryViews.forEach((v) => {
    clear(v.group);
    clear(v.halo);
  });
  galleryViews = [];
  $("gallery").replaceChildren();
  if (!grammar) return;
  const start = galleryPage * 12;
  [...grammar.types]
    .sort(
      (a, b) =>
        Number(b.kind === "connected component") -
          Number(a.kind === "connected component") ||
        b.symmetries.length - a.symmetries.length ||
        b.occurrences.length - a.occurrences.length,
    )
    .slice(start, start + 12)
    .forEach((type) => {
      const card = document.createElement("article");
      card.className = "cluster-card";
      const canvas = document.createElement("canvas");
      canvas.width = 260;
      canvas.height = 160;
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = type.level ? "level 2" : "level 1";
      const h = document.createElement("h3");
      h.textContent = "C" + (type.id + 1) + " · " + formula(type.sites);
      const p = document.createElement("p");
      p.textContent =
        type.occurrences.length +
        " observations · " +
        type.observedOrientationClasses +
        " orientation classes · " +
        type.symmetries.length +
        " symmetries";
      card.append(canvas, tag, h, p);
      $("gallery").append(card);
      const sc = new THREE.Scene();
      sc.add(new THREE.HemisphereLight(0xffffff, 0x385b64, 3));
      const group = new THREE.Group(),
        halo = new THREE.Group();
      sc.add(group, halo);
      const radius = Math.max(...type.sites.map((s) => norm(s.position)), 1);
      buildAtoms(group, type.sites, grammar.minimum * 0.15);
      hull(group, type.sites);
      const cam = new THREE.PerspectiveCamera(40, 260 / 160, 0.01, 10000);
      cam.position.set(radius * 0.3, radius * 0.4, radius * 3.9);
      cam.lookAt(0, 0, 0);
      galleryViews.push({ card, canvas, sc, group, halo, cam, type, radius });
    });
  if (grammar.types.length > 12) {
    const nav = document.createElement("div");
    nav.className = "gallery-pagination";
    const prev = document.createElement("button"),
      next = document.createElement("button");
    prev.textContent = "← Previous clusters";
    next.textContent = "Next clusters →";
    prev.disabled = !galleryPage;
    next.disabled = start + 12 >= grammar.types.length;
    prev.onclick = () => {
      galleryPage--;
      buildGallery();
    };
    next.onclick = () => {
      galleryPage++;
      buildGallery();
    };
    nav.append(prev, next);
    $("gallery").append(nav);
  }
  updateHalos();
}
function updateHalos() {
  for (const v of galleryViews) {
    clear(v.halo);
    const positions = [];
    for (const port of grammar.ports
      .filter((p) => p.parent === v.type.id)
      .slice(0, 48)) {
      const d = port.pose.t,
        mag = norm(d);
      if (mag < 1e-5) continue;
      const score = trainingWeights.length
        ? trainingWeights.reduce(
            (s, w, i) =>
              s +
              w *
                Math.cos(
                  ((i + 1) * mag) / (grammar.scale * Number($("reach").value)),
                ),
            0,
          )
        : Math.sin(port.id * 2.1) * 0.4;
      const endpoint = d.map(
        (x) => (x / mag) * v.radius * (1.25 + 0.22 * Math.tanh(score)),
      );
      positions.push(0, 0, 0, ...endpoint);
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(v.radius * 0.1, v.radius * 0.009, 5, 18),
        new THREE.MeshBasicMaterial({
          color: score > 0 ? 0x91e4ca : 0xd5a3ed,
          transparent: true,
          opacity: 0.7,
        }),
      );
      ring.position.set(...endpoint);
      ring.quaternion.setFromUnitVectors(
        new THREE.Vector3(0, 0, 1),
        new THREE.Vector3(...d).normalize(),
      );
      v.halo.add(ring);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    v.halo.add(
      new THREE.LineSegments(
        geo,
        new THREE.LineBasicMaterial({
          color: 0xa3cfca,
          transparent: true,
          opacity: 0.18,
        }),
      ),
    );
  }
}
function status(text) {
  $("status").textContent = text;
}
function event(text, kind = "") {
  const li = document.createElement("li");
  li.textContent = text;
  li.className = kind;
  $("events").prepend(li);
  while ($("events").children.length > 30) $("events").lastChild.remove();
}
function setStage(value) {
  stage = value;
  document.querySelectorAll("[data-stage]").forEach((b) => {
    if (Number(b.dataset.stage) === stage)
      b.setAttribute("aria-current", "step");
    else b.removeAttribute("aria-current");
  });
  document
    .querySelectorAll("[data-panel]")
    .forEach((p) => (p.hidden = Number(p.dataset.panel) !== stage));
  $("gallery").hidden = stage !== 2;
  $("scene").style.visibility = stage === 2 ? "hidden" : "visible";
  $("viewTitle").textContent = [
    "The observation",
    "Finding recurring supports",
    "One scene for each cluster",
    "The current search branch",
  ][stage];
  $("viewKicker").textContent = [
    "KNOWN ATOMIC POSITIONS",
    "PROPOSAL → ISOMETRY → COMPLETE COVER",
    "LOCAL CONNECTION MARKINGS",
    "CONTINUOUS POSES · REVERSIBLE DECISIONS",
  ][stage];
  if (stage !== 3 && running) pause();
  if (stage !== 1) clear(overlay);
  if (stage < 2) showAtoms(patch.atoms);
  if (stage === 1 && grammar) edges(settledEdges());
  if (stage === 2) buildGallery();
  if (stage === 3 && grammar) {
    if (!initialized) initialize();
    else worker.postMessage({ type: "view" });
  }
}
function setBusy(value) {
  busy = value;
  for (const id of [
    "sample",
    "identify",
    "support",
    "tolerance",
    "hierarchy",
    "file",
    "database",
    "channels",
    "reach",
  ])
    $(id).disabled = value;
  $("train").disabled = value || !grammar;
  $("run").disabled = value || !grammar;
  $("step").disabled = value || !grammar;
}
function workerSetup() {
  worker?.terminate();
  worker = new Worker(new URL("./continuous-worker.mjs", import.meta.url), {
    type: "module",
  });
  worker.onerror = (e) => {
    setBusy(false);
    status("Worker error: " + e.message);
  };
  worker.onmessage = ({ data: d }) => {
    if (d.type === "error") {
      setBusy(false);
      running = false;
      status(d.message);
      event(d.message, "backtrack");
      $("pause").disabled = true;
      return;
    }
    if (d.type === "discovery") {
      status(d.message + " · " + d.done + " / " + d.total);
      $("progressBar").style.width = (100 * d.done) / d.total + "%";
      if (stage === 1) edges(d.edges);
    }
    if (d.type === "identified") {
      grammar = d.grammar;
      setBusy(false);
      initialized = false;
      galleryPage = 0;
      clear(overlay);
      $("typeCount").textContent = grammar.types.length;
      $("portCount").textContent = grammar.ports.length.toLocaleString();
      $("coverStats").textContent =
        grammar.audit.coveredAtoms +
        " / " +
        patch.atoms.length +
        " atoms in recurring supports · " +
        grammar.residuals.length +
        " residual atoms · " +
        grammar.audit.hierarchyLevels +
        " fitted levels.";
      if (grammar.audit.molecularSupportClosure)
        $("coverStats").textContent +=
          " Molecular closure: " +
          grammar.audit.recurringMolecules +
          " complete observed molecules; crop fragments are not propagated.";
      $("toLearning").disabled = false;
      $("toSearch").disabled = false;
      $("restart").disabled = false;
      $("progressBar").style.width = "100%";
      status(
        "Complete atomic cover recorded. Inspect each cluster and its connection evidence.",
      );
      event(
        grammar.types.length +
          " cluster types and " +
          grammar.ports.length +
          " finite overlap ports fitted.",
      );
    }
    if (d.type === "identified" && stage === 1) edges(settledEdges());
    if (d.type === "training") {
      trainingWeights = d.weights;
      trainingCurve.push(d.loss);
      plotCurve(trainingCurve);
      $("trainingState").textContent =
        d.epoch +
        " epochs · " +
        d.samples +
        " observed connections · loss " +
        d.loss.toFixed(4);
      updateHalos();
    }
    if (d.type === "trained") {
      models.push(d.model);
      trainingWeights = d.model.weights;
      plotCurve(d.model.curve);
      $("trainingState").textContent =
        d.model.samples +
        " connection observations · final loss " +
        d.model.curve.at(-1).toFixed(4) +
        " · training-only";
      $("library").replaceChildren(
        ...models.map(
          (m, i) =>
            new Option(
              "Marking " +
                (i + 1) +
                " · " +
                m.channels +
                " channels · " +
                m.reach +
                "× reach",
              m.id,
            ),
        ),
      );
      $("library").value = d.model.id;
      $("policy").value = "marking";
      initialized = false;
      setBusy(false);
      status(
        "Marking saved in this experiment. Train another or compare policies in tree search.",
      );
      updateHalos();
    }
    if (d.type === "search" || d.type === "best") {
      lastReceipt = d.receipt;
      if (stage === 3) showAtoms(d.atoms);
      $("backtrackCount").textContent =
        d.receipt.stats.backtracks.toLocaleString();
      $("searchState").textContent =
        d.receipt.status +
        " · depth " +
        d.receipt.stats.depth +
        " · " +
        d.receipt.stats.checks.toLocaleString() +
        " checks · best " +
        d.receipt.bestAtoms.toLocaleString() +
        " atoms";
      $("download").disabled = false;
      $("best").disabled = false;
      for (const e of d.events || [])
        if (e.type === "accept")
          event(
            "Attach " +
              e.novel +
              " atoms · depth " +
              e.depth +
              (e.forced ? " · single legal choice" : ""),
            "accept",
          );
        else if (e.type === "backtrack")
          event("Undo branch → depth " + e.depth, "backtrack");
      if (d.type === "best") {
        fitView(d.atoms);
        status(
          "Best encountered structure · " +
            d.atoms.length +
            " explicit atoms. The retained search branch is unchanged.",
        );
      } else if (
        d.receipt.status.endsWith("limit") ||
        d.receipt.status === "exhausted"
      ) {
        status(d.receipt.status + " · inspect or download the best structure.");
      }
    }
    if (d.type === "paused") {
      running = false;
      $("pause").disabled = true;
      $("run").textContent = "Resume";
      $("step").disabled = !grammar;
      if (lastReceipt?.status === "searching")
        $("searchState").textContent =
          "Paused · depth " +
          lastReceipt.stats.depth +
          " · " +
          lastReceipt.stats.checks.toLocaleString() +
          " checks · best " +
          lastReceipt.bestAtoms +
          " atoms";
    }
  };
}
function load(value) {
  const atoms = validateAtoms(value.atoms);
  if (atoms.length > 1600)
    throw Error("Choose a patch with at most 1,600 atoms.");
  patch = { ...value, atoms };
  grammar = null;
  models = [];
  initialized = false;
  running = false;
  lastReceipt = null;
  workerSetup();
  setBusy(false);
  $("toLearning").disabled = true;
  $("toSearch").disabled = true;
  $("restart").disabled = true;
  $("best").disabled = true;
  $("download").disabled = true;
  $("pause").disabled = true;
  $("library").replaceChildren(new Option("No marking trained", ""));
  $("specimenName").textContent = patch.name;
  $("provenance").textContent = patch.source;
  $("composition").replaceChildren();
  const species = [...new Set(atoms.map((s) => s.species))];
  for (const s of species) {
    const chip = document.createElement("span");
    chip.className = "chip";
    const dot = document.createElement("i");
    dot.style.background = color(s);
    chip.append(
      dot,
      document.createTextNode(
        s + " · " + atoms.filter((a) => a.species === s).length,
      ),
    );
    $("composition").append(chip);
  }
  $("typeCount").textContent = "—";
  $("portCount").textContent = "—";
  $("backtrackCount").textContent = "—";
  $("progressBar").style.width = "0%";
  showAtoms(atoms, true);
  setStage(0);
  status(
    "Observed patch ready. No lattice or family label is passed to learning.",
  );
}
function initialize() {
  if (!grammar) return;
  const marking = models.find((m) => m.id === $("library").value) || null;
  if ($("policy").value === "marking" && !marking) {
    status("Train a marking first, or choose another policy.");
    return false;
  }
  worker.postMessage({
    type: "initialize",
    options: {
      policy: $("policy").value,
      marking,
      maximumAtoms: Number($("memory").value),
    },
  });
  initialized = true;
  return true;
}
function pause() {
  worker.postMessage({ type: "pause" });
  running = false;
  $("pause").disabled = true;
}
function plotCurve(values) {
  const max = Math.max(...values, 0.001),
    min = Math.min(...values, 0),
    points = values
      .map(
        (v, i) =>
          10 +
          (240 * i) / Math.max(1, values.length - 1) +
          "," +
          (80 - (65 * (v - min)) / (max - min)),
      )
      .join(" ");
  $("curve").innerHTML =
    '<path d="M10 10V80H250" fill="none" stroke="#3c5360"/><polyline points="' +
    points +
    '" fill="none" stroke="#91e4ca" stroke-width="2"/><text x="12" y="12" fill="#a0b2bc" font-size="9">observed-frequency loss</text>';
}
document
  .querySelectorAll("[data-stage]")
  .forEach((b) => (b.onclick = () => setStage(Number(b.dataset.stage))));
$("toClusters").onclick = () => setStage(1);
$("toLearning").onclick = () => setStage(2);
$("toSearch").onclick = () => setStage(3);
$("identify").onclick = () => {
  models = [];
  trainingWeights = [];
  setBusy(true);
  status("Discovering supports in the worker…");
  worker.postMessage({
    type: "identify",
    atoms: patch.atoms,
    options: {
      tolerance: Number($("tolerance").value),
      maximumSupport: Number($("support").value),
      hierarchy: $("hierarchy").checked,
    },
  });
};
$("train").onclick = () => {
  setBusy(true);
  trainingCurve = [];
  worker.postMessage({
    type: "train",
    options: {
      channels: Number($("channels").value),
      reach: Number($("reach").value),
    },
  });
};
$("sample").onchange = () => {
  try {
    load(samplePatch($("sample").value));
  } catch (e) {
    status(e.message);
  }
};
$("file").onchange = async () => {
  try {
    const f = $("file").files[0];
    if (!f) return;
    const result = parseStructureText(await f.text(), f.name);
    load({
      name: f.name,
      source: "Local observation · " + result.atoms.length + " atoms",
      atoms: result.atoms,
    });
  } catch (e) {
    status(e.message);
  }
};
for (const id of ["policy", "library"])
  $(id).onchange = () => {
    pause();
    initialized = false;
    status(
      "Policy changed. The next run starts a fresh tree from the same observed patch.",
    );
  };
$("memory").onchange = () => {
  pause();
  worker.postMessage({
    type: "budget",
    maximumAtoms: Number($("memory").value),
  });
  status("Memory budget updated. Resume retains the current search branch.");
};
$("run").onclick = () => {
  if (!initialized && !initialize()) return;
  running = true;
  $("pause").disabled = false;
  $("step").disabled = true;
  $("run").textContent = "Running…";
  worker.postMessage({
    type: "run",
    milliseconds: Number($("duration").value),
  });
};
$("pause").onclick = pause;
$("step").onclick = () => {
  if (!initialized && !initialize()) return;
  worker.postMessage({ type: "step" });
};
$("restart").onclick = () => {
  pause();
  initialize();
  status("New search initialized from the complete observation.");
};
$("best").onclick = () => {
  pause();
  worker.postMessage({ type: "best" });
};
$("download").onclick = () => {
  const blob = new Blob(
      [
        JSON.stringify(
          {
            specimen: patch.name,
            atoms: currentAtoms,
            exportedAtomCount: currentAtoms.length,
            exportedStructureMayBeBestSnapshot: true,
            receipt: lastReceipt,
            grammarAudit: grammar?.audit,
            markings: models,
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    ),
    url = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = url;
  a.download = "materials-gcts-experiment.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
$("auditButton").onclick = () => $("audit").showModal();
$("closeAudit").onclick = () => $("audit").close();
const elements = new Set(["Na", "Cl"]);
for (const el of PERIODIC_ELEMENTS) {
  const b = document.createElement("button");
  b.textContent = el.symbol;
  b.title = el.symbol + " · " + el.phase + " near room temperature";
  b.className = "element-" + el.phase;
  b.setAttribute("aria-pressed", elements.has(el.symbol));
  b.onclick = () => {
    if (elements.has(el.symbol)) elements.delete(el.symbol);
    else elements.add(el.symbol);
    b.setAttribute("aria-pressed", elements.has(el.symbol));
    $("elementToggle").textContent =
      "Choose elements · " + [...elements].join(" + ");
  };
  $("elementPicker").append(b);
}
PERIODIC_ELEMENTS.forEach((el, i) => {
  const b = $("elementPicker").children[i];
  b.style.gridColumn = el.column;
  b.style.gridRow = el.row;
});
$("elementToggle").onclick = () => {
  $("elementPicker").hidden = !$("elementPicker").hidden;
  $("elementToggle").setAttribute("aria-expanded", !$("elementPicker").hidden);
};
document.addEventListener("click", (e) => {
  if (
    !$("elementPicker").contains(e.target) &&
    e.target !== $("elementToggle")
  ) {
    $("elementPicker").hidden = true;
    $("elementToggle").setAttribute("aria-expanded", false);
  }
});
$("database").onclick = async () => {
  if (!elements.size) {
    $("databaseState").textContent = "Choose at least one element.";
    return;
  }
  setBusy(true);
  $("databaseState").textContent = "Querying public NOMAD archives…";
  try {
    const result = await randomNomadStructure([...elements]);
    load({
      name: [...elements].join("–") + " · NOMAD",
      source:
        "Public archive · " +
        (result.structure.name || "composition-matched periodic sample"),
      atoms: result.structure.atoms,
    });
    $("databaseState").textContent = "Loaded a matching observation.";
  } catch (e) {
    $("databaseState").textContent = e.message;
  } finally {
    setBusy(false);
  }
};
let lastGallery = 0;
function animate(time) {
  requestAnimationFrame(animate);
  const w = $("viewport").clientWidth,
    h = $("viewport").clientHeight;
  if (
    renderer.domElement.width !== Math.round(w * renderer.getPixelRatio()) ||
    renderer.domElement.height !== Math.round(h * renderer.getPixelRatio())
  ) {
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  controls.autoRotate =
    $("rotate").checked &&
    !matchMedia("(prefers-reduced-motion: reduce)").matches;
  controls.update();
  if (stage !== 2) renderer.render(scene, camera);
  else if (time - lastGallery > 100) {
    lastGallery = time;
    for (const v of galleryViews) {
      const rect = v.card.getBoundingClientRect(),
        parent = $("gallery").getBoundingClientRect();
      if (rect.bottom < parent.top || rect.top > parent.bottom) continue;
      if (controls.autoRotate) {
        v.group.rotation.y += 0.018;
        v.halo.rotation.copy(v.group.rotation);
      }
      galleryRenderer.render(v.sc, v.cam);
      v.canvas
        .getContext("2d")
        .drawImage(galleryRenderer.domElement, 0, 0, 260, 160);
    }
  }
}
load(samplePatch("nacl"));
requestAnimationFrame(animate);
