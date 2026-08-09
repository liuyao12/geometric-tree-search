import { BOUNDARY, CirclePackingSearch } from "../../assets/circle-packing-search.js";
import { CIRCLE_PACKING_SAMPLES, hydrateSample } from "../../assets/circle-packing-samples.js";

const $ = id => document.getElementById(id);
const elements = {
  bends: $("bends"), maxCircles: $("max-circles"), nodeLimit: $("node-limit"),
  run: $("run"), step: $("step"), reset: $("reset"), error: $("error"), canvas: $("packing"),
  statusTitle: $("status-title"), statusBadge: $("status-badge"), nodes: $("nodes"),
  depth: $("depth"), frontier: $("frontier"), dead: $("dead"), symmetry: $("symmetry"),
};

const palette = ["#d5a549", "#5e9b82", "#cd735b", "#6994ad", "#8b79a4", "#a4a65f"];
let search = null;
let running = false;
let savedSnapshot = null;

function parseBends() {
  const tokens = elements.bends.value.trim().split(/[\s,]+/).filter(Boolean);
  return tokens.map(token => Number(token));
}

function makeSearch() {
  const bends = parseBends();
  search = new CirclePackingSearch(bends, {
    maxCircles: Number(elements.maxCircles.value),
    nodeLimit: Number(elements.nodeLimit.value),
  });
  elements.error.textContent = "";
  return search;
}

function setupCanvas() {
  const ratio = Math.min(devicePixelRatio || 1, 2);
  const rect = elements.canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(rect.width));
  const height = Math.max(1, Math.round(rect.height));
  if (elements.canvas.width !== width * ratio || elements.canvas.height !== height * ratio) {
    elements.canvas.width = width * ratio;
    elements.canvas.height = height * ratio;
  }
  const ctx = elements.canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  return { ctx, width, height };
}

function renderPacking(snapshot) {
  const { ctx, width, height } = setupCanvas();
  const size = Math.min(width, height) * .79;
  const scale = size / 2;
  const cx = width / 2;
  const cy = height / 2;
  const project = circle => ({ x: cx + circle.x * scale, y: cy - circle.y * scale, r: circle.radius * scale });

  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, scale, 0, Math.PI * 2);
  ctx.fillStyle = "#f8f5eb";
  ctx.fill();
  ctx.clip();

  snapshot.contacts.forEach((neighbors, i) => {
    const from = project(snapshot.circles[i]);
    for (const neighbor of neighbors) {
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      if (neighbor === BOUNDARY) {
        const norm = Math.hypot(snapshot.circles[i].x, snapshot.circles[i].y) || 1;
        ctx.lineTo(cx + snapshot.circles[i].x / norm * scale, cy - snapshot.circles[i].y / norm * scale);
      } else if (neighbor > i) {
        const to = project(snapshot.circles[neighbor]);
        ctx.lineTo(to.x, to.y);
      } else continue;
      ctx.strokeStyle = "rgba(36,93,74,.42)";
      ctx.lineWidth = 1.4;
      ctx.stroke();
    }
  });

  const bendColors = new Map(search.bends.map((bend, i) => [bend, palette[i % palette.length]]));
  snapshot.circles.forEach((circle, index) => {
    const screen = project(circle);
    ctx.beginPath();
    ctx.arc(screen.x, screen.y, screen.r, 0, Math.PI * 2);
    ctx.fillStyle = `${bendColors.get(circle.bend)}d9`;
    ctx.fill();
    ctx.strokeStyle = index === snapshot.circles.length - 1 ? "#b95037" : "#263c33";
    ctx.lineWidth = index === snapshot.circles.length - 1 ? 3 : 1.25;
    ctx.stroke();
    if (screen.r > 19) {
      ctx.fillStyle = "#17221e";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = `750 ${Math.max(12, Math.min(24, screen.r * .48))}px Inter, sans-serif`;
      ctx.fillText(String(circle.bend), screen.x, screen.y);
    }
  });
  ctx.restore();

  ctx.beginPath();
  ctx.arc(cx, cy, scale, 0, Math.PI * 2);
  ctx.strokeStyle = "#17221e";
  ctx.lineWidth = 3;
  ctx.stroke();
}

