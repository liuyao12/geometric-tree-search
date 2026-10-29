/** Exact symbolic Wang-cube data: Culik–Kari (1995), Figures 3–4 and Theorem 3.
 * Formula order is (left,front,back,right,top,bottom), following Figures 5–6.
 * Two printed occurrences of (0',1,1,1/2) in the cube construction disagree
 * with Figure 4. We use its existing (0',1,0',1/2) transition, and expose this
 * correction in the catalog; all 21 projections are independently checked.
 * Colors are symbols, including "0p" and "half", not rounded numbers.
 */
export const T13=[
 ['-2','1','2','-1'],['-2','1','1','0'],['-1','1','2','0'],['-1','0','1','-2'],['0','0','2','-2'],['0','0','1','-1'],
 ['0p','0p','0','0p'],['0p','2','1','0p'],['0p','1','0','half'],['0p','1','0p','half'],['half','0p','0','half'],['half','2','1','half'],['half','1','1','0p']
];
const removed=new Set([7,9,11,12]);
export const WANG21=[
 ...T13.filter((_,i)=>!removed.has(i)).map(([s,a,b,t],i)=>({id:`A${i+1}`,family:'A',colors:[[s,1],a,b,[t,1],[1,1],[1,1]]})),
 ...['0p','half'].flatMap((s,j)=>[0,1].flatMap(x=>[0,1].map(y=>({id:`B${j*4+x*2+y+1}`,family:'B',colors:[[s,x],'2','1',[s,y],[1,x],[1,x^y]]})))),
 ...[0,1].flatMap(x=>[{id:`C${x*2+1}`,family:'C',colors:[['half',1],'1','1',['0p',x],[0,1],[0,1]]},{id:`C${x*2+2}`,family:'C',colors:[['0p',1],'1','0p',['half',x],[0,1],[0,1]]}])
];
export const cubeProjection=c=>[c.colors[0][0],c.colors[1],c.colors[2],c.colors[3][0]];
export function wangFacesAgree(a,b,axis){const opposite=[[3,0],[4,5],[2,1]][axis];return JSON.stringify(a.colors[opposite[0]])===JSON.stringify(b.colors[opposite[1]]);}
