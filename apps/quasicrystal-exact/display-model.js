// One-way display adapter. Approximate coordinates never enter the exact
// construction, predicates, identities, or exported certificate.
import { ORIENTATIONS, INTERNAL_STAR, internalPoint } from "../../assets/icosahedral-exact.js";
import { vector, vadd, cross, dot, pointKey } from "../../assets/golden-field.js";

const PHI_DISPLAY = (1 + Math.sqrt(5)) / 2;
export const displayScalar = x => (Number(x.a) + Number(x.b) * PHI_DISPLAY) / Number(x.d);
const displayPoint = v => v.map(displayScalar);
export const displayTile = t => ({
  kind: t.kind, axes: t.axes, vertices: t.vertices.map(displayPoint),
  keys: t.vertices.map(pointKey), faces: t.faces,
  exact: t.vertices.map(p => p.map(x => x.toJSON())),
  volume: t.volume.toJSON(), lift: t.lift?.map(String), decoration: t.decoration,
  dots: t.faceDots?.map((mark,face)=>({face,black:t.vertices.findIndex(v=>pointKey(v)===pointKey(mark.blackCorner)),red:t.vertices.findIndex(v=>pointKey(v)===pointKey(mark.redCorner))})),
  learnedPoints: t.learnedMarkings?.map(m=>({point:displayPoint(m.point),exact:m.point.map(x=>x.toJSON()),components:m.components})),
  pointValues: t.pointMarkings?.map(m=>({point:m.point.map(x=>x.toJSON()),components:m.components}))
});

export function makeDisplayModel(patch) {
  const displayTiles = patch.tiles.map(displayTile);
  // The finite grid-index crop includes detached boundary fragments. Select
  // its largest face-connected component for the initial display only.
  const incidence = new Map(), adjacency = displayTiles.map(() => new Set());
  displayTiles.forEach((t, i) => t.faces.forEach(face => {
    const key = face.map(j => t.keys[j]).sort().join('|');
    if (incidence.has(key)) { const j = incidence.get(key); adjacency[i].add(j); adjacency[j].add(i); }
    else incidence.set(key, i);
  }));
  const seen = new Set(); let connected = [];
  adjacency.forEach((_, i) => {
    if (seen.has(i)) return;
    const queue = [i], component = []; seen.add(i);
    while (queue.length) { const j = queue.pop(); component.push(j); for (const k of adjacency[j]) if (!seen.has(k)) { seen.add(k); queue.push(k); } }
    if (component.length > connected.length) connected = component;
  });
  const points = new Map();
  for (const t of patch.tiles) for (let mask = 0; mask < 8; mask++) {
    const lift = [...t.lift];
    t.axes.forEach((axis, j) => { if (mask & (1 << j)) lift[axis]++; });
    const key = lift.join(",");
    if (!points.has(key)) points.set(key, displayPoint(internalPoint(lift, patch.shifts)));
  }
  // Author the 30 window faces with EXACT supporting-plane predicates.
  const vertices = [], faces = [], keys = new Map();
  for (let i = 0; i < 6; i++) for (let j = i + 1; j < 6; j++) for (const side of [-1, 1]) {
    const normal = cross(INTERNAL_STAR[i], INTERNAL_STAR[j]);
    let base = vector(0n, 0n, 0n);
    INTERNAL_STAR.forEach((v, k) => {
      if (k !== i && k !== j && dot(normal, v).sign() === side) base = vadd(base, v);
    });
    let corners = [base, vadd(base, INTERNAL_STAR[i]), vadd(vadd(base, INTERNAL_STAR[i]), INTERNAL_STAR[j]), vadd(base, INTERNAL_STAR[j])];
    if (dot(cross(INTERNAL_STAR[i], INTERNAL_STAR[j]), normal).sign() !== side) corners = corners.reverse();
    faces.push(corners.map(p => {
      const key = pointKey(p);
      if (!keys.has(key)) { keys.set(key, vertices.length); vertices.push(displayPoint(p)); }
      return keys.get(key);
    }));
  }
  return { tiles: displayTiles, connected, prototypes: ["prolate", "oblate"].map(kind => displayTile(ORIENTATIONS.find(t => t.kind === kind))),
    window: { vertices, faces, points: [...points.values()] } };
}

// Display projection only: retain every assigned value when inspecting a
// rejected pair. A conflict must never be flattened into apparent agreement.
export function learnedDisplaySection(tiles){
 const section=new Map();for(const tile of tiles)for(const mark of tile.learnedPoints||[]){
  const key=JSON.stringify(mark.exact);if(!section.has(key))section.set(key,{...mark,refs:0,components:{},options:{}});const point=section.get(key);point.refs++;
  for(const [channel,value]of Object.entries(mark.components)){point.components[channel]=value;point.options[channel]??=[];if(!point.options[channel].includes(value))point.options[channel].push(value);}
 }
 return [...section.values()].map(point=>({...point,conflict:Object.values(point.options).some(values=>values.length>1)}));
}
