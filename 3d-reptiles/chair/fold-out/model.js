// Millimetres. A single outside-corner mechanism coupon, not a tested monotile.
export const dimensions = Object.freeze({
  side:40, radius:10, cavityRadius:10.3, rotorStart:12, rotorEnd:28,
  cavityStart:11.7, cavityEnd:28.3, pinRadius:1, bodyBore:1.1,
  rotorBore:1.2, rotorHubRadius:2.5, bodyHubRadius:3.5, hubLength:2,
  bearingLength:3, pinStart:-2, pinEnd:42, angularSegments:128
});
// Generate the boundary of occupied polar cells. Shared cells have no internal
// triangles. The two flat panel directions align exactly with angular grid lines.
function mesh(radial,ys,occupied,segments=dimensions.angularSegments) {
  const nr=radial.length-1,ny=ys.length-1,positions=[];
  const point=(a,r,y)=>{
    const theta=2*Math.PI*a/segments,rr=typeof radial[r]==='function'?radial[r](theta):radial[r];
    return [rr*Math.cos(theta),ys[y],rr*Math.sin(theta)].map(v=>Math.abs(v)<1e-10?0:v);
  };
  const isFilled=(a,r,y)=>r>=0&&r<nr&&y>=0&&y<ny&&occupied((a+segments)%segments,r,y);
  const faces=[[0,4,7,3],[1,2,6,5],[0,1,5,4],[3,7,6,2],[0,3,2,1],[4,5,6,7]];
  const offsets=[[-1,0,0],[1,0,0],[0,-1,0],[0,1,0],[0,0,-1],[0,0,1]];
  for(let a=0;a<segments;a++)for(let r=0;r<nr;r++)for(let y=0;y<ny;y++) {
    if(!isFilled(a,r,y))continue;
    const p=[point(a,r,y),point(a+1,r,y),point(a+1,r+1,y),point(a,r+1,y),
      point(a,r,y+1),point(a+1,r,y+1),point(a+1,r+1,y+1),point(a,r+1,y+1)];
    const center=[0,1,2].map(i=>p.reduce((s,q)=>s+q[i],0)/8);
    faces.forEach((face,j)=>{
      const d=offsets[j];if(isFilled(a+d[0],r+d[1],y+d[2]))return;
      const q=face.map(i=>p[i]),u=q[1].map((v,i)=>v-q[0][i]),v=q[2].map((v,i)=>v-q[0][i]);
      const n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
      if(n.reduce((s,v,i)=>s+v*(q[0][i]-center[i]),0)<0)q.reverse();
      positions.push(...q[0],...q[1],...q[2],...q[0],...q[2],...q[3]);
    });
  }
  return positions;
}
export function bodyMesh() {
  const d=dimensions,n=d.angularSegments;
  const ys=[0,d.bearingLength,d.cavityStart,d.cavityEnd,d.side-d.bearingLength,d.side];
  const outer=theta=>d.side/Math.max(Math.abs(Math.cos(theta)),Math.abs(Math.sin(theta)));
  return mesh([d.bodyBore,d.bodyHubRadius,d.cavityRadius,outer],ys,(a,r,y)=>{
    const corner=a>=n/2&&a<3*n/4;
    return corner?(y!==2||r===2):((y===0||y===4)&&r===0);
  });
}
export function rotorMesh() {
  const d=dimensions,n=d.angularSegments;
  return mesh([d.rotorBore,d.rotorHubRadius,d.radius],[d.rotorStart,d.rotorStart+d.hubLength,d.rotorEnd-d.hubLength,d.rotorEnd],
    (a,r,y)=>(a>=n/2&&a<3*n/4)||((y===0||y===2)&&r===0));
}
export function pinMesh() {
  // A polygonal cylinder with explicit caps, rather than a degenerate polar ring.
  const d=dimensions,p=[];const n=64;
  const q=(i,y)=>[d.pinRadius*Math.cos(i*2*Math.PI/n),y,d.pinRadius*Math.sin(i*2*Math.PI/n)];
  for(let i=0;i<n;i++){
    const a=q(i,d.pinStart),b=q(i+1,d.pinStart),c=q(i+1,d.pinEnd),e=q(i,d.pinEnd);
    p.push(...a,...c,...b,...a,...e,...c,0,d.pinStart,0,...a,...b,0,d.pinEnd,0,...c,...e);
  }return p;
}
export function foldPoint(p,angle) {
  // Positive angle sends the green-side removed volume into the red exterior.
  const c=Math.cos(angle),s=Math.sin(angle);
  return [c*p[0]-s*p[2],p[1],s*p[0]+c*p[2]];
}
