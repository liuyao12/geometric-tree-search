// Active coordinates: the central white material mark is the origin.
export const ORIGIN_TILE = 3546;
const root5 = Math.sqrt(5);
export const WHITE_PLANE_MATRIX = Object.freeze([
  Object.freeze([-2, -1-root5, 4, 0]),
  Object.freeze([2*root5, root5-3, 4, 8]),
]);
export function originFromMarks(marks) {
  const anchor = marks.anchors.find(a => a.tile === ORIGIN_TILE);
  if (!anchor) throw Error('The white-dot coordinate origin is missing.');
  return anchor.coordinates.slice();
}
const pairs = [];
for (let i=0;i<4;i++) for(let j=i+1;j<4;j++) {
  const a=WHITE_PLANE_MATRIX[0],b=WHITE_PLANE_MATRIX[1];
  pairs.push({i,j,det:a[i]*b[j]-a[j]*b[i]});
}
export function planeManhattanDistance(point) {
  const [a,b]=WHITE_PLANE_MATRIX;
  const u=a.reduce((s,v,k)=>s+v*point[k],0),v=b.reduce((s,w,k)=>s+w*point[k],0);
  // A minimum L1 correction with two constraints has support of size <= 2.
  let best=Infinity;
  for(const {i,j,det} of pairs) {
    if(Math.abs(det)<1e-12)continue;
    best=Math.min(best,Math.abs((u*b[j]-v*a[j])/det)+Math.abs((a[i]*v-b[i]*u)/det));
  }
  return best;
}
export const DISTANCE_STOPS = Object.freeze(['#234db0','#147e9a','#16875e','#b18712','#d86516','#b52b43']);
export function distanceColor(distance) {
  const t=Math.max(0,Math.min(5,distance)),i=Math.min(4,Math.floor(t)),f=t-i;
  const rgb=c=>[1,3,5].map(k=>parseInt(c.slice(k,k+2),16));
  const a=rgb(DISTANCE_STOPS[i]),b=rgb(DISTANCE_STOPS[i+1]);
  return `rgb(${a.map((v,k)=>Math.round(v+(b[k]-v)*f)).join(',')})`;
}
// One camera for the plane V = alpha U through the white-dot origin.
// mean is a screen-centering offset in the same translated Cartesian frame.
export function originPlaneFrame(c,s,mean=[0,0,0,0]) {
  const h=Math.sqrt(3)/2,ar=Math.sqrt(3)/4,ai=-root5/4;
  const nr=.5+h*ar,ni=h*ai,dr=c+s*ar,di=s*ai,den=dr*dr+di*di;
  const re=(nr*dr+ni*di)/den,im=(ni*dr-nr*di)/den;
  const br=-mean[2]+ar*mean[0]-ai*mean[1],bi=-mean[3]+ai*mean[0]+ar*mean[1];
  const kr=h-s*re,ki=-s*im;
  return {re,im,tx:br*kr-bi*ki,ty:bi*kr+br*ki,scale:Math.hypot(re,im),rms:0};
}
