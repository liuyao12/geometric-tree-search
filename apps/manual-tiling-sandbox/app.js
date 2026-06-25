const canvas = document.getElementById('sandbox');
const ctx = canvas.getContext('2d');
const statusEl = document.getElementById('status');
const clearButton = document.getElementById('clearBoard');

const BLUE = '#0072b2', BLUE_STROKE = '#005a8c', ORANGE = '#d55e00', ORANGE_STROKE = '#a74700';
const sqrt2 = Math.sqrt(2), sqrt6 = Math.sqrt(6), latticeScale = 24;
const trefoilVerts = [[1,0,-1],[2,0,-2],[2,1,-3],[0,2,-2],[-1,1,0],[-2,2,0],[-3,2,1],[-2,0,2],[0,-1,1],[0,-2,2],[1,-3,2],[2,-2,0]];
const turtleVerts = [[3,-2,-1],[2,0,-2],[0,1,-1],[0,2,-2],[-1,3,-2],[-2,2,0],[-1,0,1],[-2,0,2],[-2,-1,3],[0,-2,2],[1,-4,3],[2,-4,2],[3,-5,2],[4,-4,0]];
const trefoilStripeDefs = [{from:0,to:6,value:-1},{from:4,to:10,value:-1},{from:8,to:2,value:-1}];
const turtleStripeDefs = [{from:0,to:10,value:1},{from:2,to:8,value:-1},{from:0,to:6,value:-1},{from:4,to:12,value:-1}];
const tileDefs = {
  turtle: { verts: turtleVerts, stripes: turtleStripeDefs, fill: 'rgba(0,114,178,.42)', stroke: BLUE_STROKE },
  blueTrefoil: { verts: trefoilVerts, stripes: trefoilStripeDefs, fill: 'rgba(0,114,178,.48)', stroke: BLUE_STROKE },
  orangeTrefoil: { verts: trefoilVerts, stripes: trefoilStripeDefs.map(s => ({ ...s, value: 1 })), fill: 'rgba(213,94,0,.48)', stroke: ORANGE_STROKE, reflect: true }
};
const palette = [
  { kind: 'turtle', label: 'Turtle', x: 92, y: 120 },
  { kind: 'blueTrefoil', label: 'Blue trefoil', x: 92, y: 270 },
  { kind: 'orangeTrefoil', label: 'Orange trefoil', x: 92, y: 420 },
  { kind: 'orangeTrefoil', label: 'Orange trefoil rotated', x: 92, y: 570, rotation: Math.PI / 3 }
];
let placed = [];
let drag = null;
let pendingDraw = false;
let tileScale = 0.9;
const trash = { x: 42, y: 690, w: 100, h: 100 };
let nextId = 1;

