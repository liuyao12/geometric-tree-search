// Rendering only: this module consumes one-way approximate display geometry.
import * as THREE from 'three';
import { learnedDisplaySection } from './display-model.js?v=gcts-learning-v3';
import { OrbitControls } from '../3d-lattice-tiler/vendor/OrbitControls.js';

const AMBER = '#e4b269', TEAL = '#65bdb5';
const centerOf = vertices => vertices.reduce((s, p) => s.map((x, i) => x + p[i] / vertices.length), [0, 0, 0]);
const geometry = positions => {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  g.computeVertexNormals(); return g;
};
const dispose = group => { while (group.children.length) { const child = group.children[0]; group.remove(child); child.geometry?.dispose(); if (child.material) (Array.isArray(child.material) ? child.material : [child.material]).forEach(m => m.dispose()); } };

export class CrystalScene {
  constructor(canvas, onSelect) {
    this.canvas = canvas; this.onSelect = onSelect; this.mode = 'crystal';
    this.options = { separation: 0, cutaway: 0, prolate: true, oblate: true, edges: true, glass: false, fragments: false, pointSupport: false, learned: true };
    this.scene = new THREE.Scene();
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.camera = new THREE.PerspectiveCamera(32, 1, 0.1, 1500);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true; this.controls.dampingFactor = 0.075;
    this.controls.autoRotate = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.controls.autoRotateSpeed = 0.48; this.controls.enablePan = true;
    this.controls.minDistance = 2; this.controls.maxDistance = 500;
    this.scene.add(new THREE.HemisphereLight(0xd4eff2, 0x314047, 2.1));
    const key = new THREE.DirectionalLight(0xffe2b7, 3.5);
    key.position.set(12, 24, 15); key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048); key.shadow.camera.left = -45; key.shadow.camera.right = 45;
    key.shadow.camera.top = 45; key.shadow.camera.bottom = -45; key.shadow.camera.far = 150;
    key.shadow.bias = -0.0005; key.shadow.normalBias = 0.035; this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x85d8dd, 2.5); rim.position.set(-16, 8, -14); this.scene.add(rim);
    const fill = new THREE.DirectionalLight(0xd2e6ff, 0.9); fill.position.set(4, -2, 15); this.scene.add(fill);
    this.group = new THREE.Group(); this.scene.add(this.group);
    this.highlight = new THREE.Group(); this.scene.add(this.highlight);
    this.searchFocus = new THREE.Group(); this.scene.add(this.searchFocus);
    this.floor = new THREE.Mesh(new THREE.CircleGeometry(100, 96), new THREE.MeshStandardMaterial({ color: 0x14262c, roughness: 1, transparent: true, opacity: 0.45 }));
    this.floor.rotation.x = -Math.PI / 2; this.floor.receiveShadow = true; this.scene.add(this.floor);
    this.raycaster = new THREE.Raycaster();this.raycaster.params.Points.threshold=.18;
    canvas.addEventListener('pointermove',e=>{
      const tooltip=document.querySelector('#marking-tooltip');if(!tooltip)return;const box=canvas.getBoundingClientRect();this.raycaster.setFromCamera(new THREE.Vector2((e.clientX-box.left)/box.width*2-1,1-(e.clientY-box.top)/box.height*2),this.camera);const hit=this.raycaster.intersectObjects(this.group.children).find(h=>h.object.userData.markingPoints);tooltip.hidden=!hit;if(hit){const m=hit.object.userData.markingPoints[hit.index];tooltip.textContent=`Learned point: ${JSON.stringify(m.exact)} · ${Object.entries(m.options).map(([k,v])=>`${k} = ${v.join(' / ')}${v.length>1?' (conflict)':''}`).join(', ')} · ${m.refs} tile assignments`;}
    });canvas.addEventListener('pointerleave',()=>{const t=document.querySelector('#marking-tooltip');if(t)t.hidden=true;});
    let down;
    canvas.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
    canvas.addEventListener('pointerup', e => {
      if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
      const box = canvas.getBoundingClientRect();
      this.raycaster.setFromCamera(new THREE.Vector2((e.clientX - box.left) / box.width * 2 - 1, -(e.clientY - box.top) / box.height * 2 + 1), this.camera);
      const hit = this.raycaster.intersectObjects(this.group.children).find(h => h.object.userData.tiles);
      const tile = hit ? hit.object.userData.tiles[hit.faceIndex] : null;
      this.select(tile);
    });
    this.resizeObserver = new ResizeObserver(() => this.resize()); this.resizeObserver.observe(canvas.parentElement);
    this.resize();
    this.renderer.setAnimationLoop(() => {
      this.controls.update(); this.renderer.render(this.scene, this.camera);
      if (this.mode === 'tiles') for (const [kind, x] of [['prolate', -3.1], ['oblate', 3.1]]) {
        const p = new THREE.Vector3(x, -3.05, 0).project(this.camera);
        const label = document.querySelector(`.${kind}-label`);
        label.style.left = `${(p.x + 1) * this.canvas.clientWidth / 2}px`;
        label.style.top = `${(1 - p.y) * this.canvas.clientHeight / 2}px`;
        label.style.bottom = 'auto'; label.hidden = !this.options[kind];
      }
    });
    canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); document.querySelector('#status').textContent = 'The graphics context was interrupted. Reload the page to restore the view.'; });
  }
  resize() {
    const { width, height } = this.canvas.parentElement.getBoundingClientRect();
    this.renderer.setSize(width, height, false); this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix(); if (this.bounds) this.fit(this.preset ?? 'perspective');
  }
  setModel(model) { this.model = model; this.rebuild(true); }
  updateModel(model, first = false) {
    const oldRadius = this.bounds?.radius;
    this.model = model; this.rebuild(first);
    if (!first && oldRadius && this.bounds?.radius) {
      this.camera.position.sub(this.controls.target).multiplyScalar(this.bounds.radius / oldRadius).add(this.controls.target);
    }
  }
  setSearchFocus(points, dead = false) {
    dispose(this.searchFocus); if (this.mode !== 'search' || !points || !this.model) return;
    const phi = (1 + Math.sqrt(5)) / 2, c = centerOf(this.model.tiles.flatMap(t => t.vertices));
    const vertices = points.map(p => p.map(([a,b,d],i) => (Number(a)+Number(b)*phi)/Number(d)-c[i]));
    const g = new THREE.BufferGeometry(); g.setAttribute('position',new THREE.Float32BufferAttribute(vertices.flat(),3));
    this.searchFocus.add(new THREE.LineLoop(g,new THREE.LineBasicMaterial({color:dead?0xff6e65:0xfff4c7,depthTest:false,transparent:true,opacity:0.9})));
  }
  setMode(mode) { this.mode = mode; this.rebuild(true); }
  setOptions(options) { const refit = options.fragments !== undefined && options.fragments !== this.options.fragments; Object.assign(this.options, options); this.rebuild(refit); }
  fit(preset = 'perspective') {
    this.preset = preset;
    const directions = { perspective: [1.15, 0.8, 1.45], five: [0, 1, (1 + Math.sqrt(5)) / 2], three: [1, 1, 1], two: [0, 0, 1] };
    const d = new THREE.Vector3(...directions[preset]).normalize();
    const radius = this.bounds?.radius ?? 10;
    const angle = Math.atan(Math.tan(this.camera.fov * Math.PI / 360) * Math.min(1, this.camera.aspect));
    const distance = radius / Math.sin(angle) * 0.95;
    this.camera.position.copy(d.multiplyScalar(distance));
    this.controls.target.set(0, 0, 0); this.controls.update();
    this.camera.near = Math.max(0.02, distance / 1000); this.camera.far = Math.max(200, distance * 10); this.camera.updateProjectionMatrix();
  }
  select(tile) {
    dispose(this.highlight);
    if (tile) {
      const lines = []; const used = new Set();
      tile.faces.forEach(f => f.forEach((a, i) => { const b = f[(i + 1) % f.length], k = [a, b].sort().join(','); if (!used.has(k)) { used.add(k); lines.push(...tile.drawVertices[a], ...tile.drawVertices[b]); } }));
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(lines, 3));
      this.highlight.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xfff4c7, depthTest: false, transparent: true, opacity: 0.95 })));
    }
    this.onSelect(tile);
  }
  rebuild(refit) {
    if (!this.model) return;
    dispose(this.group); dispose(this.searchFocus); this.select(null);
    const opt = this.options;
    const tileMode = this.mode === 'tiles', windowMode = this.mode === 'window';
    let tiles = tileMode ? this.model.prototypes : opt.fragments ? this.model.tiles : this.model.connected.map(i => this.model.tiles[i]);
    const fullCenter = centerOf(tiles.flatMap(t => t.vertices));
    const limit = Math.max(...tiles.map(t => centerOf(t.vertices)[0] - fullCenter[0]));
    const min = Math.min(...tiles.map(t => centerOf(t.vertices)[0] - fullCenter[0]));
    tiles = tiles.filter(t => opt[t.kind] && (tileMode || centerOf(t.vertices)[0] - fullCenter[0] <= limit - (limit - min) * opt.cutaway / 100));
    const drawTiles = tiles.map((t, index) => {
      const c = centerOf(t.vertices);
      let vertices;
      if (tileMode) {
        const opposite = [0, 1, 2, 3].map(i => ({ d: new THREE.Vector3(...t.vertices[i ^ 7]).sub(new THREE.Vector3(...t.vertices[i])), i }));
        opposite.sort((a, b) => a.d.lengthSq() - b.d.lengthSq());
        const axis = (t.kind === 'prolate' ? opposite.at(-1) : opposite[0]).d.normalize();
        const q = new THREE.Quaternion().setFromUnitVectors(axis, new THREE.Vector3(0, 1, 0));
        const x = t.kind === 'prolate' ? -3.1 : 3.1;
        vertices = t.vertices.map(p => { const v = new THREE.Vector3(...p).sub(new THREE.Vector3(...c)).applyQuaternion(q); return [v.x + x, v.y, v.z]; });
        const base = Math.min(...vertices.map(p => p[1]));
        vertices = vertices.map(([x, y, z]) => [x, y - base - 2.5, z]);
      } else {
        vertices = t.vertices.map(p => p.map((x, i) => x - fullCenter[i] + (c[i] - fullCenter[i]) * opt.separation / 100));
      }
      return { ...t, drawVertices: vertices, displayIndex: index };
    });
    if (windowMode) {
      this.drawWindow();
    } else {
      const incidence = new Map();
      for (const t of drawTiles) for (const f of t.faces) { const key = f.map(i => t.keys[i]).sort().join('|'); incidence.set(key, (incidence.get(key) ?? 0) + 1); }
      const buckets = { prolate: { positions: [], tiles: [], colors: [] }, oblate: { positions: [], tiles: [], colors: [] } };
      const lines = [], edgeSet = new Set(), dotBuckets={black:[],red:[],rim:[],support:[]};
      for (const t of drawTiles) for (const f of t.faces) {
        const faceKey = f.map(i => t.keys[i]).sort().join('|');
        if (!tileMode && opt.separation === 0 && incidence.get(faceKey) > 1 && !opt.glass) continue;
        const bucket = buckets[t.kind];
        const color = new THREE.Color(t.kind === 'prolate' ? AMBER : TEAL);
        color.multiplyScalar(0.88 + (t.axes.reduce((a, b) => a + b, 0) % 7) * 0.025);
        for (const tri of [[f[0], f[1], f[2]], [f[0], f[2], f[3]]]) {
          bucket.positions.push(...tri.flatMap(i => t.drawVertices[i])); bucket.tiles.push(t);
          for (let i = 0; i < 3; i++) bucket.colors.push(color.r, color.g, color.b);
        }
        const dotSpec=t.dots?.find(d=>d.face===t.faces.indexOf(f));
        if(dotSpec){
          const center=f.reduce((s,i)=>s.add(new THREE.Vector3(...t.drawVertices[i])),new THREE.Vector3()).multiplyScalar(0.25);
          const u=new THREE.Vector3(...t.drawVertices[f[1]]).sub(new THREE.Vector3(...t.drawVertices[f[0]])).normalize();
          const n=u.clone().cross(new THREE.Vector3(...t.drawVertices[f[3]]).sub(new THREE.Vector3(...t.drawVertices[f[0]]))).normalize();
          const v=n.clone().cross(u).normalize();
          const circle=(out,p,r,lift)=>{
            const c=p.clone().addScaledVector(n,lift);
            for(let j=0;j<18;j++){
              const a=j/18*Math.PI*2,b=(j+1)/18*Math.PI*2;
              out.push(c.x,c.y,c.z,...c.clone().addScaledVector(u,Math.cos(a)*r).addScaledVector(v,Math.sin(a)*r).toArray(),...c.clone().addScaledVector(u,Math.cos(b)*r).addScaledVector(v,Math.sin(b)*r).toArray());
            }
          };
          for(const color of ['black','red']){
            const p=new THREE.Vector3(...t.drawVertices[dotSpec[color]]).multiplyScalar(0.75).addScaledVector(center,0.25);
            circle(dotBuckets.rim,p,0.095,0.011);circle(dotBuckets[color],p,0.075,0.015);
          }
          if(opt.pointSupport)circle(dotBuckets.support,center,0.036,0.018);
        }
        if (opt.edges) f.forEach((a, i) => {
          const b = f[(i + 1) % f.length];
          const key = (opt.separation || tileMode ? `${t.displayIndex}:` : '') + [t.keys[a], t.keys[b]].sort().join('|');
          if (!edgeSet.has(key)) { edgeSet.add(key); lines.push(...t.drawVertices[a], ...t.drawVertices[b]); }
        });
      }
      for (const bucket of Object.values(buckets)) {
        if (!bucket.positions.length) continue;
        const g = geometry(bucket.positions); g.setAttribute('color', new THREE.Float32BufferAttribute(bucket.colors, 3));
        const material = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: opt.glass ? 0.22 : 0.42, metalness: opt.glass ? 0.12 : 0.22,
          transparent: opt.glass, opacity: opt.glass ? 0.22 : 1, depthWrite: !opt.glass, side: opt.glass ? THREE.DoubleSide : THREE.FrontSide });
        const mesh = new THREE.Mesh(g, material); mesh.castShadow = !opt.glass; mesh.receiveShadow = true; mesh.userData.tiles = bucket.tiles;
        this.group.add(mesh);
      }
      for(const [key,positions]of Object.entries(dotBuckets))if(positions.length){
        const color={black:0x121c25,red:0xf45149,rim:0xffefdc,support:0xffffff}[key];
        const mesh=new THREE.Mesh(geometry(positions),new THREE.MeshBasicMaterial({color}));this.group.add(mesh);
      }
      if(opt.learned){
        const marks=learnedDisplaySection(drawTiles),positions=marks.flatMap(m=>m.point.map((v,i)=>v-fullCenter[i])),colors=marks.flatMap(m=>{const value=Object.values(m.components)[0]??0,col=m.conflict?new THREE.Color('#ff6b65'):new THREE.Color().setHSL((Number(value)*.61803398875)%1,.65,.67);return [col.r,col.g,col.b];});
        if(marks.length){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));const points=new THREE.Points(g,new THREE.PointsMaterial({vertexColors:true,size:.13,depthTest:false,transparent:true,opacity:.95}));points.renderOrder=3;points.userData.markingPoints=marks;this.group.add(points);}
      }
      if (lines.length) { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(lines, 3)); this.group.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: opt.glass ? 0xb0ded6 : 0x223a3d, transparent: true, opacity: opt.glass ? 0.32 : 0.56 }))); }
    }
    const box = new THREE.Box3().setFromObject(this.group);
    if (!box.isEmpty()) {
      const sphere = box.getBoundingSphere(new THREE.Sphere()); this.bounds = sphere;
      this.floor.position.y = box.min.y - 0.2; this.floor.visible = !windowMode; this.floor.scale.setScalar(Math.max(0.1, sphere.radius / 22));
      if (refit) this.fit('perspective');
    }
    document.querySelector('#visible-count').textContent = windowMode ? `30 golden faces · ${this.model.window.points.length.toLocaleString()} accepted vertices` : `${drawTiles.length.toLocaleString()} tiles in view${opt.cutaway ? ' · cutaway display' : ''}`;
    document.querySelector('#tile-labels').hidden = !tileMode;
    for (const kind of ['prolate', 'oblate']) document.querySelector(`#${kind}-count`).textContent = drawTiles.filter(t => t.kind === kind).length.toLocaleString();
  }
  drawWindow() {
    const { vertices, faces, points } = this.model.window, c = centerOf(vertices);
    const local = vertices.map(p => p.map((x, i) => x - c[i])), positions = [], lines = [], edges = new Set();
    for (const f of faces) {
      positions.push(...[f[0], f[1], f[2], f[0], f[2], f[3]].flatMap(i => local[i]));
      if (this.options.edges) f.forEach((a, i) => { const b = f[(i + 1) % 4], key = [a, b].sort().join(','); if (!edges.has(key)) { edges.add(key); lines.push(...local[a], ...local[b]); } });
    }
    this.group.add(new THREE.Mesh(geometry(positions), new THREE.MeshStandardMaterial({ color: 0x75c6bb, metalness: 0.15, roughness: 0.2, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false })));
    const edgeGeo = new THREE.BufferGeometry(); edgeGeo.setAttribute('position', new THREE.Float32BufferAttribute(lines, 3));
    this.group.add(new THREE.LineSegments(edgeGeo, new THREE.LineBasicMaterial({ color: 0xa4e7d2, transparent: true, opacity: 0.72 })));
    const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.Float32BufferAttribute(points.flatMap(p => p.map((x, i) => x - c[i])), 3));
    this.group.add(new THREE.Points(pg, new THREE.PointsMaterial({ color: 0xeec17c, size: 0.045, transparent: true, opacity: 0.8, sizeAttenuation: true })));
  }
  saveImage() {
    this.renderer.render(this.scene, this.camera);
    const image = document.createElement('canvas'); image.width = this.canvas.width; image.height = this.canvas.height;
    const ctx = image.getContext('2d'), w = image.width, h = image.height, s = this.renderer.getPixelRatio();
    const backdrop = ctx.createRadialGradient(w * 0.48, h * 0.43, 0, w * 0.48, h * 0.43, w * 0.75);
    backdrop.addColorStop(0, '#233c43'); backdrop.addColorStop(1, '#0c191f');
    ctx.fillStyle = backdrop; ctx.fillRect(0, 0, w, h); ctx.drawImage(this.canvas, 0, 0);
    ctx.fillStyle = '#dce6e8'; ctx.font = `${16 * s}px system-ui, sans-serif`;
    ctx.fillText(document.querySelector('#scene-title').textContent, 24 * s, 32 * s);
    ctx.fillStyle = '#8ca5aa'; ctx.font = `${10 * s}px system-ui, sans-serif`;
    ctx.fillText('GCTS · Exact algebraic geometry / display projection', 24 * s, h - 20 * s);
    const a = document.createElement('a'); a.download = `quasicrystal-${this.mode}.png`; a.href = image.toDataURL('image/png'); a.click();
  }
}