const statusCopy = {
  running: ["Exploring corner branches", "running"],
  found: ["Packing certificate found", "found"],
  exhausted: ["Bounded tree exhausted", "exhausted"],
  node_limit: ["Node limit reached", "node limit"],
};

function render() {
  if (!search) return;
  const snapshot = savedSnapshot ?? search.snapshot();
  const [title, badge] = snapshot.saved
    ? ["Saved packing", `${snapshot.circles.length} circles`]
    : statusCopy[snapshot.status];
  elements.statusTitle.textContent = title;
  elements.statusBadge.textContent = badge;
  elements.statusBadge.className = `status ${snapshot.saved ? "saved" : snapshot.status}`;
  elements.nodes.textContent = snapshot.nodes.toLocaleString();
  elements.depth.textContent = snapshot.maxDepth;
  elements.frontier.textContent = snapshot.frontierStates.toLocaleString();
  elements.dead.textContent = snapshot.deadBranches.toLocaleString();
  elements.symmetry.textContent = snapshot.symmetryPrunes.toLocaleString();
  renderPacking(snapshot);
  if (snapshot.status !== "running") stopRunning();
}

function stopRunning() {
  running = false;
  elements.run.textContent = savedSnapshot
    ? "Run this search"
    : search?.status === "running" ? "Resume search" : "Run again";
  elements.run.classList.remove("running");
}

function frame() {
  if (!running || !search) return;
  search.step(250);
  render();
  if (running) requestAnimationFrame(frame);
}

elements.run.addEventListener("click", () => {
  try {
    if (running) {
      stopRunning();
      return;
    }
    if (!search || search.status !== "running") makeSearch();
    savedSnapshot = null;
    running = true;
    elements.run.textContent = "Pause search";
    elements.run.classList.add("running");
    requestAnimationFrame(frame);
  } catch (error) {
    elements.error.textContent = error.message;
  }
});

elements.step.addEventListener("click", () => {
  try {
    if (running) stopRunning();
    if (!search || search.status !== "running") makeSearch();
    savedSnapshot = null;
    search.step(1);
    render();
  } catch (error) {
    elements.error.textContent = error.message;
  }
});

elements.reset.addEventListener("click", () => {
  try {
    stopRunning();
    savedSnapshot = null;
    makeSearch();
    render();
  } catch (error) {
    elements.error.textContent = error.message;
  }
});

document.querySelectorAll("[data-example]").forEach(button => button.addEventListener("click", () => {
  elements.bends.value = button.dataset.example;
  elements.maxCircles.value = button.dataset.example === "3" ? "6"
    : button.dataset.example === "3, 4, 5, 6" ? "8" : "12";
  elements.reset.click();
}));

const sampleGrid = $("sample-grid");
sampleGrid.innerHTML = CIRCLE_PACKING_SAMPLES.map(sample =>
  `<button type="button" data-sample="${sample.id}" aria-label="Load saved bends ${sample.label}">{${sample.label}}</button>`
).join("");
sampleGrid.addEventListener("click", event => {
  const button = event.target.closest("[data-sample]");
  if (!button) return;
  const sample = CIRCLE_PACKING_SAMPLES.find(item => item.id === button.dataset.sample);
  stopRunning();
  elements.bends.value = sample.bends.join(", ");
  elements.maxCircles.value = String(sample.maxCircles);
  makeSearch();
  const circles = hydrateSample(sample);
  savedSnapshot = {
    saved: true,
    status: "found",
    nodes: sample.searchNodes,
    maxDepth: circles.length,
    frontierStates: 0,
    deadBranches: 0,
    symmetryPrunes: 0,
    circles,
    contacts: search.contacts(circles),
  };
  elements.run.textContent = "Run search";
  render();
});

window.addEventListener("resize", () => render());
makeSearch();
render();
