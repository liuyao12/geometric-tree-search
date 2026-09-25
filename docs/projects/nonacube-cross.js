import * as THREE from 'three';
import { OrbitControls } from '../../apps/3d-lattice-tiler/vendor/OrbitControls.js';

const $ = id => document.getElementById(id);
const publicBase = 'https://liuyao12.github.io/geometric-tree-search/';
const instructionURL = `${publicBase}data/nonacube-cross-certificate/VERIFY.md`;
const archiveHash = 'c1d36e7bad4d2f20194e83c6eb61c061ad81c0f0a009ee9ab7b26cf90b865fa4';
const aiPrompt = `Verify the nine-cube cross lattice result using ${instructionURL} . Download the linked self-contained certificate package and verify its SHA-256: ${archiveHash}. Inspect the documented geometric reduction and run python3 verify.py from the extracted polycube-certificates directory. Require successful DRAT-trim and cake_lpr checks, and report the local verification.json receipt. The precise claim is one complete face/edge/vertex corona but no second corona under integer translations and cubic rotations. Do not infer a result about arbitrary off-grid placements. A geometry-only audit or an archived success log is not a fresh UNSAT verification.`;

$('copy-ai').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(aiPrompt);
    $('copy-status').textContent = 'Copied. Paste into your AI to request an independent local verification.';
  } catch {
    $('copy-status').textContent = 'Copy this instruction:';
    let box = $('ai-prompt');
    if (!box) {
      box = document.createElement('textarea'); box.id = 'ai-prompt';
      box.setAttribute('aria-label', 'Instructions for an AI'); box.rows = 8;
      box.style.cssText = 'width:100%;font:12px monospace;padding:12px;margin-top:10px';
      $('copy-status').after(box);
    }
    box.value = aiPrompt; box.focus(); box.select();
  }
});

function fail(error) {
  $('error').textContent = `The 3D illustration could not load: ${error.message || error}. The downloadable certificate and verification instructions remain available.`;
  if ($('loading')) $('loading').textContent = '3D illustration unavailable on this device.';
}

