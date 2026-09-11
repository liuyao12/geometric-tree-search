import {fitConnectionLibrary,connectionScore,twistConnection} from '../connection-descriptor.mjs';
const $=id=>document.getElementById(id);
try {
  const response=await fetch('connection-results.json');if(!response.ok)throw Error('Data unavailable');
  const report=await response.json();
  const pct=(a,b)=>b?`${(100*a/b).toFixed(1)}%`:'not estimable';
  const total=(rows,k)=>rows.reduce((n,r)=>n+r[k],0);
  let libraries,fixture;
  function render(){
    const domain=$('connection-domain').value,fraction=+$('connection-size').value,strict=$('connection-threshold').value==='strict';
    const rows=report.analyses.filter(r=>r.domain===domain&&r.fraction===fraction);
    const box=$('connection-comparison');box.replaceChildren();
    for(const row of rows){
      const s=strict?row.strictSummary:row.summary,card=document.createElement('div');card.className='connection-card';
      const title=document.createElement('h4');title.textContent=row.crossChannels?'Motifs + connection channels':'Individual-motif channels';card.append(title);
      for(const [label,n,d] of [['Held-out observed connections retained',total(s,'retained'),total(s,'known')],['Twists rejected, conditional on original retained',total(s,'conditionalRejected'),total(s,'conditionalTwists')]]){
        const p=document.createElement('p');p.textContent=`${label}: ${pct(n,d)} (${n}/${d})`;card.append(p);
        const bar=document.createElement('div');bar.className='connection-meter';const fill=document.createElement('span');fill.style.width=`${d?100*n/d:0}%`;bar.append(fill);card.append(bar);
      }
      const p=document.createElement('p');p.className='fine';p.textContent=`${row.trainingExamples} training connections · ${total(s,'unknown')} test connections in unknown strata (abstentions) · descriptor tolerance ${(strict?.06:row.threshold).toFixed(3)} Å`;card.append(p);box.append(card);
    }
    fixture=report.illustrations[domain];
    // Illustration is always the first test connection; the corpus-size control
    // affects the results above, not this deliberately fixed full-library example.
    libraries=[false,true].map(c=>fitConnectionLibrary(fixture.training.map(sites=>({sites})),c));
    const rowsAll=report.analyses.filter(r=>r.domain===domain&&r.crossChannels);
    $('connection-curve').innerHTML=`<svg viewBox="0 0 600 185" role="img" aria-label="Connection transfer across four training sizes"><path d="M45 15V145H565" fill="none" stroke="#809394"/>${[0,50,100].map(v=>`<text x="8" y="${150-v*1.2}" font-size="13">${v}%</text>`).join('')}${['retained','conditionalRejected'].map((key,ki)=>{
      const points=rowsAll.flatMap((r,i)=>{const s=strict?r.strictSummary:r.summary,d=total(s,key==='retained'?'known':'conditionalTwists');return d?[[65+i*155,145-120*total(s,key)/d]]:[];});
      return `<polyline points="${points.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${ki?'#a64635':'#176d70'}" stroke-width="3"/>${points.map(p=>`<circle cx="${p[0]}" cy="${p[1]}" r="4" fill="${ki?'#a64635':'#176d70'}"/>`).join('')}`;
    }).join('')}${rowsAll.map((r,i)=>`<text x="${65+i*155}" y="170" text-anchor="middle" font-size="13">${r.trainingExamples}</text>`).join('')}</svg>`;
    draw();
  }
  function draw(){
    const angle=+$('connection-angle').value,sites=twistConnection(fixture.sites,angle*Math.PI/180);
    $('connection-degrees').textContent=`${angle}°`;
    const canvas=$('connection-canvas'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,640,300);ctx.fillStyle='#102d35';ctx.fillRect(0,0,640,300);
    const project=p=>[320+40*(.85*p[0]+.52*p[2]),150+40*(-.25*p[0]+.91*p[1]+.4*p[2])];
    const centre=[0,1,2].map(k=>sites.reduce((n,s)=>n+s.position[k],0)/sites.length);
    const pts=sites.map(s=>project(s.position.map((x,k)=>x-centre[k])));
    for(const [indices,color] of [[[0,1,2,3],'#5bd9d1'],[[0,1,4,5],'#f6ad85']]){
      ctx.strokeStyle=color;ctx.globalAlpha=.55;
      for(let i=0;i<indices.length;i++)for(let j=0;j<i;j++){ctx.beginPath();ctx.moveTo(...pts[indices[i]]);ctx.lineTo(...pts[indices[j]]);ctx.stroke();}
    }
    ctx.globalAlpha=1;
    sites.forEach((s,i)=>{ctx.fillStyle=i<2?'#fff':s.role==='A'?'#5bd9d1':'#f6ad85';ctx.beginPath();ctx.arc(...pts[i],7,0,2*Math.PI);ctx.fill();ctx.font='14px sans-serif';ctx.fillText(s.species,pts[i][0]+10,pts[i][1]-8);});
    const fullRows=report.analyses.filter(r=>r.domain===$('connection-domain').value&&r.fraction===1);
    $('connection-live').textContent=libraries.map((library,i)=>{
      const score=connectionScore(library,sites),threshold=$('connection-threshold').value==='strict'?.06:fullRows[i].threshold;
      return `${i?'Connection':'Individual motifs'}: ${Number.isFinite(score)?score.toFixed(3)+' Å · '+(score<=threshold?'admitted':'restricted'):'unknown / abstain'}`;
    }).join('   |   ');
  }
  for(const id of ['connection-domain','connection-size','connection-threshold'])$(id).addEventListener('change',render);
  $('connection-angle').addEventListener('input',draw);render();
}catch(error){$('connection-comparison').textContent='Interactive data could not be loaded. The static table and downloadable records below remain available.';}
