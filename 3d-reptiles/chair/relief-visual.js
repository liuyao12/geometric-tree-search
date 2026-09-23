import * as THREE from 'three';
import { worldMarks, COLORS } from './chair44.js';
import { reliefFeatures, reliefFrame, reliefPoint } from './relief-profile.js';

export function makeReliefVisual(placements) {
  const group = new THREE.Group(), materials = [], geometries = [];
  group.name = 'chair44-relief';
  const flat = [], colored = new Map(Object.keys(COLORS).map(color => [color, []]));
  let protrusions = 0, indents = 0;
  for (const placement of placements) for (const mark of worldMarks(placement)) {
    const frame = reliefFrame(mark), features = reliefFeatures(mark.color);
    const tangents = [0, 1, 2].filter(i => mark.direction[i] === 0);
    const contour = [[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]].map(pair => {
      const delta = [0, 0, 0]; tangents.forEach((axis, i) => { delta[axis] = pair[i]; });
      return new THREE.Vector2(delta.reduce((sum, v, i) => sum + v * frame.side[i], 0),
        delta.reduce((sum, v, i) => sum + v * frame.forward[i], 0));
    }).sort((a, b) => Math.atan2(a.y, a.x) - Math.atan2(b.y, b.x));
    const bases = features.map(feature => [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([x, y]) =>
      new THREE.Vector2(feature.u + x * feature.radius, feature.v + y * feature.radius)));
    // Cut actual holes in each flat panel; pyramid sides close them, upwards
    // for a bump and downwards for a recess. No flat face covers an indent.
    const holes = bases.map(base => [...base].reverse());
    const points = [...contour, ...holes.flat()];
    for (const face of THREE.ShapeUtils.triangulateShape(contour, holes)) {
      const [a, b, c] = face.map(index => points[index]);
      if ((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x) < 0) face.reverse();
      // Earcut may bridge collinear corners of the two blue holes with one
      // long edge. Split it at every corner so the relief is watertight.
      const boundary = [];
      for (let edge = 0; edge < 3; edge++) {
        const start = points[face[edge]], end = points[face[(edge + 1) % 3]];
        const dx = end.x - start.x, dy = end.y - start.y, length2 = dx * dx + dy * dy;
        boundary.push(start);
        const inside = points.map(point => ({ point, t: ((point.x - start.x) * dx + (point.y - start.y) * dy) / length2 }))
          .filter(({ point, t }) => t > 1e-9 && t < 1 - 1e-9 && Math.abs((point.x - start.x) * dy - (point.y - start.y) * dx) < 1e-9)
          .sort((left, right) => left.t - right.t);
        boundary.push(...inside.map(entry => entry.point));
      }
      if (boundary.length === 3) {
        for (const point of boundary) flat.push(...reliefPoint(frame, point.x, point.y));
      } else {
        const center = new THREE.Vector2((a.x + b.x + c.x) / 3, (a.y + b.y + c.y) / 3);
        for (let edge = 0; edge < boundary.length; edge++) {
          for (const point of [center, boundary[edge], boundary[(edge + 1) % boundary.length]]) flat.push(...reliefPoint(frame, point.x, point.y));
        }
      }
    }
    features.forEach((feature, i) => {
      if (feature.height > 0) protrusions++; else indents++;
      const base = bases[i], apex = reliefPoint(frame, feature.u, feature.v, feature.height);
      for (let edge = 0; edge < 4; edge++) {
        const a = base[edge], b = base[(edge + 1) % 4];
        colored.get(mark.color).push(...reliefPoint(frame, a.x, a.y), ...reliefPoint(frame, b.x, b.y), ...apex);
      }
    });
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
      metalness: 0, flatShading: true, transparent: true, opacity: .92,
      side: THREE.FrontSide, depthWrite: false });
    material.userData.baseOpacity = .92;
    const rear = material.clone(); rear.side = THREE.BackSide; rear.opacity = .28; rear.userData.baseOpacity = .28;
    const back = new THREE.Mesh(geometry, rear); back.renderOrder = 3;
    const front = new THREE.Mesh(geometry, material); front.renderOrder = 4;
    group.add(back, front); materials.push(rear, material);
    const edges = new THREE.EdgesGeometry(geometry, 1); geometries.push(edges);
    const edgeMaterial = new THREE.LineBasicMaterial({ color: 0x354842, transparent: true, opacity: .38, depthWrite: false });
    edgeMaterial.userData.baseOpacity = .38; materials.push(edgeMaterial);
    const lines = new THREE.LineSegments(edges, edgeMaterial); lines.renderOrder = 5; group.add(lines);
  }
  group.userData.protrusions = protrusions;
  group.userData.indents = indents;
  return { group, materials, geometries };
}
