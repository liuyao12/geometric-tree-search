import * as THREE from 'three';
import {VARIANTS,COLORS,apply} from './chair44.js';
import {tetraBoundary,TETRA_FEATURES} from './tetra-relief.js?v=20260923-apex-shift';
const boundary=tetraBoundary();
// Keep the triangular base rims and hinges even where the surface is coplanar.
// Shared edges are drawn once, so transparent outlines do not become darker.
const pyramidEdges=new Map(),seenEdges=new Set();
for(const {vertices,color} of TETRA_FEATURES){
  if(!pyramidEdges.has(color))pyramidEdges.set(color,[]);
  for(let i=0;i<4;i++)for(let j=i+1;j<4;j++){
    const edgeKey=[vertices[i].join(','),vertices[j].join(',')].sort().join('|');
    if(seenEdges.has(edgeKey))continue;
    seenEdges.add(edgeKey);pyramidEdges.get(color).push(vertices[i],vertices[j]);
  }
}
export function makeReliefVisual(placements) {
  const group=new THREE.Group(),materials=[],geometries=[];
  group.name='chair44-relief';
  const flat=[],colored=new Map(Object.keys(COLORS).map(c=>[c,[]]));
  const outlines=new Map(Object.keys(COLORS).map(c=>[c,[]]));
  const protrusions=16*placements.length,indents=16*placements.length;
  for(const placement of placements){
    const rotation=VARIANTS[placement.variantId].rotation;
    const transform=p=>apply(rotation,p.map(v=>v/6-1)).map((v,i)=>v+1+placement.origin[i]);
    for(const [color,vertices] of pyramidEdges)
      for(const p of vertices)outlines.get(color).push(...transform(p));
    for(const {vertices,color} of boundary){
      const target=color?colored.get(color):flat;
      for(let i=1;i<vertices.length-1;i++)for(const p of [vertices[0],vertices[i],vertices[i+1]])target.push(...transform(p));
    }
  }
  const geometryFor = positions => {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.computeVertexNormals(); geometries.push(geometry); return geometry;
  };
  const neutral = new THREE.MeshBasicMaterial({ color: 0xf0f1e9, transparent: true,
    opacity: .18, side: THREE.DoubleSide, depthWrite: false });
  neutral.userData.baseOpacity = .18; materials.push(neutral);
  const panels = new THREE.Mesh(geometryFor(flat), neutral); panels.renderOrder = 1; group.add(panels);
  for (const [color, positions] of colored) {
    const geometry = geometryFor(positions);
    const material = new THREE.MeshStandardMaterial({ color: COLORS[color], roughness: .8,
      metalness: 0, flatShading: true, transparent: true, opacity: .42,
      side: THREE.FrontSide, depthWrite: false });
    material.userData.baseOpacity = .42;
    const rear = material.clone(); rear.side = THREE.BackSide; rear.opacity = .16; rear.userData.baseOpacity = .16;
    const back = new THREE.Mesh(geometry, rear); back.renderOrder = 3;
    const front = new THREE.Mesh(geometry, material); front.renderOrder = 4;
    group.add(back, front); materials.push(rear, material);
    const edges = new THREE.BufferGeometry();
    edges.setAttribute('position', new THREE.Float32BufferAttribute(outlines.get(color), 3));
    geometries.push(edges);
    const edgeMaterial = new THREE.LineBasicMaterial({ color: 0x354842, transparent: true, opacity: .68, depthWrite: false });
    edgeMaterial.userData.baseOpacity = .68; materials.push(edgeMaterial);
    const lines = new THREE.LineSegments(edges, edgeMaterial);
    lines.name = `chair44-relief-${color}-creases`;
    lines.renderOrder = 5; group.add(lines);
  }
  group.userData.protrusions = protrusions;
  group.userData.indents = indents;
  return { group, materials, geometries };
}
