const byId = (id) => document.getElementById(id);

const atlas = byId("evidenceAtlas");
const atlasButton = byId("evidenceAtlasButton");
const ribbonButton = byId("evidenceRibbonButton");
const closeButton = byId("evidenceAtlasClose");
const methodLink = byId("atlasMethodLink");

const SYSTEMS = {
  nacl: {
    short: "NaCl", kind: "periodic crystal", name: "NaCl rocksalt",
    summary: "The positive control for true stationary recursion. Positions and species are sufficient to recover three translations, a radix-two cell rule, eight child offsets, and a frozen directed-port certificate.",
    values: [2, 16, 128, 1024, 8192, 65536, 524288, 4194304], verifiedThrough: 7,
    metrics: [["learned scale", "2.000×"], ["child cells", "8"], ["strong witnesses", "1,478 / 750 / 86"], ["symbolic actions", "7 → 4.19m"]],
    verdict: ["proved", "Stationary colored production · exact scale and population substitution"],
    evidence: [
      ["Discovery", "3 recurrent generators", "No cell, axes, or space group supplied."],
      ["Frozen replay", "216 → 1,728 → 13,824", "Separate colored configurations replay exactly."],
      ["Port certificate", "8 children · 24 directed ports", "Two atom-disjoint macro occurrences; MDL saving 30."],
    ],
  },
  iqc: {
    short: "Ideal IQC", kind: "icosahedral quasicrystal", name: "Ideal icosahedral QC",
    summary: "The generic port/cover graph performs exact self-fed continuation and promotes larger recurrent supports. What it has not found is one exact chemistry–chirality–port production that repeats across three consecutive scales.",
    values: [507, 4923, 13847, 31521, 66935], verifiedThrough: 4,
    metrics: [["exact actions", "3+"], ["largest audited cloud", "66,935"], ["train hierarchy", "73→17→6→3→2→1"], ["stationary witnesses", "0"]],
    verdict: ["open", "Finite exact growth passes · generic stationary/exponential rule remains open"],
    evidence: [
      ["Generic VM", "31,521 exact sites", "One relational evaluator; no material-family dispatch."],
      ["Continuous section", "4 / 4 + 4 / 4 fresh", "Continuous port-state invariants rank both self-fed colored actions first."],
      ["Parallel section preflight", "57 / 216 · 48 / 216 pure bands", "No whole-action threshold reaches 95% group-heldout precision; the fresh antichain target stays sealed."],
      ["Carried obligations", "1 + 1 pure actions retained", "Future port-consensus features reach perfect precision only at one action per stage; the 18-action coverage gate stays red."],
      ["Explicit incidences", "8 / 9 connected paths · 0 / 16 exact", "Role vocabulary transfers at 97.4% mass, but connection closure alone selects structurally legal false branches."],
      ["Candidate section", "25 / 26 exact · 4 / 9 nuclei", "Adding the colored nearest-neighbor metric graph raises precision-qualified throughput, but four boundary families remain uncovered."],
      ["Individual port paths", "9 / 9 exact paths exist · 5 / 9 selected", "Removing a double-counted child score exposes real joint-marking value, but four boundary environments remain unresolved."],
      ["Third-frontier value", "4 / 9 selected", "A 512-path target-free lookahead is worse than the corrected two-step mark; frontier supply is not the missing value."],
      ["Clusters²", "6 positive quotient levels", "History-free re-clustering improves proof depth."],
      ["Frontier states", "336 / 368 sites", "Four heterogeneous multi-child rules are real, but no closed state matrix repeats across transitions."],
      ["Strict audit", "0 common three-level keys", "Topology, chemistry, chirality, ports, pose, and populations stay exact."],
    ],
  },
  cdyb: {
    short: "Cd–Yb", kind: "published real-material model", name: "Cd₅.₇Yb icosahedral QC",
    summary: "A published cut-and-project model supplies positions and species only; its hidden higher-dimensional coordinates never enter the learner. Local connection marking gives exact finite growth, while promoted vocabularies still fail to seed a stationary exterior rule on a disjoint nucleus.",
    values: [59, 237], verifiedThrough: 1,
    metrics: [["causal nuclei", "2 disjoint"], ["local growth", "295 / 295 exact"], ["train hierarchy", "9 positive levels"], ["stationary witnesses", "0"]],
    verdict: ["progress", "Real-material finite continuation passes · hierarchical transfer and stationarity remain open"],
    evidence: [
      ["Causal section", "178 / 178 + 117 / 117", "Bounded connection witnesses beat 31 ownership shuffles."],
      ["Deep hierarchy", "80→36→22→15→8→6→4→2→1", "Every later retained type is witnessed in at least two raw windows."],
      ["Sealed nucleus", "82 partial candidates · 6 exact", "One-child completion exposes policy headroom without target leakage."],
    ],
  },
  glass: {
    short: "Glass", kind: "amorphous negative control", name: "Cu–Zr metallic glass",
    summary: "A complete finite cover is always possible, but a deterministic stationary production should not be hallucinated. The amorphous control is therefore successful when compression and recursive transfer are rejected.",
    values: [216], verifiedThrough: 0,
    metrics: [["complete representation", "yes + residuals"], ["stationary macros", "0"], ["deterministic continuation", "rejected"], ["correct target", "ensemble statistics"]],
    verdict: ["control", "Negative control passes by refusing a false exponential grammar"],
    evidence: [
      ["Local structure", "motifs are allowed", "Short-range order is not confused with global determinism."],
      ["Recursion", "stationarity rejected", "No copied patch is promoted forever from one observation."],
      ["Evaluation", "RDF + S(q) + motif statistics", "A glass target is an ensemble, not one privileged continuation."],
    ],
  },
};

