const figure=document.querySelector('#dynamic-filling');
if(figure) init().catch(error=>{figure.querySelector('[data-df-matrix]').textContent=`Unable to load the result visualization: ${error.message}. The linked receipts remain available.`;});
async function init(){
 const response=await fetch(new URL('./results.json',import.meta.url));if(!response.ok)throw Error(`HTTP ${response.status}`);
 const data=await response.json();let selected=data.rows.find(r=>r.id==='oxalic-beta-0155')||data.rows.find(r=>r.verified),stage=2;
 const matrix=figure.querySelector('[data-df-matrix]');matrix.replaceChildren();
 for(const phase of ['alpha','beta']){
  const rows=data.rows.filter(r=>r.phase===phase),group=document.createElement('div');group.className='df-phase';
  const label=document.createElement('strong');label.textContent=`${phase==='alpha'?'α':'β'} · ${rows.filter(r=>r.verified).length}/${rows.length}`;
  const cells=document.createElement('div');cells.className='df-cells';
  for(const row of rows){const button=document.createElement('button');button.type='button';button.textContent=row.id.slice(-3);button.dataset.id=row.id;button.dataset.verified=String(row.verified);button.setAttribute('aria-label',`${row.id}: ${row.verified?'verified reconstruction':'no solution in this fixed-pose pool'}`);button.addEventListener('click',()=>{selected=row;stage=row.states.length-1;render();});cells.append(button);}
  group.append(label,cells);matrix.append(group);
 }
 for(const button of figure.querySelectorAll('[data-df-stage]'))button.addEventListener('click',()=>{stage=Number(button.dataset.dfStage);render();});
 function render(){
  for(const button of matrix.querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.id===selected.id));
  for(const button of figure.querySelectorAll('[data-df-stage]')){const index=Number(button.dataset.dfStage);button.disabled=index>=selected.states.length;button.setAttribute('aria-pressed',String(index===stage));}
  figure.querySelector('[data-df-title]').textContent=selected.id.replace('oxalic-','Oxalic acid · ');
  figure.querySelector('[data-df-case]').textContent=selected.verified?`${selected.candidates} candidate placements · ${selected.stats.forced} forced moves · ${selected.stats.branches} branch decisions · ${selected.stats.backtracks} backtracks. Independent geometric and filling checks passed.`:'No context survived the declared preprocessing for this fixed-pose domain. This does not prove that the configuration is geometrically impossible.';
  const values=selected.states[stage],roots=selected.atomRoots;let active=0,unused=0,full=0;
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');const height=Math.ceil(values.length/10)*42+24;svg.setAttribute('viewBox',`0 0 440 ${height}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',`Schematic t occupancy after ${stage} placements, not atomic coordinates`);
  values.forEach((value,i)=>{
   if(!roots[i]){if(value)active++;else unused++;}if(value===selected.capacity)full++;
   const x=30+(i%10)*42,y=25+Math.floor(i/10)*42;
   const circle=document.createElementNS(ns,'circle');circle.setAttribute('cx',x);circle.setAttribute('cy',y);circle.setAttribute('r','13');circle.setAttribute('fill',value?'#e6f3ec':'#fff');circle.setAttribute('stroke',roots[i]?'#506e64':'#a9b9b2');if(!roots[i])circle.setAttribute('stroke-dasharray','3 3');svg.append(circle);
   if(value){const arc=document.createElementNS(ns,'circle');for(const [k,v]of Object.entries({cx:x,cy:y,r:10,fill:'none',stroke:'#197f73','stroke-width':5,'stroke-dasharray':`${value/selected.capacity*62.832} 62.832`,transform:`rotate(-90 ${x} ${y})`}))arc.setAttribute(k,v);svg.append(arc);}
  });
  figure.querySelector('[data-df-points]').replaceChildren(svg);
  figure.querySelector('[data-df-state]').textContent=`${full} filled points · ${roots.filter(Boolean).length} atom roots · ${active} active latent points · ${unused} unused possible latent sites.`;
 }
 render();
}