function setStatus(text) { statusEl.textContent = text; }
function projectRaw([x,y,z]) { return { x: ((z-x)/sqrt2)*latticeScale, y: ((2*y-x-z)/sqrt6)*latticeScale }; }
const allBase = [...turtleVerts, ...trefoilVerts].map(projectRaw);
const center = allBase.reduce((sum, point) => ({ x: sum.x + point.x / allBase.length, y: sum.y + point.y / allBase.length }), { x: 0, y: 0 });
function project(point) { const q = projectRaw(point); return { x: q.x - center.x, y: q.y - center.y }; }
function eventPoint(event) {
  const rect = canvas.getBoundingClientRect();
  return { x: (event.clientX - rect.left) * canvas.width / rect.width, y: (event.clientY - rect.top) * canvas.height / rect.height };
}
function tilePoints(tile) {
  const def = tileDefs[tile.kind];
  const angle = tile.rotation || 0;
  const cos = Math.cos(angle), sin = Math.sin(angle);
  return def.verts.map(vertex => {
    const raw = project(vertex);
    const reflectedX = def.reflect ? -raw.x : raw.x;
    const x = reflectedX * tileScale, y = raw.y * tileScale;
    return { x: tile.x + x * cos - y * sin, y: tile.y + x * sin + y * cos };
  });
}
function drawPath(points, fill, stroke, width = 2.2) {
  ctx.beginPath();
  points.forEach((point, index) => index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y));
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = stroke;
  ctx.lineWidth = width;
  ctx.stroke();
}
function drawStripe(a, b, value) {
  ctx.strokeStyle = value > 0 ? ORANGE : BLUE;
  ctx.lineWidth = 2.4;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(a.x, a.y);
  ctx.lineTo(b.x, b.y);
  ctx.stroke();
}
function scheduleDraw() {
  if (pendingDraw) return;
  pendingDraw = true;
  window.requestAnimationFrame(() => { pendingDraw = false; draw(); });
}
function drawTile(tile, { paletteTile = false } = {}) {
  const def = tileDefs[tile.kind];
  const points = tilePoints(tile);
  drawPath(points, def.fill, def.stroke, paletteTile ? 2.2 : 2.8);
  def.stripes.forEach(stripe => drawStripe(points[stripe.from], points[stripe.to], stripe.value));
}
function pointInTile(point, tile) {
  const points = tilePoints(tile);
  let inside = false;
  for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
    const a = points[i], b = points[j];
    if ((a.y > point.y) !== (b.y > point.y) && point.x < ((b.x - a.x) * (point.y - a.y)) / (b.y - a.y) + a.x) inside = !inside;
  }
  return inside;
}
function hitPlaced(point) {
  for (let index = placed.length - 1; index >= 0; index -= 1) if (pointInTile(point, placed[index])) return { tile: placed[index], index };
  return null;
}
function hitPalette(point) {
  return palette.find(tile => pointInTile(point, tile));
}
function pointInTrash(point) { return point.x >= trash.x && point.x <= trash.x + trash.w && point.y >= trash.y && point.y <= trash.y + trash.h; }
function drawTrash() {
  ctx.save();
  ctx.strokeStyle = drag?.overTrash ? ORANGE : '#b8c3bf';
  ctx.fillStyle = drag?.overTrash ? '#fff1e8' : '#f7faf8';
  ctx.lineWidth = 3;
  ctx.fillRect(trash.x, trash.y, trash.w, trash.h);
  ctx.setLineDash([7, 6]);
  ctx.strokeRect(trash.x, trash.y, trash.w, trash.h);
  ctx.setLineDash([]);
  ctx.fillStyle = '#52645f';
  ctx.font = '42px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('🗑', trash.x + trash.w / 2, trash.y + trash.h / 2);
  ctx.restore();
}
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#eef4f1';
  ctx.fillRect(0, 0, 172, canvas.height);
  ctx.strokeStyle = '#cbd8d4';
  ctx.beginPath();
  ctx.moveTo(172, 0);
  ctx.lineTo(172, canvas.height);
  ctx.stroke();
  palette.forEach(tile => drawTile(tile, { paletteTile: true }));
  drawTrash();
  placed.forEach(tile => drawTile(tile));
  if (drag?.tile && drag.active) drawTile(drag.tile);
}
function beginDrag(event) {
  const point = eventPoint(event);
  const placedHit = hitPlaced(point);
  if (placedHit) {
    const [tile] = placed.splice(placedHit.index, 1);
    drag = { tile, dx: point.x - tile.x, dy: point.y - tile.y, fromPalette: false, start: point, active: false, overTrash: false };
  } else {
    const paletteHit = hitPalette(point);
    if (!paletteHit) return;
    drag = { tile: { ...paletteHit, id: nextId++ }, dx: point.x - paletteHit.x, dy: point.y - paletteHit.y, fromPalette: true, start: point, active: false, overTrash: false };
  }
  canvas.classList.add('dragging');
  canvas.setPointerCapture(event.pointerId);
  setStatus('ready to drag');
  event.preventDefault();
  scheduleDraw();
}
function moveDrag(event) {
  if (!drag) return;
  const point = eventPoint(event);
  const distance = Math.hypot(point.x - drag.start.x, point.y - drag.start.y);
  if (!drag.active && distance >= 4) drag.active = true;
  if (drag.active) {
    drag.tile.x = point.x - drag.dx;
    drag.tile.y = point.y - drag.dy;
    drag.overTrash = pointInTrash(point);
    setStatus(drag.overTrash ? 'release to delete' : 'dragging');
  }
  event.preventDefault();
  scheduleDraw();
}
function endDrag(event) {
  if (!drag) return;
  const point = eventPoint(event);
  const shouldDelete = drag.active && pointInTrash(point);
  if (!shouldDelete && (!drag.fromPalette || drag.active)) placed.push(drag.tile);
  drag = null;
  canvas.classList.remove('dragging');
  canvas.releasePointerCapture?.(event.pointerId);
  setStatus(shouldDelete ? 'deleted' : `${placed.length} tile${placed.length === 1 ? '' : 's'}`);
  event.preventDefault();
  draw();
}
canvas.addEventListener('pointerdown', beginDrag);
canvas.addEventListener('pointermove', moveDrag);
canvas.addEventListener('pointerup', endDrag);
canvas.addEventListener('pointercancel', () => { if (drag && !drag.fromPalette) placed.push(drag.tile); drag = null; canvas.classList.remove('dragging'); setStatus('cancelled'); draw(); });
canvas.addEventListener('wheel', event => {
  event.preventDefault();
  tileScale = Math.max(0.35, Math.min(2.4, tileScale * Math.exp(-event.deltaY * 0.001)));
  draw();
}, { passive: false });
clearButton.addEventListener('click', () => { placed = []; setStatus('ready'); draw(); });
draw();