const MATRIX = [
  ["NaCl crystal", ["pass", "100% colored cover"], ["pass", "2 exact unseen levels"], ["pass", "8-child cell macro"], ["pass", "4.19m / 7 actions"]],
  ["Ideal IQC", ["pass", "2,064 / 2,064"], ["pass", "31,521 exact sites"], ["progress", "6 train levels"], ["open", "no 3-scale key"]],
  ["Cd₅.₇Yb IQC", ["pass", "2,385 / 2,385"], ["pass", "295 / 295 local"], ["progress", "9 train · 4 replay"], ["open", "no stationary key"]],
  ["Cu–Zr glass", ["control", "cover + residuals"], ["control", "not uniquely defined"], ["control", "recursion rejected"], ["control", "negative passes"]],
];

const MATRIX_DETAILS = {
  "NaCl crystal": "The learner receives neither the unit cell nor Fm-3m. A positions-only discovery proposes the radix and offsets; the independently learned proper-port graph must witness the same eight-child production at three scales before the stationary gate turns green.",
  "Ideal IQC": "Exact continuation is real and self-fed, but different promoted productions appear at successive levels. Deep compression is not renamed exponential growth: the strict stationary audit requires the same exact semantic production and learned scale twice in succession.",
  "Cd₅.₇Yb IQC": "The real-material model is the hardest transfer case. Bounded local marking succeeds for finite primitive growth, but exact promoted clusters are sparse and nucleus-dependent. Dormant types remain frozen rather than being refit on held-out atoms.",
  "Cu–Zr glass": "The negative control protects the benchmark from a trivial answer. Residual clusters guarantee representation, but no stable macro production, unique exterior continuation, or million-site symbolic claim is admitted.",
};

