const $=s=>document.querySelector(s), NS='http://www.w3.org/2000/svg';
const colors=['#f8f3e8','#65b6a1','#e1b354','#7598c1','#d38783','#b299c8'];
const family={omino:'Polyomino',hex:'Polyhex',iamond:'Polyiamond'};
const math=s=>`\\(${s}\\)`;
function vertices([x,y,s],f){
 if(f==='omino')return [[x,y],[x+1,y],[x+1,y+1],[x,y+1]];
 if(f==='hex')return [[1,1],[-1,2],[-2,1],[-1,-1],[1,-2],[2,-1]].map(([a,b])=>[3*x+a,3*y+b]);
 return s===0?[[x,y],[x+1,y],[x,y+1]]:[[x+1,y],[x+1,y+1],[x,y+1]];
}
function draw(svg,layers,f,max){
 svg.replaceChildren();const coords=[];
 const xy=([x,y])=>f==='omino'?[x,-y]:[x+y/2,-y*Math.sqrt(3)/2];
 layers.forEach((tiles,j)=>{if(j>max)return;tiles.forEach(tile=>{
  const edges=new Map();let path='';
  tile.forEach(cell=>{const vs=vertices(cell,f);const pts=vs.map(xy);coords.push(...pts);path+=`M${pts.map(p=>p.join(',')).join('L')}Z`;
   vs.forEach((p,i)=>{const q=vs[(i+1)%vs.length],key=[p.join(','),q.join(',')].sort().join('|');if(edges.has(key))edges.delete(key);else edges.set(key,[xy(p),xy(q)]);});});
  const fill=document.createElementNS(NS,'path');fill.setAttribute('d',path);fill.setAttribute('fill',colors[j]);svg.append(fill);
  const outline=document.createElementNS(NS,'path');outline.setAttribute('d',[...edges.values()].map(([p,q])=>`M${p.join(',')}L${q.join(',')}`).join(''));outline.setAttribute('stroke','#233b45');outline.setAttribute('fill','none');outline.setAttribute('stroke-width','1.1');outline.setAttribute('vector-effect','non-scaling-stroke');svg.append(outline);
 });});
 const xs=coords.map(p=>p[0]),ys=coords.map(p=>p[1]);const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);const pad=Math.max(maxX-minX,maxY-minY)*.045+.15;
 svg.setAttribute('viewBox',`${minX-pad} ${minY-pad} ${maxX-minX+2*pad} ${maxY-minY+2*pad}`);
}
async function typeset(){if(window.MathJax?.startup){await window.MathJax.startup.promise;await window.MathJax.typesetPromise();}}
try{
 const response=await fetch('../../data/planar-heesch/report.json');if(!response.ok)throw new Error(`Results HTTP ${response.status}`);const data=await response.json();
 const options=[...data.records.filter(r=>r.witness),...data.examples.sort((a,b)=>b.Hh-a.Hh)];
 options.forEach((r,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`${family[r.family]} · ${r.size} cells · ${r.id}`;$('#shape').append(option);});
 function show(){const r=options[+$('#shape').value],w=r.witness.witness;$('#layer').max=w.layers.length-1;$('#layer').value=w.layers.length-1;
  $('#description').textContent=`${r.size} cells per tile. ${w.layers.slice(1).map(l=>l.length).join(', ')} tiles in successive coronas. ${w.holeFree?'This witness has no holes.':'This witness allows holes in the outer corona.'}`;
  $('#verdict').textContent=r.upper?math(`${w.holeFree?'H_c=H_h':'H_h'}=${r.upper.depth-1}`):r.Hh!==undefined&&!r.runs?math(`H_h=${r.Hh}`):math(`H_h\geq ${r.witness.depth}`);
  $('#evidence').replaceChildren();if(r.upper){const a=document.createElement('a');a.href='../../'+r.upper.path;a.textContent=`Depth ${r.upper.depth}: UNSAT, proof checked`;$('#evidence').append(a);}else $('#evidence').textContent=r.runs?'Upper bound unresolved in this run.':'Upper-bound proof checked in the census.';
  draw($('#prototype'),[w.layers[0]],r.family,0);redraw();typeset();
 }
 function redraw(){const r=options[+$('#shape').value],k=+$('#layer').value;$('#layer-value').textContent=k;draw($('#drawing'),r.witness.witness.layers,r.family,k);$('#legend').innerHTML=Array.from({length:k+1},(_,i)=>`<span><i class="dot" style="background:${colors[i]}"></i>${i===0?'Root':`Corona ${i}`}</span>`).join('');}
 $('#shape').addEventListener('change',show);$('#layer').addEventListener('input',redraw);$('#download').addEventListener('click',()=>{const r=options[+$('#shape').value],url=URL.createObjectURL(new Blob([JSON.stringify(r.witness,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=r.id+'-witness.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 $('#record-count').textContent=data.records.filter(r=>r.witness&&r.upper&&r.witness.depth===r.upper.depth-1&&r.witness.witness.holeFree).length+' / '+data.records.length;
 $('#enum-count').textContent=data.census.reduce((s,r)=>s+r.enumerated,0).toLocaleString();$('#finite-count').textContent=data.census.reduce((s,r)=>s+(r.classification.finite||0),0).toLocaleString();
 $('#records').innerHTML=data.records.map(r=>{const w=r.witness,u=r.upper,exact=w&&u&&w.depth===u.depth-1&&w.witness.holeFree;return `<tr><td><a href="${r.source}">${r.size}-cell ${family[r.family].toLowerCase()} · row ${r.sourceRow}</a></td><td>${math(`H_c=H_h=${r.Hh}`)}</td><td>${w?`${w.depth} coronas${w.witness.holeFree?', hole-free':''}`:'Budget cutoff'}</td><td>${u?`Depth ${u.depth}: proof checked`:'Unresolved'}</td><td class="${exact?'success':'unknown'}">${exact?'Reproduced':'Partial result'}</td></tr>`}).join('');
 $('#census').innerHTML=data.census.map(r=>`<tr><td>${family[r.family]} / ${r.size}</td><td>${r.enumerated} / ${r.processed}</td><td>${r.classification.periodic||0}</td><td>${r.classification.finite||0}</td><td>${r.classification.unknown||0}</td><td>${Object.entries(r.finiteHistogram).map(([h,n])=>math(`H_h=${h}`)+`: ${n}`).join('; ')}</td></tr>`).join('');
 $('#date').textContent='Run snapshot: '+data.date.slice(0,10)+'.';$('#shape').value=String(Math.max(0,options.findIndex(r=>r.id==='hex-11-19')));show();
}catch(error){$('#error').textContent='Unable to load results: '+error.message;console.error(error);}