async function main() {
  const response = await fetch(new URL('../../data/nonacube-cross-certificate/release.json', import.meta.url));
  if (!response.ok) throw new Error(`Witness request failed (${response.status})`);
  const data = await response.json();
  if (data.root.length !== 9 || data.corona.length !== 34) throw new Error('Unexpected witness inventory');
  const tiles = [data.root, ...data.corona];
  const occupied = new Set();
  for (const tile of tiles) for (const p of tile) {
    const key = p.join(',');
    if (occupied.has(key)) throw new Error('Witness contains overlapping voxels');
    occupied.add(key);
  }
  for (const p of data.root) for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) {
    if (!occupied.has([p[0] + x, p[1] + y, p[2] + z].join(','))) throw new Error('Witness does not surround the root');
  }

  const host = $('scene');
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0xffffff); renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.domElement.setAttribute('aria-hidden', 'true'); host.append(renderer.domElement);
  $('loading').remove();
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, .1, 500);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.minDistance = 3; controls.maxDistance = 90;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x759a87, 2.7));
  const light = new THREE.DirectionalLight(0xffffff, 2.2); light.position.set(8, -10, 18); scene.add(light);
  const light2 = new THREE.DirectionalLight(0xffffff, .9); light2.position.set(-10, 6, 5); scene.add(light2);
  const group = new THREE.Group(); scene.add(group);
  const colors = [0x4b9784, 0x76a8b1, 0x9caa6d, 0xba9b69, 0x829ab3, 0x71a58a, 0x95a5b1];
  const faces = [
    [[1,0,0], [[1,0,0],[1,1,0],[1,1,1],[1,0,1]]],
    [[-1,0,0], [[0,0,1],[0,1,1],[0,1,0],[0,0,0]]],
    [[0,1,0], [[0,1,1],[1,1,1],[1,1,0],[0,1,0]]],
    [[0,-1,0], [[0,0,0],[1,0,0],[1,0,1],[0,0,1]]],
    [[0,0,1], [[0,0,1],[1,0,1],[1,1,1],[0,1,1]]],
    [[0,0,-1], [[0,1,0],[1,1,0],[1,0,0],[0,0,0]]]
  ];
  function surface(tile) {
    const set = new Set(tile.map(p => p.join(','))), vertices = [];
    for (const p of tile) for (const [normal, face] of faces) {
      if (set.has(p.map((v, a) => v + normal[a]).join(','))) continue;
      for (const j of [0,1,2,0,2,3]) vertices.push(...p.map((v, a) => v + face[j][a]));
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.computeVertexNormals(); return geometry;
  }
  const objects = tiles.map((tile, index) => {
    const object = new THREE.Group(), geometry = surface(tile);
    const material = new THREE.MeshStandardMaterial({ color: index ? colors[(index * 3) % colors.length] : 0xe87935,
      roughness: .62, transparent: Boolean(index), opacity: index ? .29 : 1, depthWrite: !index });
    const mesh = new THREE.Mesh(geometry, material); mesh.userData.tile = index;
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 25),
      new THREE.LineBasicMaterial({ color: index ? 0x456253 : 0x934821, transparent: true, opacity: index ? .28 : .8 }));
    object.add(mesh, edges); group.add(object);
    const center = tile.reduce((c, p) => c.add(new THREE.Vector3(...p)), new THREE.Vector3()).divideScalar(9).addScalar(.5);
    return { object, mesh, edges, center, index };
  });
  const rootCenter = objects[0].center.clone();
  let selected = -1;
  function select(index) {
    selected = index;
    objects.forEach(item => {
      item.mesh.material.emissive.setHex(item.index === index ? 0x2e2813 : 0x000000);
      item.edges.material.opacity = item.index === index ? 1 : item.index ? .28 : .8;
    });
    $('selection').replaceChildren();
    const title = document.createElement('strong'), description = document.createElement('p');
    title.textContent = index === 0 ? 'Central nine-cube cross' : `Surrounding copy ${index}`;
    description.textContent = 'Exact voxel coordinates (JSON):';
    const coords = document.createElement('code'); coords.textContent = JSON.stringify(tiles[index]);
    $('selection').append(title, description, coords);
  }
  function frame() {
    group.updateWorldMatrix(true, true);
    const bounds = new THREE.Box3().setFromObject($('view').value === 'root' ? objects[0].object : group);
    const center = bounds.getCenter(new THREE.Vector3());
    const span = bounds.getSize(new THREE.Vector3()).length();
    controls.target.copy(center);
    camera.position.copy(center).add(new THREE.Vector3(1.15, -1.55, 1.15).normalize().multiplyScalar(span * 1.22));
    camera.up.set(0, 0, 1); controls.update();
  }
  function updateView() {
    const mode = $('view').value, solid = $('solid').checked;
    objects.forEach(item => {
      item.object.visible = mode !== 'root' || item.index === 0;
      item.object.position.set(0, 0, 0);
      if (mode === 'exploded' && item.index) item.object.position.copy(item.center).sub(rootCenter).multiplyScalar(.58);
      if (item.index) {
        item.mesh.material.opacity = solid ? 1 : mode === 'exploded' ? .7 : .29;
        item.mesh.material.transparent = !solid;
        item.mesh.material.depthWrite = solid;
        item.mesh.material.needsUpdate = true;
      }
    });
    $('view-note').textContent = mode === 'exploded'
      ? 'Exploded illustration: surrounding tiles are moved outward to reveal their shapes. Switch to Complete corona for the certified coordinates.'
      : mode === 'root'
        ? 'The prototype is a flat cross made of nine unit cubes. It has three distinct orientations under cubic rotations.'
        : solid ? 'The complete packing at its certified coordinates. Use transparency or the exploded illustration to see the central tile.'
          : 'Transparent colors reveal the central tile. Coordinates are the verified packing; the outer tiles need not be surrounded.';
    if (mode === 'root' && selected > 0) select(0);
    frame();
    window.nonacubeCertificateView = { mode, tiles: tiles.length, surroundingCopies: data.corona.length,
      rootVoxels: data.root.length, occupiedVoxels: occupied.size, heesch: data.heesch };
  }
  $('view').addEventListener('change', updateView);
  $('solid').addEventListener('change', updateView);
  $('reset').addEventListener('click', frame);
  let down = null;
  renderer.domElement.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
    const rect = renderer.domElement.getBoundingClientRect(), ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2(2 * (e.clientX - rect.left) / rect.width - 1,
      1 - 2 * (e.clientY - rect.top) / rect.height), camera);
    const intersections = ray.intersectObjects(objects.filter(item => item.object.visible).map(item => item.mesh));
    if (intersections.length) select(intersections[0].object.userData.tile);
  });
  new ResizeObserver(() => {
    renderer.setSize(host.clientWidth, host.clientHeight);
    camera.aspect = host.clientWidth / host.clientHeight; camera.updateProjectionMatrix();
  }).observe(host);
  updateView();
  function animate() { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }
  animate();
}
main().catch(fail);