const ANATOMY = {
  cover: ["Complete, irregular cluster cover", "Frequent colored point-set isometries are found without requiring an atom at the centre or a fixed-radius sphere. A deterministic cover records overlaps, while every uncovered connected component becomes an explicit residual cluster. Coverage is therefore exact and compression remains falsifiable.", ["species + xyz only", "proper rotations", "gaps stay explicit"]],
  ports: ["Finite connection vocabulary", "Each witnessed neighboring or overlapping placement is expressed in the parent cluster frame and quotiented by the proper symmetry groups of both clusters. Reflections, unlike-species coincidences, and sub-minimum-distance collisions are rejected.", ["SE(3), never O(3)", "overlap chemistry", "boundary slots"]],
  mark: ["A local section over connections", "The marking is not an energy surface. It is a bounded function of already present incident ports and local compatibility evidence. It ranks the same frozen exact actions seen by every baseline and shuffled control.", ["incoming order ≤ 2", "no target atoms", "identical candidates"]],
  search: ["Tree search with parallel visible moves", "Under the hood, every placement is a branch decision with rejection and rollback accounting. On screen, candidates that commute—different frontier sides with no conflicts—are committed as one antichain, so update order does not create a fake physical sequence.", ["whole clusters", "pairwise compatibility", "proposal work counted"]],
  promote: ["Clusters become atoms of the next grammar", "Accepted or re-clustered unions are canonicalized as new proper-SE(3) prototypes. Their internal ports become edges and exposed ports become the next frontier. Stationarity is claimed only if one exact production recurs across three levels with equal learned scales and population substitutions.", ["history-free option", "positive MDL", "strict recurrence gate"]],
};

const TIMELINE = [
  ["01", "Complete covers", "Atom-centred shells were replaced by irregular repeated supports, exact overlap covers, and explicit residual gap clusters.", "proved"],
  ["02", "Oriented ports", "Connection identity became a finite double orbit of proper cluster symmetries with colored overlap witnesses.", "proved"],
  ["03", "Causal frontier", "Held-out atoms were removed from branch choice; targets are opened only after frozen candidate traces exist.", "proved"],
  ["04", "Parallel growth", "Compatible whole-cluster moves became antichains over an underlying tree search, preserving order independence.", "proved"],
  ["05", "Clusters of clusters", "Sparse port graphs and exact MDL mining promoted recurring connected unions into higher-level prototypes.", "proved"],
  ["06", "Crystal stationarity", "NaCl produced an independently witnessed eight-child rule at three scales and crossed the symbolic million-site gate.", "proved"],
  ["07", "Quasicrystal continuation", "Ideal IQC and published Cd–Yb systems achieved exact, self-fed finite growth with causal local markings.", "progress"],
  ["08", "History-free hierarchy", "Re-clustering generated deeper IQC and nine-level Cd–Yb compression without encoding action order as geometry.", "progress"],
  ["09", "Site-resolved completion", "Partial macro sites now remain explicit obligations; no child or parent exists until its full colored support and ports verify.", "proved"],
  ["10", "Vector frontier substitutions", "Global one-owner matching learns and executes A→AB, B→A with spectral growth φ; the real IQC still has no closed recurrent matrix.", "progress"],
  ["11", "Continuous port-state section", "Adding invariant parent/source connection statistics makes both fresh self-fed actions rank first: 4 / 4 plus 4 / 4 exact colored sites.", "proved"],
  ["12", "Whole-action calibration", "Absolute pure thresholds select 50 and 24 training sites but transfer no actions; a 15-feature band section also fails the 95% group-heldout precision preflight.", "open"],
  ["13", "Carried obligations", "One-step successor-port summaries isolate one pure seed and one pure self-fed action, but fail the predeclared two-actions-per-nucleus aggregate coverage gate.", "progress"],
  ["14", "Explicit port incidence", "Bounded backtracking finds two-action connected paths on 8 / 9 held-out nuclei, but all 16 selected actions are false; role closure is necessary, not sufficient.", "progress"],
  ["15", "Candidate-level section", "Adding the colored nearest-neighbor metric graph to individual pose–port descriptors yields 25 / 26 exact compatible placements across four of nine nuclei.", "progress"],
  ["16", "Individual port paths", "Every nucleus contains exact two-step root→child paths in a fixed target-free supply. Correcting score composition raises heldout selection from 0 / 9 to 5 / 9.", "progress"],
  ["17", "Third-frontier control", "A fixed 512-path shortlist contains exact alternatives in every nucleus, but outgoing-frontier valuation falls to 4 / 9 and is rejected.", "progress"],
  ["18", "Open frontier", "Learn a transferable connection section that selects the existing exact paths, then promote the resulting antichain into a recurring oriented production.", "open"],
];

