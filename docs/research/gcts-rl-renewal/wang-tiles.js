'use strict';
/* The SVG is a drawing of the saved point values, never an extra constraint. */
function wangTileSvg(row,selected,isolated){
 const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const colors=['#28745c','#7452a3','#a76022','#246aa2','#a94461','#527b23'];
 const formulaValues=[...new Set(row.tiles.flatMap(t=>t.marks.filter(([p])=>p[1]===1).map(([,v])=>v)))].sort((a,b)=>a-b);
 const formulaColor=v=>colors[formulaValues.indexOf(v)%colors.length];
 const n=row.length,size=Math.min(155,860/n),left=(1040-n*size)/2,cy=250;
 const xy=p=>[left+size/2+p[0]*size/2,cy-p[1]*size/2];
 const body=(s,content='')=>`<g>${s}${content}</g>`,text=(x,y,s,cls='')=>`<text x="${x}" y="${y}" text-anchor="middle" class="${cls}">${safe(s)}</text>`;
 const active=row.tiles[selected],shown=isolated?[active]:row.tiles,owners=new Map();
 row.tiles.forEach((t,i)=>t.members.forEach(k=>owners.set(k[0],i)));
 let squares='',contacts='',ports='',titles='';
 for(let j=0;j<n;j++){
  const [x,y]=xy([2*j,0]),i=owners.get(j),t=row.tiles[i],visible=!isolated||i===selected,chosen=i===selected;
  squares+=`<rect x="${x-size/2}" y="${y-size/2}" width="${size}" height="${size}" fill="${visible?colors[i%colors.length]:'#eef0e9'}" fill-opacity="${visible?(chosen?'.20':'.08'):'1'}" stroke="${chosen?'#273e31':'#a1b2a4'}" stroke-width="${chosen?3:1}"/>`;
  if(visible)squares+=`<circle cx="${x}" cy="${y}" r="5" fill="${colors[i%colors.length]}"/>`+text(x,y+25,`Cell ${j+1}`)+text(x,y+43,`Tile ${i+1}`,'tile-small');
  else squares+=text(x,y+25,`Cell ${j+1}`,'tile-ghost');
 }
 const occupied=new Set(active.members.map(k=>k[0]));
 const origin=xy([2*active.members[0][0],0]);
 for(const [p,v] of active.marks){
  if(p[1]!==1||occupied.has(p[0]/2))continue;
  const q=xy(p),peak=Math.min(q[1]-60,origin[1]-size-65);
  contacts+=`<path class="remote-contact" d="M ${origin[0]} ${origin[1]-8} C ${origin[0]} ${peak}, ${q[0]} ${peak}, ${q[0]} ${q[1]}"/>`;
  titles+=text((origin[0]+q[0])/2,peak-4,'Distant premise contact','tile-small');
 }
 const groups=new Map();
 shown.forEach(t=>t.marks.forEach(([p,v])=>{const k=p.join(',');if(!groups.has(k))groups.set(k,{p,v,writers:[]});const g=groups.get(k);if(JSON.stringify(g.v)!==JSON.stringify(v))throw Error('Conflicting displayed point values');g.writers.push(row.tiles.indexOf(t));}));
 for(const {p,v,writers} of groups.values()){
  const [x,y]=xy(p),chosen=writers.includes(selected),remote=chosen&&p[1]===1&&!occupied.has(p[0]/2),stroke=remote?'#7452a3':chosen?'#273e31':'#7e9485';
  if(p[1]===1){
   ports+=`<circle cx="${x}" cy="${y}" r="${remote?17:13}" fill="#fcfdf7" stroke="${stroke}" stroke-width="${chosen?3:1.5}"/>`;
   ports+=`<circle cx="${x}" cy="${y}" r="6" fill="${formulaColor(v)}"/>`+text(x,y+31,`F${v}`,'tile-port-label');
   if(p[0]===2*(n-1))ports+=text(x,y-27,'Fixed target','tile-small');
   const label=`Formula port (${p.join(', ')}), value F${v}; written by tile ${writers.map(i=>i+1).join(', ')}`;
   ports+=`<title>${safe(label)}</title>`;
  }else if(p[1]===2){
   const i=writers[0];ports+=`<rect x="${x-10}" y="${y-10}" width="20" height="20" rx="2" fill="${colors[i%colors.length]}" fill-opacity=".2" stroke="${stroke}" stroke-width="${chosen?2.5:1}"/>`+text(x,y-18,`Owner ${v}`,'tile-small');
  }
 }
 const spans=active.members.map(k=>k[0]).sort((a,b)=>a-b);
 if(active.kind==='searched cluster'){
  const x=xy([2*spans[0],0])[0]-size/2,y=cy+size/2+17,w=(spans[spans.length-1]-spans[0]+1)*size;
  titles+=`<path d="M ${x} ${y-6} V ${y} H ${x+w} V ${y-6}" stroke="#273e31" stroke-width="2" fill="none"/>`+text(x+w/2,y+23,`One searched cluster · ${spans.length} cells`,'tile-small');
 }
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1040 400" role="img" aria-label="${safe(isolated?'Isolated selected tile with extended markings':'Assembled selected proof tiles with extended markings')}"><style>text{font:15px system-ui,sans-serif;fill:#273e31}.tile-small{font-size:12px}.tile-ghost{fill:#89928b}.tile-port-label{font-size:14px;font-weight:600}.remote-contact{fill:none;stroke:#7452a3;stroke-width:2.5;stroke-dasharray:7 5}</style>${body(squares)}${body(contacts)}${body(ports)}${body(titles)}</svg>`;
}
if(typeof module!=='undefined')module.exports={wangTileSvg};
