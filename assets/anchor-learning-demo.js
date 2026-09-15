import { CORNERS, VERSION, createModel, objective, trainStep, compileModel, search } from './anchor-learning.js';

const card = document.getElementById('turtle-tiling-card');
const select = document.getElementById('tiling-lane');
const panel = document.getElementById('anchor-lane');
const $ = id => document.getElementById(id);
let model, initial, elapsed, running = false, lastTime, iterator = null, frame = null, result = null, compiled = null;
const canvas = $('anchor-canvas'), ctx = canvas.getContext('2d');
const train = $('anchor-train'), check = $('anchor-check'), freeze = $('anchor-freeze');
const seed = $('anchor-seed');
let trainingMode = true;
let animation = 0;
function reset() {
  stop();
  model = createModel(Number(seed.value) || 7);
  initial = structuredClone(model); elapsed = 0; iterator = null; frame = null; result = null; compiled = null;
  trainingMode = !freeze.checked;
  $('anchor-result').textContent = 'Perturbed square prototype. Train, then freeze and check a projected exact model.';
  draw();
}
function stop() { running = false; cancelAnimationFrame(animation); train.textContent = 'Train'; }
function activate() {
  const active = select.value === 'anchors';
  if (active && $('turtle-start').textContent === 'Pause tiling') $('turtle-start').click();
  if (!active) stop();
  for (const child of card.children) if (child.matches('.interactive-toolbar, #turtle-tiling, figcaption')) child.hidden = active;
  panel.hidden = !active;
  card.classList.toggle('anchor-active', active);
  if (active) draw();
  window.dispatchEvent(new Event('resize'));
}
function draw() {
  const loss = objective(model);
  const movement = Math.sqrt(model.anchors.reduce((s, p, i) => s + (p.x - initial.anchors[i].x) ** 2 + (p.y - initial.anchors[i].y) ** 2, 0) / 4);
  $('anchor-metrics').textContent = `Step ${model.step} · loss ${loss.loss.toExponential(2)} · anchor RMS move ${movement.toFixed(3)} · ${elapsed.toFixed(0)} ms training`;
  $('anchor-loss').textContent = `Contact ${loss.terms.contact.toExponential(1)} · coverage ${loss.terms.coverage.toExponential(1)} · marking ${loss.terms.marking.toExponential(1)}`;
  $('anchor-values').textContent = model.anchors.map((p, i) => `${i + 1}: (${p.x.toFixed(3)}, ${p.y.toFixed(3)})  t ${p.t.toFixed(3)}  m ${p.m.toFixed(3)}`).join('\n');
  check.disabled = running || model.step === 0;
  $('anchor-export').disabled = !result;
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#faf8f2'; ctx.fillRect(0, 0, w, h);
  const left = 34, top = 61, unit = 120;
  const pos = p => [left + (p.x + .5) * unit, top + (p.y + .5) * unit];
  ctx.font = '15px system-ui'; ctx.fillStyle = '#313d3b'; ctx.fillText('Learned prototype', 22, 25);
  ctx.fillText(frame ? 'Exact search · 4 × 4 torus' : 'Shared contacts · translated copies', 320, 25);
  ctx.strokeStyle = '#dddcd3'; ctx.lineWidth = 1;
  for (let i = 0; i < 3; i++) {
    ctx.beginPath(); ctx.moveTo(left + i * unit, 40); ctx.lineTo(left + i * unit, h - 20); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(15, top + i * unit); ctx.lineTo(290, top + i * unit); ctx.stroke();
  }
  ctx.setLineDash([4, 4]); ctx.strokeStyle = '#aaa99d'; ctx.beginPath();
  CORNERS.forEach(([x, y], i) => { const q = pos({ x, y }); i ? ctx.lineTo(...q) : ctx.moveTo(...q); }); ctx.closePath(); ctx.stroke(); ctx.setLineDash([]);
  ctx.strokeStyle = '#d17d44'; ctx.beginPath();
  model.anchors.forEach((p, i) => { const q = pos(p); i ? ctx.lineTo(...q) : ctx.moveTo(...q); }); ctx.closePath(); ctx.stroke();
  model.anchors.forEach((p, i) => {
    const q = pos(p), start = pos(initial.anchors[i]);
    ctx.strokeStyle = '#b9b5a7'; ctx.beginPath(); ctx.moveTo(...start); ctx.lineTo(...q); ctx.stroke();
    ctx.strokeRect(start[0] - 3, start[1] - 3, 6, 6);
    ctx.fillStyle = p.m >= 0 ? '#ad5737' : '#247b83'; ctx.beginPath(); ctx.arc(...q, 5 + 14 * p.t, 0, 2 * Math.PI); ctx.fill();
    ctx.fillStyle = '#303a38'; ctx.font = '13px system-ui'; ctx.fillText(String(i + 1), q[0] + 13, q[1] - 11);
  });
  if (frame) {
    const s = 52, ox = 348, oy = 77;
    const chosen = new Set(frame.selected);
    for (const c of frame.problem.candidates) if (chosen.has(c.id)) {
      ctx.fillStyle = c.phase > 0 ? '#c6dfe0' : '#ebcbb7';
      ctx.fillRect(ox + c.x * s, oy + c.y * s, s - 2, s - 2);
    }
    frame.graph.totals.forEach((t, p) => {
      const x = ox + (p % 4) * s, y = oy + Math.floor(p / 4) * s;
      ctx.fillStyle = t === 12 ? '#277d68' : '#fff'; ctx.strokeStyle = '#66716c';
      ctx.beginPath(); ctx.arc(x, y, 7, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#243b36'; ctx.font = '11px system-ui'; ctx.fillText(`${t}/12`, x + 10, y - 7);
    });
    ctx.font = '12px system-ui'; ctx.fillText('Opposite edges identified; all 16 points required.', 320, h - 18);
  } else {
    for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) {
      const u = 83, ox = 367 + x * u, oy = 101 + y * u;
      ctx.strokeStyle = '#c3c6bb'; ctx.strokeRect(ox, oy, u, u);
      model.anchors.forEach(p => {
        const mark = p.m * ((x + y) % 2 ? -1 : 1);
        ctx.fillStyle = mark >= 0 ? '#ad5737aa' : '#247b83aa';
        ctx.beginPath(); ctx.arc(ox + p.x * u, oy + p.y * u, 5 + p.t * 9, 0, Math.PI * 2); ctx.fill();
      });
    }
    ctx.font = '12px system-ui'; ctx.fillStyle = '#384a43'; ctx.fillText('Color = m sign · radius = t · square = initial anchor', 320, h - 18);
  }
}
function tick(time) {
  if (!running) return;
  if (time - lastTime > 25) {
    const started = performance.now();
    for (let i = 0; i < 2; i++) trainStep(model, { moveAnchors: trainingMode });
    elapsed += performance.now() - started;
    lastTime = time;
    if (model.step >= 300) {
      stop();
      $('anchor-result').textContent = trainingMode ? 'Training complete. Freeze and check the projected model.' : 'Frozen-anchor control complete. Contact error remains; exact compilation may fail.';
    }
    draw();
  }
  if (running) animation = requestAnimationFrame(tick);
}
train.addEventListener('click', () => {
  if (running) { stop(); draw(); return; }
  if (model.step >= 300 || result || iterator) reset();
  frame = null; compiled = null; result = null;
  trainingMode = !freeze.checked; running = true; lastTime = 0; train.textContent = 'Pause';
  $('anchor-result').textContent = trainingMode ? 'Learning anchor coordinates, t-values and m-values…' : 'Learning t and m with anchor coordinates frozen…';
  draw(); animation = requestAnimationFrame(tick);
});
$('anchor-reset').addEventListener('click', reset);
freeze.addEventListener('change', reset);
seed.addEventListener('change', () => { seed.value = Math.max(1, Math.min(9999, Math.round(Number(seed.value) || 7))); reset(); });
check.addEventListener('click', () => {
  stop(); compiled = compileModel(model); result = null; frame = null;
  if (!compiled.ok) { $('anchor-result').textContent = `${compiled.reason} No exact result.`; draw(); return; }
  iterator = search(compiled);
  const active = iterator;
  const start = performance.now();
  let searchMs = 0;
  function step() {
    if (iterator !== active) return;
    const started = performance.now();
    const next = active.next();
    searchMs += performance.now() - started;
    if (next.done) {
      result = { ...next.value, searchMs, playbackMs: performance.now() - start };
      iterator = null;
      const s = result.stats;
      $('anchor-result').textContent = `${result.status}: ${s.accepted} placements · ${s.attempts} attempts · ${s.forced} forced · ${s.branches} branches · ${s.backtracks} backtracks · ${searchMs.toFixed(1)} ms search. Exact for the rounded model only.`;
    } else {
      frame = next.value;
      $('anchor-result').textContent = `${frame.selected.length} placements · ${frame.graph.frontier.size} frontier points · ${frame.graph.reverse.size} legal candidates · ${frame.graph.markingEliminations} currently excluded by m · ${frame.graph.capacityEliminations} by capacity`;
      setTimeout(step, 65);
    }
    draw(); check.disabled = !!iterator;
  }
  step();
});
$('anchor-export').addEventListener('click', () => {
  const data = { version: VERSION, training: { model, initial, moveAnchors: trainingMode, elapsedMs: elapsed,
    objective: objective(model).terms, supervision: 'Unit-square contact graph; fixed unit translations; centroid gauge; D4 t-symmetry; nonzero marking norm.' }, result };
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = 'gcts-moving-anchors.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
select.addEventListener('change', activate);
// The parent Turtle card supports drag gestures; experiment controls and its
// scrollable details must retain their ordinary pointer behavior.
panel.addEventListener('pointerdown', event => event.stopPropagation());
function hashLane() {
  if (location.hash === '#anchor-learning') {
    select.value = 'anchors'; activate();
    if (window.innerWidth <= 900) card.scrollIntoView({ block: 'start' });
  }
}
window.addEventListener('hashchange', hashLane);
reset(); hashLane();
