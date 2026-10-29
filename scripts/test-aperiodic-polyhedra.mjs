import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {Golden as G,ZERO,vector,vsub,cross,dot,determinant,pointKey} from '../assets/golden-field.js';
import {buildSpecimens,volume} from './build-aperiodic-polyhedra.mjs';
import {T13,WANG21,cubeProjection,wangFacesAgree} from '../assets/aperiodic-wang-cubes.js';
const systems=buildSpecimens();let count=0;
function verify(t,{pointJunction=false}={}){
 assert(volume(t).sign()>0,t.id);const edges=new Map();for(const f of t.faces){assert(f.length>=3);const [a,b,c]=f.map(i=>t.vertices[i]),normal=cross(vsub(b,a),vsub(c,a));assert(dot(normal,normal).sign());for(const i of f)assert(!dot(normal,vsub(t.vertices[i],a)).sign(),'Every facet is exactly planar');for(let i=0;i<f.length;i++){const x=f[i],y=f[(i+1)%f.length],key=[x,y].sort((a,b)=>a-b).join(',');edges.set(key,(edges.get(key)||0)+(x<y?1:-1));}}
 assert([...edges.values()].every(x=>x===0),`${t.id}: oriented boundary edges cancel`);
 // Each mesh is independently checked against the already-built wire format.
 count++;
}
for(const tiles of Object.values(systems))for(const t of tiles)verify(t);
assert.deepEqual(systems.socolar.map(t=>t.faces.length),[6,12,20,30]);
assert.deepEqual(systems.danzer.map(t=>t.rightAngleEdges.length),[1,1,1,3]);
for(let i=0;i<4;i++){assert.equal(systems.danzerOcta[i].faces.length,8);assert(volume(systems.danzerOcta[i]).equals(volume(systems.danzer[i]).mul(i===3?8n:4n)));}
assert(volume(systems.goodman[0]).equals(new G(5n,0n,12n)));assert(volume(systems.goodman[1]).equals(new G(27n,0n,4n)));assert(volume(systems.scd[0]).equals(20n));
assert.equal(WANG21.length,21);assert.equal(new Set(WANG21.map(t=>JSON.stringify(t.colors))).size,21);const originals=new Set(T13.map(JSON.stringify));for(const c of WANG21)assert(originals.has(JSON.stringify(cubeProjection(c))),`Cube ${c.id} must project to an actual source transition`);
assert.equal(WANG21.filter(t=>t.family==='A').length,9);assert.equal(WANG21.filter(t=>t.family==='B').length,8);assert.equal(WANG21.filter(t=>t.family==='C').length,4);
const serialized=JSON.parse(await readFile(new URL('../apps/quasicrystal-exact/data/polyhedra-exact.json',import.meta.url),'utf8'));
for(const [system,tiles]of Object.entries(systems))for(const [i,t]of tiles.entries()){assert.deepEqual(JSON.parse(JSON.stringify(t.vertices)),serialized.systems[system][i].vertices);assert.deepEqual(t.faces,serialized.systems[system][i].faces);}
console.log(`ok: ${count} exact meshes; oriented boundaries close; zonohedron facets; Danzer right angles and compound volumes; rational I/L and SCD geometry; 21 symbolic cubes with verified source projections`);
// Exercise the browser data adapter with local reads, independently of WebGL.
globalThis.fetch=async url=>({ok:true,json:async()=>JSON.parse(await readFile(url,'utf8'))});
const {SYSTEMS,loadSpecimens,reflectedSpecimen}=await import('../apps/quasicrystal-exact/polyhedral-catalog.js');let specimens=0;
for(const s of SYSTEMS){const tiles=await loadSpecimens(s.id);specimens+=tiles.length;for(const t of tiles){assert(t.vertices.length&&t.faces.length);assert(t.vertices.flat().every(Number.isFinite));if(t.exact){assert.equal(t.exact.length,t.vertices.length);for(const p of t.exact)for(const x of p)assert.deepEqual(G.fromJSON(x).toJSON(),x,'Exact scalar records are canonical');for(const f of t.faces)for(const i of f)assert(i>=0&&i<t.vertices.length);const r=reflectedSpecimen(reflectedSpecimen(t));assert.deepEqual(r.exact,t.exact);}}
 if(s.id==='wang')assert(tiles.every(t=>t.pointMarkings.length===6));
 if(s.id==='taylor')assert(tiles.every(t=>t.displayOnly&&!t.exact));
}
assert.equal(specimens,44);assert.equal(SYSTEMS.length,11);console.log(`ok: ${SYSTEMS.length} source entries and ${specimens} adapted specimens; exact scalars canonical; reflection involution; display-only STL stays separate`);
