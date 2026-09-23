import * as THREE from 'three';
import { latticeTile, LATTICE_SCALE } from './chair-lattice.js';

const colors = new Map([[-1, 0x7054ba], [0, 0x63736d], [1, 0x008781]]);
const textures = new Map();

function pointTexture(value) {
  if (textures.has(value)) return textures.get(value);
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 64;
  const context = canvas.getContext('2d');
  context.fillStyle = context.strokeStyle = '#fff';
  context.beginPath();
  if (value === -1) {
    context.moveTo(32, 4); context.lineTo(60, 32);
    context.lineTo(32, 60); context.lineTo(4, 32);
    context.closePath(); context.fill();
  } else {
    context.arc(32, 32, value === 0 ? 23 : 27, 0, Math.PI * 2);
    if (value === 0) { context.lineWidth = 10; context.stroke(); }
    else context.fill();
  }
  const texture = new THREE.CanvasTexture(canvas);
  textures.set(value, texture);
  return texture;
}

export function makeLatticeMarkVisual(placements) {
  const entries = new Map();
  let assignmentCount = 0;
  for (const placement of placements) for (const { point, value } of latticeTile(placement).m) {
    const key = point.join(',');
    const previous = entries.get(key);
    if (previous && previous.value !== value) throw new Error('Conflicting scalar marking in displayed patch');
    if (previous) previous.assignments++;
    else entries.set(key, { point, value, assignments: 1 });
    assignmentCount++;
  }
  const group = new THREE.Group(), materials = [], geometries = [];
  group.name = 'chair44-lattice';
  group.userData.pointCount = entries.size;
  group.userData.assignmentCount = assignmentCount;
  for (const [value, color] of colors) {
    const positions = [], assignments = [];
    for (const entry of entries.values()) if (entry.value === value) {
      positions.push(...entry.point.map(coordinate => coordinate / LATTICE_SCALE));
      assignments.push(entry.assignments);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('assignments', new THREE.Uint8BufferAttribute(assignments, 1));
    const material = new THREE.PointsMaterial({
      color, map: pointTexture(value), size: 0.14, sizeAttenuation: true,
      transparent: true, opacity: 0.95, alphaTest: 0.05,
      depthWrite: false, depthTest: false,
    });
    material.userData.baseOpacity = 0.95;
    const points = new THREE.Points(geometry, material);
    points.userData.value = value;
    points.renderOrder = value === 0 ? 3 : 4;
    group.add(points); materials.push(material); geometries.push(geometry);
  }
  return { group, materials, geometries };
}
