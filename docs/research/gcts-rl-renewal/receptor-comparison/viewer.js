/* Native saved-data presentation only. No scientific code or authority. */
'use strict';
const SVG='http://www.w3.org/2000/svg',XHTML='http://www.w3.org/1999/xhtml';
const lanes=['canonical','ordinary-symbolic-advice','extracted-finite-family-advice'];
const cases=['fresh-i2-CD-vw-direct','fresh-i2-CD-vw-incidence-transport'];
const colors={'canonical':'#65758a','ordinary-symbolic-advice':'#a97724','extracted-finite-family-advice':'#16887e'};
const byId=id=>document.getElementById(id);
const node=(tag,text,className)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;};
const math=(latex,tag='span',className)=>node(tag,`\\(${latex}\\)`,className);
const svg=(tag,attrs)=>{const n=document.createElementNS(SVG,tag);for(const [key,value] of Object.entries(attrs))n.setAttribute(key,String(value));return n;};
const requireDisplay=(yes,message)=>{if(!yes)throw Error(message);};
const pending=text=>node('p',text,'pending');
function number(value,unit=''){
  if(value===null||value===undefined)return node('span','Unavailable');
  requireDisplay(typeof value==='number'&&Number.isFinite(value)&&value>=0,'Invalid recorded nonnegative metric');
  return math(`${value}${unit?`\\,${unit}`:''}`);
}
function safeLink(href,label){
  requireDisplay(typeof href==='string','Evidence route must be a string');
  const url=new URL(href,location.href);
  requireDisplay(url.origin===location.origin&&['http:','https:'].includes(url.protocol),'Evidence route must stay on the report origin');
  const a=node('a',label);a.href=url.href;return a;
}
function validatePacket(packet){
  requireDisplay(packet.schema==='Notebook159-saved-display-packet-v1'&&packet.presentation_only===true,'Unexpected presentation packet');
  requireDisplay(typeof packet.lead==='string'&&typeof packet.status_text==='string','Missing display prose');
  for(const field of ['trials','prior_costs','evidence_links'])requireDisplay(Array.isArray(packet[field]),`Missing saved array ${field}`);
  requireDisplay(packet.trials.length<=6,'More than the preregistered six trial slots');
  const seen=new Set();
  for(const trial of packet.trials){
    requireDisplay(cases.includes(trial.case)&&lanes.includes(trial.lane),'Unpreregistered case or lane');
    const id=JSON.stringify([trial.case,trial.lane]);requireDisplay(!seen.has(id),'Duplicate presentation trial');seen.add(id);
    requireDisplay(typeof trial.status==='string'&&typeof trial.logical_accepted==='boolean'&&typeof trial.registry_completed==='boolean','Missing saved trial flags');
    requireDisplay(Array.isArray(trial.proof_rows),'Missing proof-row array; UNKNOWN needs an honest empty array');
    for(const row of trial.proof_rows){
      requireDisplay(Number.isInteger(row.physical_row)&&row.physical_row>=0&&row.physical_row<24,'Invalid displayed physical row');
      requireDisplay(Array.isArray(row.ordered_prior_rows)&&row.ordered_prior_rows.every(ref=>Number.isInteger(ref)&&ref>=0&&ref<row.physical_row),'Invalid saved ordered prior addresses');
      for(const field of ['formula_latex','formula_english','derivation_english'])requireDisplay(typeof row[field]==='string',`Missing saved ${field}`);
      for(const field of ['t','m'])requireDisplay(Array.isArray(row[field])&&row[field].every(p=>Array.isArray(p)&&p.length===3&&p.every(Number.isInteger)),`Invalid literal ${field} point data`);
      requireDisplay(row.t.length===1&&JSON.stringify(row.t[0])===JSON.stringify([0,row.physical_row,1]),'Display expects the actual unit point carrier');
      requireDisplay(row.m.some(p=>p[0]===1&&p[1]===row.physical_row),'Saved output formula mark is missing');
      row.ordered_prior_rows.forEach((ref,port)=>requireDisplay(
        row.m.some(p=>p[0]===2+port&&p[1]===row.physical_row&&p[2]===ref-row.physical_row)&&row.m.some(p=>p[0]===1&&p[1]===ref),
        'Saved ordered source address does not match its literal point markings'));
      requireDisplay(row.command&&typeof row.command==='object'&&!Array.isArray(row.command),'Missing exact primitive command');
    }
    requireDisplay(new Set(trial.proof_rows.map(row=>row.physical_row)).size===trial.proof_rows.length,'Repeated positive physical row in displayed patch');
  }
}
function table(headings,rows){
  const t=node('table'),head=node('thead'),tr=node('tr');
  for(const h of headings)tr.append(node('th',h));head.append(tr);t.append(head);
  const body=node('tbody');for(const cells of rows){const r=node('tr');for(const cell of cells){const d=node('td');d.append(cell);r.append(d);}body.append(r);}t.append(body);return t;
}
function trialLabel(trial){return `${trial.case} / ${trial.lane}`;}
function comparison(trials){
  if(!trials.length)return pending('Actual six-lane outcomes are pending attachment.');
  return table(['Case / lane','Saved status','Attempts / events','Inner search','Whole owned','Whole caller','Observed peak','Logical / registry','Evidence'],trials.map(t=>[
    node('code',trialLabel(t)),node('span',t.status),(()=>{const n=node('span');n.append(number(t.attempts),node('span',' / '),number(t.events));return n;})(),
    number(t.search_seconds,'\\mathrm{s}'),number(t.owned_seconds,'\\mathrm{s}'),number(t.caller_seconds,'\\mathrm{s}'),number(t.peak_MiB,'\\mathrm{MiB}'),
    node('span',`Saved logical flag: ${t.logical_accepted}; registry completed: ${t.registry_completed}`),
    t.evidence_href?safeLink(t.evidence_href,'Saved record'):node('span','Pending')
  ]));
}
function chart(trials){
  const measured=trials.filter(t=>typeof t.caller_seconds==='number'&&Number.isFinite(t.caller_seconds)&&t.caller_seconds>=0);
  if(!measured.length)return pending('Recorded whole caller times are pending.');
  const figure=node('figure',undefined,'cost-figure'),max=Math.max(1,...measured.map(t=>t.caller_seconds));
  for(const trial of trials){
    const row=node('div',undefined,'chart-row'),label=node('div',undefined,'chart-label'),swatch=node('span',undefined,'chart-swatch');
    swatch.style.background=colors[trial.lane];label.append(swatch,node('code',trialLabel(trial)));row.append(label);
    const picture=svg('svg',{viewBox:'0 0 500 30',role:'img','aria-label':'Recorded inclusive caller time, with no combined or stacked component clocks',class:'comparison-chart'});
    picture.append(svg('rect',{x:0,y:9,width:500,height:12,fill:'#edf0f3',rx:3}));
    if(typeof trial.caller_seconds==='number'&&Number.isFinite(trial.caller_seconds)&&trial.caller_seconds>=0)
      picture.append(svg('rect',{x:0,y:9,width:500*trial.caller_seconds/max,height:12,fill:colors[trial.lane],rx:3}));
    row.append(picture,number(trial.caller_seconds,'\\mathrm{s}'));figure.append(row);
  }
  const axis=node('div',undefined,'chart-axis');for(const v of [0,max/2,max])axis.append(number(v,'\\mathrm{s}'));figure.append(axis);
  figure.append(node('figcaption','Native SVG bars show recorded inclusive caller durations only. Bar length is a presentation scale, not a gain or statistical result.'));return figure;
}
function priorCosts(rows){
  if(!rows.length)return pending('Preparation, preserved failures and receiver-control costs are pending attachment.');
  const holder=node('div');
  holder.append(table(['Saved stage/version','Status / scope','Whole owned','Whole caller','Observed peak'],rows.map(row=>[
    node('span',row.label||'Saved prior stage'),node('span',[row.status,row.scope].filter(Boolean).join(' · ')),
    number(row.owned_seconds,'\\mathrm{s}'),number(row.caller_seconds,'\\mathrm{s}'),number(row.peak_MiB,'\\mathrm{MiB}')
  ])));
  for(const row of rows){if(row.note)holder.append(node('p',row.note,'muted'));if(row.evidence_href)holder.append(safeLink(row.evidence_href,`${row.label||'Prior stage'} evidence`));}
  return holder;
}
function tileDiagram(rows){
  const figure=node('figure',undefined,'tile-figure');
  const pointRows=rows.flatMap(r=>[r.physical_row,...r.ordered_prior_rows,...r.m.map(p=>p[1])]);
  const lo=Math.min(...pointRows),hi=Math.max(...pointRows);
  const y=row=>50+60*(row-lo),x=point=>120+60*point,height=y(hi)+50;
  const picture=svg('svg',{viewBox:`0 0 370 ${height}`,class:'tile-diagram',role:'img','aria-label':'Saved primitive unit point carriers, formula marks and ordered remote reads'});
  const occupied=new Set(rows.map(row=>row.physical_row));
  for(const row of rows)for(let port=0;port<row.ordered_prior_rows.length;port++){
    const ref=row.ordered_prior_rows[port],col=port===0?'#16887e':'#8861aa';
    picture.append(svg('path',{d:`M ${x(2+port)} ${y(row.physical_row)} V ${y(ref)} H ${x(1)}`,fill:'none',stroke:col,'stroke-width':2,'stroke-dasharray':occupied.has(ref)?'':'4 3'}));
  }
  for(const row of rows){
    picture.append(svg('rect',{x:x(0)-30,y:y(row.physical_row)-30,width:60,height:60,fill:'white',stroke:'#8c98a4','stroke-width':1.5}));
    picture.append(svg('circle',{cx:x(0),cy:y(row.physical_row),r:4,fill:'#364250'}));
    for(const [px,py,value] of row.m){
      const col=px===1?'#2472ac':px===2?'#16887e':'#8861aa';
      const dot=svg('circle',{cx:x(px),cy:y(py),r:4,fill:col});dot.append(svg('title',{}));dot.firstChild.textContent=`Literal assigned mark ${JSON.stringify([px,py,value])}`;picture.append(dot);
    }
    // The row address is typeset as LaTeX in an HTML foreignObject; SVG text
    // never substitutes a Unicode/plain mathematical formula.
    const label=svg('foreignObject',{x:0,y:y(row.physical_row)-18,width:77,height:40});
    const div=document.createElementNS(XHTML,'div');div.className='row-math';div.textContent=`\\(r=${row.physical_row}\\)`;label.append(div);picture.append(label);
  }
  figure.append(picture,node('figcaption','Literal saved point markings: blue formula values, teal first ordered offsets, purple later offsets. Dashes identify a referenced row absent from this displayed patch, not an established hypothesis. Carriers are vertically translated; acceptance is supplied separately.'));
  return figure;
}
function pointTable(row){
  const entries=[];for(const kind of ['t','m'])for(const [x,y,value] of row[kind])entries.push([node('code',kind),math(`(${x},${y})`),math(`${value}`)]);
  const t=table(['Channel','Literal point','Assigned value'],entries);t.className='point-table';return t;
}
function proofView(trial){
  const view=byId('proof-view');view.replaceChildren();
  const scope=byId('proof-scope');
  if(!trial){scope.textContent='No saved trial is attached.';view.append(pending('Proof rows remain pending.'));return;}
  scope.textContent=`${trial.proof_rows.length?'The same 19 commands as the earlier known proof, freshly timed and checked here. ':''}Saved status: ${trial.status}. Saved logical acceptance flag: ${trial.logical_accepted}. Origin: ${trial.origin_kind||'not supplied'}. Registry completed: ${trial.registry_completed}. These display fields issue no new acceptance.`;
  if(!trial.proof_rows.length){view.append(pending('No proof rows are attached for this saved trial. Its status and costs remain visible in the comparison table.'));return;}
  const rows=[...trial.proof_rows].sort((a,b)=>a.physical_row-b.physical_row),layout=node('div',undefined,'proof-layout'),cards=node('div');
  layout.append(tileDiagram(rows),cards);
  for(const row of rows){
    const card=node('article',undefined,'proof-line');card.id=`proof-physical-row-${row.physical_row}`;
    card.append(math(`r=${row.physical_row}`,'h3'),math(row.formula_latex,'div','formula'),node('p',row.formula_english),node('p',row.derivation_english));
    const refs=node('p',undefined,'muted');refs.append(node('span','Ordered prior rows: '));
    if(row.ordered_prior_rows.length)refs.append(math(`(${row.ordered_prior_rows.join(',')})`));else refs.append(node('span','none.'));card.append(refs);
    card.append(pointTable(row));const detail=node('details');detail.append(node('summary','Exact saved primitive command and points'));
    detail.append(node('pre',JSON.stringify({command:row.command,physical_row:row.physical_row,ordered_prior_rows:row.ordered_prior_rows,t:row.t,m:row.m},null,2)));card.append(detail);cards.append(card);
  }
  view.append(layout);
}
async function typeset(){
  if(window.MathJax?.startup?.promise){await MathJax.startup.promise;await MathJax.typesetPromise([document.querySelector('main')]);}
}
async function main(){
  const response=await fetch('summary.json');requireDisplay(response.ok,`Display packet HTTP ${response.status}`);
  const packet=await response.json();validatePacket(packet);
  byId('lead').textContent=packet.lead;byId('status').textContent=packet.status_text;
  byId('comparison-table').replaceChildren(comparison(packet.trials));byId('cost-chart').replaceChildren(chart(packet.trials));
  byId('prior-costs').replaceChildren(priorCosts(packet.prior_costs));
  if(typeof packet.arithmetic_status==='string')byId('arithmetic-status').textContent=packet.arithmetic_status;
  else if(packet.arithmetic_status!==null&&packet.arithmetic_status!==undefined)throw Error('Arithmetic status must be saved prose or null');
  const links=byId('evidence-links');links.replaceChildren();
  if(!packet.evidence_links.length)links.append(pending('Saved evidence routes are pending.'));
  else for(const row of packet.evidence_links){const p=node('p');p.append(safeLink(row.href,row.label));links.append(p);}
  const select=byId('trial');select.replaceChildren();select.disabled=!packet.trials.length;
  if(!packet.trials.length)select.append(node('option','No trials attached'));
  else packet.trials.forEach((trial,index)=>{const option=node('option',trialLabel(trial));option.value=String(index);select.append(option);});
  const winningIndex=packet.trials.findIndex(t=>t.logical_accepted&&t.proof_rows.length);
  const initialIndex=winningIndex>=0?winningIndex:0;
  if(packet.trials.length)select.value=String(initialIndex);
  proofView(packet.trials[initialIndex]||null);
  select.addEventListener('change',async()=>{if(window.MathJax?.typesetClear)MathJax.typesetClear([byId('proof-view')]);proofView(packet.trials[Number(select.value)]);await typeset();});
  await typeset();
}
main().catch(error=>{byId('status').textContent=`Display unavailable: ${error.message}. No scientific result or acceptance is inferred.`;});
