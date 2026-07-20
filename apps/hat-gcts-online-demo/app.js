const els = {
  patch: document.getElementById("patch-canvas"),
  marking: document.getElementById("marking-canvas"),
  step: document.getElementById("step-label"),
  title: document.getElementById("event-title"),
  badge: document.getElementById("event-badge"),
  message: document.getElementById("event-message"),
  support: document.getElementById("support-count"),
  domain: document.getElementById("domain-note"),
  tiles: document.getElementById("tile-count"),
  failures: document.getElementById("failure-count"),
  replay: document.getElementById("replay-status"),
  previous: document.getElementById("previous"),
  next: document.getElementById("next"),
  play: document.getElementById("play"),
  timeline: document.getElementById("timeline"),
  timelineValue: document.getElementById("timeline-value"),
  summary: document.getElementById("summary-grid"),
};

let data = null;
let frameIndex = 0;
let timer = null;

const labels = {
  start: "Unmarked seed",
  trial: "Try a branch",
  failure: "Branch fails",
  memoized: "Mismatch learned",
  "memo-hit": "Memory prunes",
  accept: "Branch accepted",
  "learning-failed": "Support horizon reached",
};

const colors = {
  start: "#376753",
  trial: "#d99033",
  failure: "#bb4a3a",
  memoized: "#326c90",
  "memo-hit": "#7a5d91",
  accept: "#376753",
};

function setupCanvas(canvas) {
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(rect.width));
  const height = Math.max(1, Math.round(rect.height));
  if (canvas.width !== width * ratio || canvas.height !== height * ratio) {
    canvas.width = width * ratio;
    canvas.height = height * ratio;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  return { ctx, width, height };
}

function boundsFor(polygons, padding = 0.8) {
  const points = polygons.flat();
  if (!points.length) return { minX: -1, maxX: 1, minY: -1, maxY: 1 };
  return {
    minX: Math.min(...points.map((p) => p[0])) - padding,
    maxX: Math.max(...points.map((p) => p[0])) + padding,
    minY: Math.min(...points.map((p) => p[1])) - padding,
    maxY: Math.max(...points.map((p) => p[1])) + padding,
  };
}

function projector(bounds, width, height, pad = 24) {
  const worldWidth = Math.max(.001, bounds.maxX - bounds.minX);
  const worldHeight = Math.max(.001, bounds.maxY - bounds.minY);
  const scale = Math.min((width - 2 * pad) / worldWidth, (height - 2 * pad) / worldHeight);
  const usedWidth = worldWidth * scale;
  const usedHeight = worldHeight * scale;
  const ox = (width - usedWidth) / 2;
  const oy = (height - usedHeight) / 2;
  return ([x, y]) => [ox + (x - bounds.minX) * scale, oy + (bounds.maxY - y) * scale];
}

function polygon(ctx, points, project, fill, stroke, lineWidth = 1.2) {
  if (!points.length) return;
  ctx.beginPath();
  points.forEach((point, index) => {
    const [x, y] = project(point);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = stroke;
  ctx.lineWidth = lineWidth;
  ctx.stroke();
}

function renderPatch(frame) {
  const { ctx, width, height } = setupCanvas(els.patch);
  const candidate = frame.candidate?.polygon || null;
  const polygons = frame.placements.map((item) => item.polygon);
  const all = candidate ? [...polygons, candidate] : polygons;
  const project = projector(boundsFor(all), width, height, 26);

  ctx.fillStyle = "#fffdf7";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "rgba(55, 103, 83, .07)";
  ctx.lineWidth = 1;
  for (let x = 20; x < width; x += 24) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
  }
  for (let y = 18; y < height; y += 24) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
  }

  polygons.forEach((points, index) => {
    const hue = 40 + (index % 4) * 5;
    polygon(ctx, points, project, `hsl(${hue} 48% ${82 - (index % 3) * 3}%)`, "#685d49");
  });
  if (candidate) {
    const isFailure = frame.type === "failure" || frame.type === "memo-hit" || frame.type === "memoized";
    ctx.save();
    ctx.globalAlpha = .68;
    polygon(ctx, candidate, project, isFailure ? "#e69a8e" : "#efc579", isFailure ? "#a9392b" : "#9a651f", 2.4);
    ctx.restore();
  }
}

function markItems(frame) {
  const fore = frame.marking?.site_fore || [];
  return fore.map((item) => ({ point: item[0], component: item.length === 2 ? 0 : item[1], value: item.length === 2 ? item[1] : item[2] }));
}

function supportPoints(frame) {
  return frame.support.map((item) => ({ point: item.point, component: item.component }));
}

function rawProject([x, y, z]) {
  return [x + y * .5, y * Math.sqrt(3) / 2];
}

