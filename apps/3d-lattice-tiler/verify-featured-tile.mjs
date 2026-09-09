import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {tileSpecs,isGctsFigureVisibleInCatalog,GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES} from './engine.js';
import {MATHEMATICA_LATTICE_TILE as data} from '../../assets/mathematica-lattice-tile.js';
// Independent verification: signed tetrahedral decomposition, rather than
// the generator's edge turns / spherical vertex links / exact ray winding.
// All barycentric membership predicates use integer determinants. Only the
// independent angle cross-check is numerical; the generator certifies exactness.
const sub = (a, b) => a.map((x, i) => x-b[i]);
const dot = (a, b) => a.reduce((s, x, i) => s+x*b[i], 0);
const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const det = (a, b, c) => dot(a, cross(b, c));
const norm = a => Math.sqrt(dot(a, a));
function tetraWeight(p, q) {
  const [a, b, c] = q.slice(1).map(v => sub(v, q[0]));
  const d = det(a, b, c), v = sub(p, q[0]), sign = Math.sign(d);
  if (!d) return 0;
  const bary = [det(v, b, c), det(a, v, c), det(a, b, v)];
  bary.unshift(d-bary.reduce((s, x) => s+x, 0));
  const numerators = bary.map(x => x*sign);
  if (numerators.some(x => x < 0)) return 0;
  const positive = numerators.flatMap((x, i) => x > 0 ? [i] : []);
  if (positive.length === 4) return sign;
  if (positive.length === 3) return sign/2;
  if (positive.length === 2) {
    const [i, j] = positive, edge = sub(q[j], q[i]);
    const [u, w] = q.flatMap((x, k) => positive.includes(k) ? [] : [cross(edge, sub(x, q[i]))]);
    return sign*Math.acos(Math.max(-1, Math.min(1, dot(u, w)/(norm(u)*norm(w)))))/(2*Math.PI);
  }
  const [u, w, z] = q.flatMap((x, k) => k === positive[0] ? [] : [sub(x, p)]);
  const denominator = norm(u)*norm(w)*norm(z)+dot(u, w)*norm(z)+dot(w, z)*norm(u)+dot(z, u)*norm(w);
  return sign*Math.atan2(Math.abs(det(u, w, z)), denominator)/(2*Math.PI);
}

function checkShell(vertices, faces, points) {
  const edges = new Map(), tetrahedra = [];
  for (const f of faces) {
    for (let k = 0; k < f.length; k++) {
      const i = f[k], j = f[(k+1)%f.length], key = [i,j].sort((a,b)=>a-b).join(',');
      if (!edges.has(key)) edges.set(key, []);
      edges.get(key).push([i,j]);
    }
    for (let k = 1; k < f.length-1; k++) tetrahedra.push([vertices[0], vertices[f[0]], vertices[f[k]], vertices[f[k+1]]]);
  }
  assert.equal(edges.size, 33);
  for (const uses of edges.values()) {
    assert.equal(uses.length, 2);
    assert.deepEqual(uses[0], uses[1].slice().reverse());
  }
  assert.equal(tetrahedra.reduce((s, q) => s+det(...q.slice(1).map(v=>sub(v,q[0]))), 0)/6, 27);
  const expected = new Map(points.map(p => [p.pos.join(','), p.weight/24]));
  for (let x = 0; x <= 5; x++) for (let y = 0; y <= 5; y++) for (let z = 0; z <= 5; z++) {
    const p = [x,y,z], actual = tetrahedra.reduce((s, q) => s+tetraWeight(p,q), 0);
    assert.ok(Math.abs(actual-(expected.get(p.join(',')) ?? 0)) < 2e-14, `${p}: ${actual}`);
  }
}


const tile=tileSpecs.TILING_REGISTRY.mathematica_16_vertex.build()[0];
assert.equal(tile.name,'16-vertex lattice tile');
assert.equal(tile.geometry_model,'lattice_function');
assert.equal(tile.is_convex_polyhedron,false);
assert.equal(tile.solid_angle.max_value,24);
assert.equal(tile.occupancy_points.length,57);
assert.equal(tile.occupancy_points.reduce((s,p)=>s+p.weight,0),648);
assert.deepEqual(tile.faces,data.faces);
assert.equal(tile.is_chiral,true);
for(const t of [tile,tile.get_mirror_copy()]){
  checkShell(t.verts,t.faces,t.occupancy_points);
  assert.equal(t.unique_orientations.length,8);
  for(const o of t.unique_orientations)checkShell(o.verts,o.faces,o.occupancy);
}
const app=readFileSync(new URL('./app.js',import.meta.url),'utf8');
const code=app.slice(app.indexOf('const catalogGroupDefinitions ='),app.indexOf('function customPolycubeDisplayName'));
const groups=vm.runInNewContext(code+';groupedCatalogFigures()',{
  figureHasCategory:(figure,category)=>(figure.category??[]).includes(category),
  figureCatalog:tileSpecs.figureCatalog,prettyName:name=>name,polycubeCubeCount:()=>0,
  isGctsFigureVisibleInCatalog,GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES
});
assert.equal(groups[0].id,'featured');
assert.equal(groups[0].figures.length,1);
assert.equal(groups[0].figures[0].mode_key,'mathematica_16_vertex');
assert.equal(groups[0].figures[0].name,'16-vertex lattice tile');
const original=new Set(['featured','aperiodic','polycubes','fedorov','space','platonic','sphere','other']);
let researchSeen=false;
for(const group of groups){if(!original.has(group.id))researchSeen=true;else assert.equal(researchSeen,false);}
assert.equal(groups.reduce((n,g)=>n+g.figures.length,0),tileSpecs.figureCatalog.filter(isGctsFigureVisibleInCatalog).length);
console.log('Passed: featured tile first, original groups before research groups, all visible figures preserved; 57 exact weights and all 16 oriented shells verified.');