const CLAIMS = [
  ["proved", "Complete representation", "Every observed atom belongs to a repeated support or an explicit residual cluster; gaps are never silently dropped."],
  ["proved", "Proper rigid-motion invariance", "Permutation and arbitrary proper-SE(3) transforms preserve the scientific grammar; mirror images remain distinct when chiral."],
  ["proved", "Crystal exponential representation", "The learned NaCl recurrence represents 4,194,304 colored sites after seven symbolic actions."],
  ["proved", "Multi-state exponential control", "A positions-only grammar learns A→AB and B→A, predicts a sealed 48-site fourth wave exactly, and represents 1,178,508 sites at vector action 24."],
  ["proved", "Causal GCTS advantage", "On sealed IQC frontiers, learned connection sections beat matched baselines and 31 shuffled controls with identical candidate sets."],
  ["proved", "Exact finite QC continuation", "Multiple ideal and published quasicrystal nuclei grow self-fed with exact colored-site certificates."],
  ["proved", "Negative amorphous control", "The generic hierarchy rejects stationary recursion rather than memorizing and repeating a glass crop."],
  ["progress", "Deep QC compression", "Ideal IQC reaches six positive quotient levels; Cd–Yb reaches nine on five disjoint training windows."],
  ["progress", "Frozen hierarchy transfer", "IQC primitive cover transfers completely and Cd–Yb promoted vocabularies re-encode four held-out levels, with dormant symbols explicit."],
  ["progress", "Site-resolved marking", "A 1,245-site train corpus gives site AUC 0.8864 and action AUC 1.0, both significant against 31 shuffles."],
  ["proved", "Continuous IQC section", "A 50,065-example post-commit port-state section transfers for two fresh self-fed waves, emitting 8 / 8 exact colored sites."],
  ["open", "Parallel IQC action marking", "Whole-action band labels are 57 / 216 and 48 / 216 positive, but no group-heldout threshold reaches 95% precision; local scores alone cannot yet admit an exact antichain."],
  ["progress", "Port-obligation lookahead", "One-step future-frontier features find one zero-error action per stage, but retain 1 / 18 required actions; explicit incidence-level search is still needed."],
  ["progress", "Explicit incidence search", "A 504-action, target-free two-level graph carries semantic port roles and backtracks stranded branches. It finds 8 / 9 connected paths, but all 16 selected actions are false; 97.4% role transfer shows the missing signal is joint local section geometry, not vocabulary coverage."],
  ["progress", "Candidate pose–port section", "Across 44,602 collision-free candidates, the colored metric-graph section admits 25 / 26 exact placements. They cover only four of nine nuclei, so the reserved target stays sealed."],
  ["progress", "Exact two-step path supply", "One hundred twenty-eight target-free descriptor classes per nucleus contain exact root→child connections in all nine nuclei. Correct score composition selects 5 / 9; four failures now isolate the missing path-value section."],
  ["progress", "Third-frontier negative control", "Executing 512 target-free paths per nucleus and marking their outgoing port sections selects only 4 / 9. A larger immediate frontier is again rejected as the search value."],
  ["progress", "Frontier-state grammar", "Five recurring types cover 336 / 368 IQC sites; four rules are heterogeneous, but no closed state matrix recurs across transitions."],
  ["open", "Nested calibration", "The strongest Cd–Yb site threshold is 97.73% precise when fixed, but fully nested selection is 94.48%; a fresh target stays sealed."],
  ["open", "Generic QC stationarity", "No exact chemistry–chirality–directed-port production recurs across three consecutive QC levels."],
  ["progress", "IQC option-preserving beam", "A width-four target-free beam keeps the branch with the largest compatible next frontier. Frozen before wave 20, it adds 120/120 exact held-forward sites; all 24 waves are 572/572 exact. Spatial confirmation and stationarity remain open."],
  ["open", "Generic million-site QC growth", "Specialized/address ceilings cross one million; the family-blind cluster-of-clusters executor does not yet."],
  ["open", "Pure-port crystal closure", "NaCl's port graph certifies the learned cell rule, but the radix/offset proposal still comes from a positions-only grid learner."],
  ["open", "Explicit output cost", "Symbolic derivations compress actions; emitting every atom remains linear and is not claimed to replace molecular dynamics time integration."],
];

