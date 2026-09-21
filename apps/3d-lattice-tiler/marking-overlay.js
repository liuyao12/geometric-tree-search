import * as THREE from 'three';
// One shared renderer for v1 and v2. Coordinates come from their actual sections.
export class MarkingOverlay {
  constructor({scene, camera, canvas, host, button, render = () => {}}) {
    Object.assign(this, {camera, canvas, host, button, render});
    this.group = new THREE.Group(); scene.add(this.group);
    this.rows = []; this.enabled = true; this.pointer = null;
    this.tooltip = document.createElement('div');
    this.tooltip.className = 'marking-tooltip'; this.tooltip.hidden = true;
    this.tooltip.style.cssText = 'position:absolute;z-index:5;pointer-events:none;background:#fffdf1;color:#294d43;border:1px solid #6a887b;border-radius:5px;padding:6px 9px;font:13px system-ui;white-space:pre-line;max-width:280px;';
    host.append(this.tooltip);
    button.onclick = () => {this.enabled = !this.enabled; this.sync(); render();};
    canvas.addEventListener('pointermove', e => {this.pointer = {x:e.clientX, y:e.clientY}; this.inspect();});
    canvas.addEventListener('pointerleave', () => {this.pointer = null; this.tooltip.hidden = true;});
    canvas.addEventListener('pointerdown', () => {this.pointer = null; this.tooltip.hidden = true;});
    this.sync();
  }
  sync() {
    this.group.visible = this.enabled;
    this.button.disabled = !this.rows.length;
    this.button.textContent = `Markings ${this.enabled ? 'on' : 'off'}`;
    this.button.setAttribute('aria-pressed', String(this.enabled));
    this.button.title = this.rows.length ? 'Hover over a colored point to inspect its learned value and overlapping assignments.' : 'No assigned marking values in this patch.';
    if (!this.enabled) this.tooltip.hidden = true;
  }
  set(rows = [], scale = 1) {
    this.rows = rows; this.scale = scale; this.tooltip.hidden = true;
    for (const child of [...this.group.children]) {this.group.remove(child); child.geometry.dispose(); child.material.dispose();}
    if (rows.length) {
      const positions = [], colors = [];
      for (const p of rows) {
        positions.push(...p.pos.map(x => x / scale));
        const c = new THREE.Color().setHSL(((p.value * 137.5) % 360 + 360) % 360 / 360, .65, .48);
        colors.push(c.r, c.g, c.b);
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
      const points = new THREE.Points(geometry, new THREE.PointsMaterial({size:8, sizeAttenuation:false, vertexColors:true, depthTest:false, transparent:true}));
      points.renderOrder = 10; this.group.add(points);
    }
    this.sync();
  }
  inspect() {
    this.tooltip.hidden = true;
    if (!this.pointer || !this.enabled || !this.rows.length) return;
    const bounds = this.canvas.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return;
    const mouse = {x:this.pointer.x-bounds.left, y:this.pointer.y-bounds.top};
    let hit = null, distance = 10, depth = Infinity;
    for (const row of this.rows) {
      const p = new THREE.Vector3(...row.pos.map(x => x / this.scale)).project(this.camera);
      if (p.z < -1 || p.z > 1) continue;
      const x=(p.x+1)*bounds.width/2, y=(1-p.y)*bounds.height/2, d=Math.hypot(x-mouse.x,y-mouse.y);
      if (d < distance-.1 || Math.abs(d-distance)<.1 && p.z<depth) {hit=row; distance=d; depth=p.z;}
    }
    if (!hit) return;
    const host = this.host.getBoundingClientRect();
    this.tooltip.textContent = `(${hit.pos.join(', ')}) · m[${hit.component ?? 0}] = ${hit.value}\n${hit.count} tile assignment${hit.count === 1 ? '' : 's'}${hit.count > 1 ? ' agree' : ''}`;
    this.tooltip.style.left = `${Math.max(0,Math.min(this.pointer.x-host.left+12,host.width-285))}px`;
    this.tooltip.style.top = `${Math.max(0,this.pointer.y-host.top-54)}px`;
    this.tooltip.hidden = false;
  }
}
