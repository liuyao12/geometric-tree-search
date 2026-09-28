import {circularArcs, drawCircularArcs} from '../../assets/penrose-circular-arcs.js?v=20260928-arcs';
const phi = (1 + Math.sqrt(5)) / 2;
for (const kind of ['kite', 'dart']) {
  const canvas = document.getElementById(`${kind}ArcExample`);
  if (!canvas) continue;
  const context = canvas.getContext('2d');
  const loop = [{x: 0, y: 0}, {x: phi * Math.cos(Math.PI/5), y: phi * Math.sin(Math.PI/5)},
    {x: kind === 'kite' ? phi : 1, y: 0}, {x: phi * Math.cos(Math.PI/5), y: -phi * Math.sin(Math.PI/5)}];
  function draw() {
    const width = canvas.clientWidth, height = canvas.clientHeight;
    if (!width || !height) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    context.clearRect(0, 0, width, height);
    const scale = Math.min((width - 40) / phi, (height - 30) / (2 * phi * Math.sin(Math.PI/5)));
    const project = p => ({x: width/2 + (p.x - phi/2) * scale, y: height/2 - p.y * scale});
    context.beginPath();
    loop.map(project).forEach((p, i) => i ? context.lineTo(p.x,p.y) : context.moveTo(p.x,p.y));
    context.closePath(); context.fillStyle = kind === 'kite' ? '#e8f1f5' : '#f8e9ee'; context.fill();
    context.strokeStyle = '#3f5653'; context.lineWidth = 1.4; context.stroke();
    drawCircularArcs(context, circularArcs(kind, loop), project, scale, 2.8);
  }
  new ResizeObserver(draw).observe(canvas);
  draw();
}