function statusLabel(status) {
  return status === "pass" || status === "proved" ? "proved" : status === "progress" ? "measured" : status === "control" ? "control" : "open";
}

function openAtlas() {
  atlas.hidden = false;
  document.body.classList.add("atlas-open");
  atlasButton.setAttribute("aria-expanded", "true");
  closeButton.focus();
}

function closeAtlas() {
  atlas.hidden = true;
  document.body.classList.remove("atlas-open");
  atlasButton.setAttribute("aria-expanded", "false");
  atlasButton.focus();
}

function renderMatrix() {
  MATRIX.forEach(([name, ...cells]) => {
    const row = document.createElement("div");
    row.className = "matrix-row";
    row.setAttribute("role", "row");
    row.innerHTML = `<strong>${name}</strong>`;
    cells.forEach(([status, label]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `matrix-cell ${status}`;
      button.innerHTML = `<i></i><span>${label}</span><small>${statusLabel(status)}</small>`;
      button.addEventListener("click", () => {
        document.querySelectorAll(".matrix-row.selected").forEach((item) => item.classList.remove("selected"));
        row.classList.add("selected");
        byId("matrixDetail").innerHTML = `<span>${name}</span><p>${MATRIX_DETAILS[name]}</p>`;
      });
      row.appendChild(button);
    });
    byId("benchmarkMatrix").appendChild(row);
  });
  byId("benchmarkMatrix").querySelector(".matrix-cell").click();
}

function drawGrowthChart(system) {
  const svg = byId("atlasGrowthChart");
  const width = 720, height = 300, left = 62, right = 28, top = 28, bottom = 54;
  const values = system.values;
  const maximum = Math.max(...values, 10);
  const maxLog = Math.ceil(Math.log10(maximum));
  const x = (index) => left + (width - left - right) * (values.length === 1 ? .5 : index / (values.length - 1));
  const y = (value) => top + (height - top - bottom) * (1 - Math.log10(Math.max(1, value)) / maxLog);
  const grid = Array.from({length: maxLog + 1}, (_, power) => {
    const value = 10 ** power;
    return `<g><line x1="${left}" y1="${y(value)}" x2="${width - right}" y2="${y(value)}"/><text x="${left - 10}" y="${y(value) + 3}" text-anchor="end">10${power === 0 ? "⁰" : `<tspan baseline-shift="super">${power}</tspan>`}</text></g>`;
  }).join("");
  const points = values.map((value, index) => `${x(index)},${y(value)}`).join(" ");
  const area = `${left},${height - bottom} ${points} ${x(values.length - 1)},${height - bottom}`;
  const dots = values.map((value, index) => `<g class="${index <= system.verifiedThrough ? "verified" : "projected"}"><circle cx="${x(index)}" cy="${y(value)}" r="5"/><text x="${x(index)}" y="${Math.max(14, y(value) - 12)}" text-anchor="middle">${value.toLocaleString()}</text></g>`).join("");
  svg.innerHTML = `<g class="chart-grid">${grid}</g><polygon class="growth-area" points="${area}"/><polyline class="growth-line" points="${points}"/>${dots}<g class="x-labels">${values.map((_value, index) => `<text x="${x(index)}" y="${height - 24}" text-anchor="middle">a${index}</text>`).join("")}</g>`;
}

