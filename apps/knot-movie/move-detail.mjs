export const descriptions = {
  'I−': {title:'Remove a curl',text:'Pull the highlighted loop straight. Its single crossing disappears.',change:'One crossing removed'},
  'I+': {title:'Make a curl',text:'Bend a strand into a small loop. This creates one crossing.',change:'One crossing added'},
  'II−': {title:'Pull two strands apart',text:'One strand passes over the other twice. Pull the pair apart to remove both crossings.',change:'Two crossings removed'},
  'II+': {title:'Bring two strands together',text:'Bring two strands together with the same strand on top at both crossings.',change:'Two crossings added'},
  III: {title:'Slide a strand past a crossing',text:'Slide one strand across the crossing of the other two. Keep the same strand on top at each encounter.',change:'Crossing count unchanged'},
};
const minus = {
  I: [[[15,110],[95,30],[65,15],[30,30],[25,65],[100,110],[145,110]]],
  II: [[[10,40],[40,40],[75,105],[110,40],[150,40]],[[10,85],[150,85]]],
  III: [[[10,30],[150,100]],[[10,100],[150,30]],[[70,10],[70,120]]],
};
const after = {
  I: [[[15,110],[145,110]]],
  II: [[[10,40],[150,40]],[[10,85],[150,85]]],
  III: [[[10,30],[150,100]],[[10,100],[150,30]],[[70,10],[100,40],[100,95],[70,120]]],
};
// These are standard local Reidemeister diagrams, separate from the actual
// full-knot panels. Endpoints and depth order remain fixed in each pair.
export function drawMoveDetail(canvas,kind) {
  const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height,type=kind.replace(/[+−]/g,''),reverse=kind.endsWith('+');
  ctx.clearRect(0,0,w,h);ctx.lineCap='round';ctx.lineJoin='round';
  const colors=['#ffc87b','#a7e7bd','#95caff'];
  const panels=reverse?[after[type],minus[type]]:[minus[type],after[type]];
  if(!panels[0])return;
  const scale=Math.min((w-120)/320,(h-45)/130),gap=80,origin=[(w-320*scale-gap)/2,35];
  panels.forEach((paths,panel)=>{
    const tx=origin[0]+panel*(160*scale+gap),ty=origin[1],point=p=>[tx+p[0]*scale,ty+p[1]*scale];
    const line=(points,color,width)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(...point(p)):ctx.moveTo(...point(p)));ctx.stroke();};
    paths.forEach((path,i)=>line(path,colors[i],5));
    const segments=paths.flatMap((path,strand)=>path.slice(1).map((b,k)=>({a:path[k],b,strand,k})));
    for(let i=0;i<segments.length;i++)for(let j=0;j<i;j++){
      const a=segments[i],b=segments[j];if(a.strand===b.strand&&Math.abs(a.k-b.k)<=1)continue;
      const r=[a.b[0]-a.a[0],a.b[1]-a.a[1]],s=[b.b[0]-b.a[0],b.b[1]-b.a[1]],q=[b.a[0]-a.a[0],b.a[1]-a.a[1]],det=r[0]*s[1]-r[1]*s[0];if(!det)continue;
      const t=(q[0]*s[1]-q[1]*s[0])/det,u=(q[0]*r[1]-q[1]*r[0])/det;if(t<=0||t>=1||u<=0||u>=1)continue;
      const p=[a.a[0]+t*r[0],a.a[1]+t*r[1]],over=a.strand<b.strand?a:b,d=[over.b[0]-over.a[0],over.b[1]-over.a[1]],len=Math.hypot(...d),v=d.map(x=>x*10/len);
      line([[p[0]-v[0],p[1]-v[1]],[p[0]+v[0],p[1]+v[1]]],'#102029',13);
      line([[p[0]-v[0],p[1]-v[1]],[p[0]+v[0],p[1]+v[1]]],colors[over.strand],5);
    }
    ctx.fillStyle='#a5b8bf';ctx.font='14px system-ui';ctx.textAlign='center';ctx.fillText(panel?'After':'Before',tx+80*scale,20);
  });
  const cx=w/2,cy=origin[1]+65*scale;ctx.strokeStyle='#eee9df';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(cx-18,cy);ctx.lineTo(cx+18,cy);ctx.lineTo(cx+10,cy-7);ctx.moveTo(cx+18,cy);ctx.lineTo(cx+10,cy+7);ctx.stroke();
}
