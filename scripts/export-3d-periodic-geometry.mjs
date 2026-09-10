import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {signedPermutations} from '../apps/3d-lattice-tiler/periodic-search.js';
import {MATHEMATICA_LATTICE_TILE as tile} from '../assets/mathematica-lattice-tile.js';
const dir=new URL('../runs/3d-periodic-rewrite-20260910/',import.meta.url);
const certificate=JSON.parse(readFileSync(new URL('regressions.json',dir))).summaries[0].tiling_evidence.certificate;
const sig=ps=>ps.map(p=>`${p.pos.join(',')}:${p.weight}`).sort().join('|');
const min=ps=>[0,1,2].map(i=>Math.min(...ps.map(p=>p.pos[i])));
const normal=ps=>{const m=min(ps);return sig(ps.map(p=>({...p,pos:p.pos.map((x,i)=>x-m[i])})));};
const placements=certificate.motif.map(m=>{
 const o=certificate.point_model.find(o=>o.type===m.prototile_idx&&o.index===m.orientation_index);
 for(const rotation of signedPermutations(certificate.include_reflections)){
  const ps=tile.points.map(p=>({weight:p.weight,pos:rotation.map(row=>row.reduce((n,x,i)=>n+x*p.pos[i],0))}));
  if(normal(ps)===normal(o.points))return {rotation,translation:m.translation.map((x,i)=>x+min(o.points)[i]-min(ps)[i])};
 }
 throw Error('Unmatched source orientation');
});
const source=readFileSync(new URL('../data/mathematica-lattice-tile.json',import.meta.url));
writeFileSync(new URL('eight-tile-rigid-motions.json',dir),JSON.stringify({kind:'periodic_lattice_polyhedron_tiling',tile:'mathematica_16_vertex',source_sha256:createHash('sha256').update(source).digest('hex'),include_reflections:certificate.include_reflections,dimensions:[certificate.hnf.a,certificate.hnf.d,certificate.hnf.f],period_vectors:certificate.period_vectors,capacity:24,placements},null,2));