function renderSystem(key) {
  const system = SYSTEMS[key];
  document.querySelectorAll("[data-system]").forEach((button) => button.classList.toggle("active", button.dataset.system === key));
  byId("atlasSystemKind").textContent = system.kind;
  byId("atlasSystemName").textContent = system.name;
  byId("atlasSystemSummary").textContent = system.summary;
  byId("atlasSystemMetrics").innerHTML = system.metrics.map(([term, value]) => `<div><dt>${term}</dt><dd>${value}</dd></div>`).join("");
  byId("atlasSystemVerdict").className = `system-verdict ${system.verdict[0]}`;
  byId("atlasSystemVerdict").innerHTML = `<span>${statusLabel(system.verdict[0])}</span><strong>${system.verdict[1]}</strong>`;
  byId("atlasCurveTitle").textContent = `${system.short} · growth by learned action`;
  byId("systemEvidenceCards").innerHTML = system.evidence.map(([label, value, note]) => `<article><small>${label}</small><strong>${value}</strong><p>${note}</p></article>`).join("");
  drawGrowthChart(system);
}

function renderSystems() {
  const tabs = byId("atlasSystemTabs");
  Object.entries(SYSTEMS).forEach(([key, system]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.system = key;
    button.innerHTML = `<span>${system.kind}</span><strong>${system.short}</strong>`;
    button.addEventListener("click", () => renderSystem(key));
    tabs.appendChild(button);
  });
  renderSystem("nacl");
}

function renderAnatomy(key) {
  const [title, copy, tags] = ANATOMY[key];
  document.querySelectorAll("[data-anatomy]").forEach((button) => button.classList.toggle("active", button.dataset.anatomy === key));
  byId("anatomyDetail").innerHTML = `<span>selected layer</span><h3>${title}</h3><p>${copy}</p><div>${tags.map((tag) => `<b>${tag}</b>`).join("")}</div>`;
}

function renderTimeline() {
  byId("researchTimeline").innerHTML = TIMELINE.map(([index, title, copy, status]) => `<article class="${status}"><span>${index}</span><div><small>${status === "proved" ? "established" : status === "progress" ? "measured advance" : "current frontier"}</small><h3>${title}</h3><p>${copy}</p></div><i></i></article>`).join("");
}

function renderLedger(filter = "all") {
  document.querySelectorAll("[data-ledger-filter]").forEach((button) => button.classList.toggle("active", button.dataset.ledgerFilter === filter));
  byId("claimLedger").innerHTML = CLAIMS.filter(([status]) => filter === "all" || status === filter).map(([status, title, copy]) => `<article class="${status}"><span>${status}</span><h3>${title}</h3><p>${copy}</p></article>`).join("");
}

function selectTab(key) {
  document.querySelectorAll("[data-atlas-tab]").forEach((button) => button.classList.toggle("active", button.dataset.atlasTab === key));
  document.querySelectorAll("[data-atlas-panel]").forEach((panel) => {
    const active = panel.dataset.atlasPanel === key;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
  });
}

atlasButton.addEventListener("click", openAtlas);
ribbonButton.addEventListener("click", openAtlas);
closeButton.addEventListener("click", closeAtlas);
atlas.addEventListener("click", (event) => { if (event.target === atlas) closeAtlas(); });
document.querySelectorAll("[data-atlas-tab]").forEach((button) => button.addEventListener("click", () => selectTab(button.dataset.atlasTab)));
document.querySelectorAll("[data-anatomy]").forEach((button) => button.addEventListener("click", () => renderAnatomy(button.dataset.anatomy)));
document.querySelectorAll("[data-ledger-filter]").forEach((button) => button.addEventListener("click", () => renderLedger(button.dataset.ledgerFilter)));
methodLink.addEventListener("click", closeAtlas);
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !atlas.hidden) closeAtlas(); });

renderMatrix();
renderSystems();
renderAnatomy("cover");
renderTimeline();
renderLedger();