function renderMarking(frame) {
  const { ctx, width, height } = setupCanvas(els.marking);
  // Site markings use doubled A2 coordinates, so draw the tile in that same
  // local coordinate system.
  const hat = data.hat.vertices.map(([x, y]) => [2 * x, 2 * y]);
  const marks = markItems(frame).map((item) => ({ ...item, projected: rawProject(item.point) }));
  const support = supportPoints(frame).map((item) => ({ ...item, projected: rawProject(item.point) }));
  const allPoints = [hat, ...support.map((item) => [item.projected])];
  const project = projector(boundsFor(allPoints, 1.1), width, height, 20);
  ctx.fillStyle = "#f0eee5";
  ctx.fillRect(0, 0, width, height);
  polygon(ctx, hat, project, "#e6dfce", "#514a3d", 1.4);

  const markByKey = new Map(marks.map((item) => [`${item.point.join(",")}:${item.component}`, item]));
  support.forEach((item) => {
    const [x, y] = project(item.projected);
    const mark = markByKey.get(`${item.point.join(",")}:${item.component}`);
    ctx.beginPath();
    ctx.arc(x, y, mark ? 7 : 4, 0, Math.PI * 2);
    if (!mark) {
      ctx.fillStyle = "#aaa596";
      ctx.fill();
      return;
    }
    const channelColors = ["#326c90", "#bb4a3a", "#7a5d91"];
    ctx.fillStyle = mark.value === 0 ? "#aaa596" : (channelColors[mark.component] || "#376753");
    ctx.fill();
    ctx.strokeStyle = mark.value < 0 ? "#fffdf7" : "#17211c";
    ctx.lineWidth = 1.6;
    ctx.stroke();
  });

  if (!support.length) {
    ctx.fillStyle = "#6f766f";
    ctx.font = "600 13px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("empty marking", width / 2, height - 22);
  }
}

function renderSummary(summary) {
  const cards = [
    [summary.tiles, "accepted Hats"],
    [summary.learned_failures, "failed branches encoded"],
    [summary.memo_hits, "later trials pruned by memory"],
    [summary.physical_support_sites, "physical A₂ support sites"],
    [summary.support_entries, "site/channel entries"],
    [summary.valid ? "passed" : "failed", "final prefix + memo replay"],
  ];
  els.summary.innerHTML = cards.map(([value, label]) => `<div class="summary-card"><strong>${value}</strong><span>${label}</span></div>`).join("");
}

function replayStatus(frame) {
  if (frame.type === "memoized") return frame.learning?.diagnostics?.accepted_replay ? "passed" : "failed";
  return frame.learned_failures ? "protected" : "not needed";
}

function render() {
  if (!data) return;
  const frame = data.trace[frameIndex];
  els.step.textContent = `Event ${frameIndex + 1} of ${data.trace.length}`;
  els.title.textContent = labels[frame.type] || frame.type;
  els.badge.textContent = frame.type;
  els.badge.style.color = colors[frame.type] || "#376753";
  els.badge.style.background = `${colors[frame.type] || "#376753"}18`;
  els.message.textContent = frame.message;
  els.tiles.textContent = frame.placements.length;
  els.failures.textContent = frame.learned_failures;
  els.replay.textContent = replayStatus(frame);
  els.support.textContent = `${frame.support.length} ${frame.support.length === 1 ? "entry" : "entries"}`;
  els.domain.textContent = frame.support.length
    ? `The domain now occupies ${new Set(frame.support.map((item) => item.point.join(","))).size} sparse physical site${frame.support.length === 1 ? "" : "s"}. Gray dots are allocated but currently unmarked; colored dots carry a signed channel value.`
    : "No domain has been allocated. The marking is empty.";
  els.timeline.value = frameIndex;
  els.timelineValue.textContent = String(frameIndex + 1);
  els.previous.disabled = frameIndex === 0;
  els.next.disabled = frameIndex === data.trace.length - 1;
  renderPatch(frame);
  renderMarking(frame);
}

function stop() {
  if (timer) window.clearInterval(timer);
  timer = null;
  els.play.textContent = "Play";
}

function setFrame(next) {
  frameIndex = Math.max(0, Math.min(data.trace.length - 1, next));
  render();
}

els.previous.addEventListener("click", () => { stop(); setFrame(frameIndex - 1); });
els.next.addEventListener("click", () => { stop(); setFrame(frameIndex + 1); });
els.timeline.addEventListener("input", (event) => { stop(); setFrame(Number(event.target.value)); });
els.play.addEventListener("click", () => {
  if (timer) { stop(); return; }
  if (frameIndex === data.trace.length - 1) setFrame(0);
  els.play.textContent = "Pause";
  timer = window.setInterval(() => {
    if (frameIndex >= data.trace.length - 1) { stop(); return; }
    setFrame(frameIndex + 1);
  }, 1050);
});

window.addEventListener("keydown", (event) => {
  if (!data || event.target.matches("input, button")) return;
  if (event.key === "ArrowLeft") setFrame(frameIndex - 1);
  if (event.key === "ArrowRight") setFrame(frameIndex + 1);
  if (event.key === " ") { event.preventDefault(); els.play.click(); }
});
window.addEventListener("resize", render);

fetch("./demo-trace.json")
  .then((response) => {
    if (!response.ok) throw new Error(`Trace request failed: ${response.status}`);
    return response.json();
  })
  .then((payload) => {
    data = payload;
    els.timeline.max = String(data.trace.length - 1);
    renderSummary(data.summary);
    render();
  })
  .catch((error) => {
    els.title.textContent = "Trace unavailable";
    els.message.textContent = error.message;
    els.badge.textContent = "error";
  });
