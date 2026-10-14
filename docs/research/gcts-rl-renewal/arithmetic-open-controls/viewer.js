/* Saved-data presentation only: no compiler, graph, checker, search or learner. */
'use strict';
const SVG='http://www.w3.org/2000/svg',XHTML='http://www.w3.org/1999/xhtml';
const byId=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const math=(latex,tag='span',cls)=>el(tag,`\\(${latex}\\)`,cls);
const pending=text=>el('p',text,'pending');
const requireDisplay=(ok,message)=>{if(!ok)throw Error(message);};
const sv=(tag,attrs)=>{const n=document.createElementNS(SVG,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));return n;};
function countText(value){
  if(typeof value==='number'){requireDisplay(Number.isSafeInteger(value)&&value>=0,'Count must be an exact nonnegative integer');return String(value);}
  requireDisplay(typeof value==='string'&&/^(0|[1-9][0-9]*)$/.test(value),'Large count requires an exact decimal string');return value;
}
function metric(value,unit){
  if(value===null||value===undefined)return el('span','Pending');
  requireDisplay(typeof value==='number'&&Number.isFinite(value)&&value>=0,'Saved clock must be finite and nonnegative');
  return math(`${value}\\,${unit}`);
}
function flag(value){requireDisplay(value===null||typeof value==='boolean','Saved acceptance flag must be explicit');return el('span',value===null?'Pending':String(value));}
function rawPin(pin){
  requireDisplay(pin&&typeof pin==='object'&&typeof pin.path==='string'&&/^[0-9a-f]{64}$/.test(pin.sha256)&&Number.isSafeInteger(pin.bytes)&&pin.bytes>=0,'Missing exact attached raw record pin');
}
function safeLink(href,label){
  requireDisplay(typeof href==='string'&&!href.startsWith('/Users/')&&!href.startsWith('/private/'),'Evidence needs a public report route, not a filesystem path');
  const url=new URL(href,location.href);
  requireDisplay(url.origin===location.origin&&['http:','https:'].includes(url.protocol),'Evidence stays on the same HTTP(S) report origin');
  const a=el('a',label);a.href=url.href;return a;
}
function validate(packet){
  requireDisplay(packet.schema==='Q-streamed-controls-saved-display-packet-v1'&&packet.presentation_only===true,'Unexpected presentation packet');
  requireDisplay(['pending','attached'].includes(packet.attachment_status),'Explicit attachment state required');
  for(const k of ['lead','status_text'])requireDisplay(typeof packet[k]==='string',`Missing ${k}`);
  for(const k of ['attempts','initial_domains','control_records','evidence_links'])requireDisplay(Array.isArray(packet[k]),`Missing saved array ${k}`);
  if(packet.attachment_status==='pending'){
    requireDisplay(packet.ROOT_presentation_pin===null&&packet.attempts.length===0&&packet.initial_domains.length===0&&packet.control_records.length===0&&packet.reported_control_count===null&&packet.initial_domains_complete===null&&packet.complete_control_records_attached===null&&packet.unary_probe===null&&packet.evidence_links.length===0,'Pending scaffold cannot contain invented results');return;
  }
  rawPin(packet.ROOT_presentation_pin);
  for(const a of packet.attempts){
    requireDisplay(typeof a.label==='string'&&typeof a.status==='string'&&typeof a.scope==='string','Saved attempts require status and scope');
    for(const k of ['stage_completed','ROOT_scoped_controls_accepted','resource_accepted'])requireDisplay(a[k]===null||typeof a[k]==='boolean',`Explicit ${k} required`);
    for(const k of ['inner_seconds','owned_postwrite_seconds','caller_observed_seconds','caller_finish_margin_seconds'])if(a[k]!==null)requireDisplay(typeof a[k]==='number'&&Number.isFinite(a[k])&&a[k]>=0,`Invalid ${k}`);
    if(a.peak_bytes!==null)countText(a.peak_bytes);
    rawPin(a.record_pin);
  }
  requireDisplay(packet.initial_domains_complete===null||typeof packet.initial_domains_complete==='boolean','Explicit domain scope required');
  if(packet.initial_domains_complete===true)requireDisplay(packet.initial_domains.length===24,'Complete scope requires all24 saved counts');
  if(packet.initial_domains.length){
    requireDisplay(packet.initial_domains.length===24,'Display needs the whole attached initial24 census, never a prefix');
    const seen=new Set();for(const d of packet.initial_domains){requireDisplay(Number.isInteger(d.row)&&d.row>=0&&d.row<24&&!seen.has(d.row),'Exact unique row census required');seen.add(d.row);countText(d.count);}
  }
  requireDisplay(packet.complete_control_records_attached===null||typeof packet.complete_control_records_attached==='boolean','Explicit control-record completeness required');
  if(packet.reported_control_count!==null){requireDisplay(Number.isSafeInteger(packet.reported_control_count)&&packet.reported_control_count>=0,'Control count must be exact');}
  if(packet.complete_control_records_attached===true)requireDisplay(packet.reported_control_count===packet.control_records.length,'Every reported control must be attached');
  for(let i=0;i<packet.control_records.length;i++){
    const c=packet.control_records[i];requireDisplay(c.index===i&&typeof c.label==='string'&&typeof c.saved_outcome==='string'&&typeof c.scope==='string'&&Object.prototype.hasOwnProperty.call(c,'record'),'Preserve complete chronological control records and explicit scope');
  }
  if(packet.unary_probe!==null)validateProbe(packet.unary_probe);
}
function validateProbe(probe){
  requireDisplay(probe.probe_kind==='actual_unary_footprint_not_proof'&&probe.source_fact_or_selected_claimed===false,'Unary diagram is only an actual footprint probe');rawPin(probe.actual_controls_record_pin);
  const r=probe.unary_placement;
  requireDisplay(r&&typeof r==='object'&&typeof r.id==='string'&&r.identity_preimage&&Array.isArray(r.key)&&r.key.length===3,'Attach the whole decorated unary record');
  const [recipe,row,refs]=r.key;requireDisplay(Number.isSafeInteger(recipe)&&recipe>=0&&Number.isInteger(row)&&row>=0&&row<24&&Array.isArray(refs)&&refs.length===1&&Number.isInteger(refs[0])&&refs[0]>=0&&refs[0]<row,'Exact actual unary key required');
  requireDisplay(r.command&&r.command.rule==='generalize'&&r.command.source===refs[0]&&Array.isArray(r.command.formula),'Preserve the actual unary primitive command');
  for(const k of ['t','m'])requireDisplay(Array.isArray(r[k])&&r[k].every(p=>Array.isArray(p)&&p.length===3&&p.every(Number.isSafeInteger)),`Invalid exact literal ${k} points`);
  requireDisplay(JSON.stringify(r.t)===JSON.stringify([[0,row,1]]),'Unary footprint must carry the saved unit support');
  requireDisplay(r.m.length===3&&r.m.filter(p=>p[0]===1&&p[1]===row).length===1&&r.m.filter(p=>p[0]===1&&p[1]===refs[0]).length===1&&r.m.some(p=>p[0]===2&&p[1]===row&&p[2]===refs[0]-row)&&!r.m.some(p=>p[0]===3),'One source formula and one offset; second port is absent');
  requireDisplay(probe.output_formula_latex===null||typeof probe.output_formula_latex==='string','Formula translation must be an explicit saved display field');
  // These are display-shape checks only. No licence, logic or point authority.
}
function table(headings,rows){
  const t=el('table'),head=el('thead'),tr=el('tr');for(const h of headings)tr.append(el('th',h));head.append(tr);t.append(head);
  const body=el('tbody');for(const cells of rows){const r=el('tr');for(const c of cells){const td=el('td');td.append(c);r.append(td);}body.append(r);}t.append(body);return t;
}
function details(label,record){const d=el('details');d.append(el('summary',label),el('pre',JSON.stringify(record,null,2)));return d;}
function renderAttempts(rows){
  if(!rows.length)return pending('No prior failure or successor result is attached.');
  const holder=el('div');holder.append(table(['Saved stage/version','Status / scope','Inner','Owned/postwrite','Observed caller','Finish reserve','Observed peak','Recorded flags'],rows.map(a=>[
    el('span',a.label),el('span',`${a.status} · ${a.scope}`),metric(a.inner_seconds,'\\mathrm{s}'),metric(a.owned_postwrite_seconds,'\\mathrm{s}'),metric(a.caller_observed_seconds,'\\mathrm{s}'),metric(a.caller_finish_margin_seconds,'\\mathrm{s}'),a.peak_bytes===null?el('span','Pending'):math(`${countText(a.peak_bytes)}\\,\\mathrm{B}`),
    el('span',`Stage completed: ${a.stage_completed===null?'Pending':a.stage_completed}; ROOT scoped controls: ${a.ROOT_scoped_controls_accepted===null?'Pending':a.ROOT_scoped_controls_accepted}; resource accepted: ${a.resource_accepted===null?'Pending':a.resource_accepted}`)
  ])));
  for(const a of rows){if(a.evidence_href)holder.append(safeLink(a.evidence_href,`${a.label} raw record`));holder.append(details(`${a.label}: exact presentation record`,a));}return holder;
}
function renderDomains(packet){
  byId('domain-scope').textContent=`Saved initial-domain completeness flag: ${packet.initial_domains_complete===null?'Pending':packet.initial_domains_complete}. This display does not re-enumerate or qualify a domain.`;
  const view=byId('domain-table');view.replaceChildren();if(!packet.initial_domains.length){view.append(pending('No initial row counts are attached.'));return;}
  view.append(table(['Row','Complete parametric candidate count','Saved descriptor'],[...packet.initial_domains].sort((a,b)=>a.row-b.row).map(d=>[math(`${d.row}`),math(countText(d.count)),d.raw_href?safeLink(d.raw_href,'Raw full descriptor'):el('span','Raw link pending')])));
  if(packet.initial_domains_raw_href)view.append(safeLink(packet.initial_domains_raw_href,'Whole initial domain census'));
}
function renderControls(packet){
  const scope=byId('control-scope');scope.replaceChildren();scope.append(el('span',packet.control_scope_text||'No complete controls scope is attached.'));
  if(packet.reported_control_count!==null)scope.append(el('span',' Saved reported record count: '),math(countText(packet.reported_control_count)),el('span',`. Complete records attached: ${packet.complete_control_records_attached}. These fields do not imply theorem acceptance.`));
  const view=byId('control-records');view.replaceChildren();if(!packet.control_records.length){view.append(pending('No control records are attached.'));return;}
  for(const c of packet.control_records){const card=el('article',undefined,'control-record');card.append(math(`${c.index+1}`,'h3'),el('p',c.label),el('p',`Saved outcome: ${c.saved_outcome}. Scope: ${c.scope}.`),details('Whole attached saved control record',c.record));if(c.raw_href)card.append(safeLink(c.raw_href,'Raw witness/evidence'));view.append(card);}
}
function renderProbe(probe){
  const view=byId('unary-view');view.replaceChildren();if(probe===null){view.append(pending('No actual unary placement is attached; no tile or formula is invented.'));return;}
  const r=probe.unary_placement,row=r.key[1],ref=r.key[2][0],lo=Math.min(row,ref),hi=Math.max(row,ref),x=n=>105+55*n,y=n=>50+55*(n-lo);
  const layout=el('div',undefined,'footprint-layout'),figure=el('figure',undefined,'footprint-figure'),cards=el('div');
  const s=sv('svg',{viewBox:`0 0 310 ${y(hi)+45}`,class:'footprint-svg',role:'img','aria-label':'Actual unary point-footprint probe only; no proof or selected antecedent'});
  s.append(sv('path',{d:`M ${x(2)} ${y(row)} V ${y(ref)} H ${x(1)}`,fill:'none',stroke:'#16887e','stroke-width':2,'stroke-dasharray':'4 3'}));
  s.append(sv('rect',{x:x(0)-27.5,y:y(row)-27.5,width:55,height:55,fill:'white',stroke:'#8c98a4','stroke-width':1.5}),sv('circle',{cx:x(0),cy:y(row),r:4,fill:'#364250'}));
  for(const [px,py,value]of r.m){const dot=sv('circle',{cx:x(px),cy:y(py),r:4,fill:px===1?'#2472ac':'#16887e'});const title=sv('title',{});title.textContent=`Literal assigned m ${JSON.stringify([px,py,value])}`;dot.append(title);s.append(dot);}
  for(const address of [ref,row]){const f=sv('foreignObject',{x:0,y:y(address)-14,width:70,height:36}),div=document.createElementNS(XHTML,'div');div.className='row-math';div.textContent=`\\(r=${address}\\)`;f.append(div);s.append(f);}
  figure.append(s,el('figcaption','One translated carrier and its saved remote source marks. Dashed read is an address, not a proved or selected fact. No second port is drawn.'));
  cards.append(el('p','Actual controls footprint probe only. No target proof, source fact or selected ancestry is claimed.'));
  if(probe.output_formula_latex!==null)cards.append(el('p','Recorded output formula, without proof authority:'),math(probe.output_formula_latex,'div','formula'));
  const points=[];for(const channel of ['t','m'])for(const [px,py,value]of r[channel])points.push([el('code',channel),math(`(${px},${py})`),math(`${value}`)]);
  cards.append(table(['Channel','Literal point','Assigned value'],points),details('Whole unchanged decorated unary placement',r),details('Actual controls record raw pin',probe.actual_controls_record_pin));
  if(probe.raw_href)cards.append(safeLink(probe.raw_href,'Raw unary placement/control record'));layout.append(figure,cards);view.append(layout);
}
async function main(){
  const response=await fetch('summary.json');requireDisplay(response.ok,`Saved packet HTTP ${response.status}`);const packet=await response.json();validate(packet);
  byId('lead').textContent=packet.lead;byId('status').textContent=packet.status_text;
  byId('attempt-table').replaceChildren(renderAttempts(packet.attempts));renderDomains(packet);renderControls(packet);renderProbe(packet.unary_probe);
  const links=byId('evidence-links');links.replaceChildren();if(!packet.evidence_links.length)links.append(pending('No raw outcome, witness or review links are attached.'));
  else for(const item of packet.evidence_links){requireDisplay(typeof item.label==='string','Saved evidence label required');const p=el('p');p.append(safeLink(item.href,item.label));links.append(p);}
  if(window.MathJax?.startup?.promise){await MathJax.startup.promise;await MathJax.typesetPromise([document.querySelector('main')]);}
}
main().catch(error=>{byId('status').textContent=`Saved display unavailable: ${error.message}. No outcome or acceptance is inferred.`;});
