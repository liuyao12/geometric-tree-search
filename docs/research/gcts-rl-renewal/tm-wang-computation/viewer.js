'use strict';
(() => {
  const channels = ['horizontal_window','horizontal_mode','horizontal_scan','vertical_symbol','vertical_phase'];
  const hues = {horizontal_window:210,horizontal_mode:275,horizontal_scan:30,vertical_symbol:145,vertical_phase:355};
  const byId = id => { const n=document.getElementById(id); if(!n) throw Error(`Missing reader element ${id}`); return n; };
  const need=(v,m)=>{if(!v)throw Error(m);};
  const text=(parent,tag,value,cls)=>{const n=document.createElement(tag);n.textContent=value;if(cls)n.className=cls;parent.append(n);return n;};
  const tex=s=>String(s).replace(/\\/g,'\\backslash ').replace(/[{}_$%&#]/g,c=>`\\${c}`).replace(/\^/g,'\\hat{}').replace(/~/g,'\\tilde{}');
  const math=s=>`\\(${s}\\)`;
  const sym=s=>`\\mathtt{${tex(s)}}`;
  const state=s=>`\\mathit{${tex(s)}}`;
  const stable=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])):x);
  const equal=(a,b)=>stable(a)===stable(b);
  const clear=n=>n.replaceChildren();
  const colour=(channel,id)=>`hsl(${(hues[channel]+(id*17)%25-12+360)%360},${68+(id*3)%21}%,${28+(id*7)%43}%)`;
  let summary,visual,evidence,controls,program,palette,census,selectedCase,outcomeIndex=0;
  const cache=new Map();
  const active=new Set(channels);
  let rendering=Promise.resolve();
  function typeset(node){rendering=rendering.then(async()=>{if(window.MathJax?.startup?.promise)await window.MathJax.startup.promise;need(window.MathJax?.typesetPromise,'Established MathJax renderer unavailable');await window.MathJax.typesetPromise([node]);}).catch(e=>text(byId('tm-status'),'p',`Math rendering error: ${e.message}`));}
  function lookup(channel,code){const rows=palette.colors[channel];need(Number.isInteger(code)&&rows&&rows[code]?.id===code,'Actual colour ID absent from bound palette');return rows[code].value;}
  function ruleLabel(identity){return math(`\\operatorname{Rule}[\\mathtt{${tex(JSON.stringify(identity))}}]`);}
  function token(t){
    need(Array.isArray(t)&&typeof t[0]==='string','Malformed saved token');
    if(t[0]==='wall'&&t.length===1)return '\\operatorname{Wall}';
    if(t[0]==='symbol'&&t.length===2)return sym(t[1]);
    if(t[0]==='head'&&t.length===3)return `\\overset{${state(t[1])}}{\\underline{${sym(t[2])}}}`;
    if(t[0]==='latch'&&t.length===2){need(Number.isInteger(t[1])&&palette.effective_rules[t[1]],'Unknown actual latch');return `\\operatorname{Latch}(${t[1]})`;}
    throw Error('Unsupported saved token tag');
  }
  function tokenEnglish(t){
    if(t[0]==='symbol')return `The cell contains ${math(sym(t[1]))}.`;
    if(t[0]==='head')return `The cell contains ${math(sym(t[2]))}; the head is here in state ${math(state(t[1]))}.`;
    if(t[0]==='wall')return 'This is a fixed wall token.';
    if(t[0]==='latch'){
      const r=palette.effective_rules[t[1]];need(r,'Saved latch is outside this palette');
      const movement={L:'move left',R:'move right',S:'stay here'}[r.move];need(movement,'Unknown saved move');
      return `Announce ${ruleLabel(r.identity)}: read ${math(sym(r.read))} in state ${math(state(r.state))}, write ${math(sym(r.write))}, ${movement}, and enter state ${math(state(r.next_state))}.`;
    }
    throw Error('Unsupported English token tag');
  }
  function config(c){need(Array.isArray(c.tape)&&Number.isInteger(c.head)&&c.head>=0&&c.head<c.tape.length,'Saved configuration shape');return `\\langle ${state(c.state)};\\;${c.tape.map((a,i)=>i===c.head?`\\underline{${sym(a)}}`:sym(a)).join('\\,')}\\rangle`;}
  function configEnglish(c){return `The tape is ${math(c.tape.map(sym).join('\\,'))}; the head is at cell ${math(String(c.head))} in state ${math(state(c.state))}.`;}
  function colourValue(v){
    if(Number.isInteger(v))return String(v);
    if(typeof v==='string')return `\\mathtt{${tex(v)}}`;
    need(Array.isArray(v),'Unknown saved colour value');
    if(['symbol','head','latch','wall'].includes(v[0]))return token(v);
    if(v[0]==='pair'&&v.length===4)return `\\operatorname{Pair}(\\text{${tex(v[1])}},${token(v[2])},${token(v[3])})`;
    if(['left_wall','right_wall'].includes(v[0])&&v.length===2)return `\\operatorname{${v[0]==='left_wall'?'LeftWall':'RightWall'}}(\\text{${tex(v[1])}})`;
    throw Error('Unknown saved edge colour structure');
  }
  function svg(parent,tag,attrs){const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));parent.append(n);return n;}
  function tilePicture(tile,translation=[0,0]){
    need(Number.isInteger(tile.id)&&equal(palette.tiles[tile.id],tile),'Tile record does not equal the full palette member');
    need(equal(tile.t,[[0,0,1]]),'Unexpected saved tile support');
    const fig=document.createElement('figure');fig.className='tm-tile';
    const picture=svg(fig,'svg',{viewBox:'0 0 160 160',role:'img','aria-label':`Actual tile ${tile.id}, orientation identity`});
    svg(picture,'rect',{x:20,y:20,width:120,height:120,fill:'#faf9f4',stroke:'#303745','stroke-width':1.5});
    svg(picture,'circle',{cx:80,cy:80,r:5,fill:'#252d3e'});
    const points=new Map();
    for(const mark of tile.m){need(Array.isArray(mark)&&mark.length===4&&channels.includes(mark[0])&&mark.slice(1).every(Number.isInteger),'Bad actual point mark');
      const key=`${mark[1]},${mark[2]}`;if(!points.has(key))points.set(key,[]);points.get(key).push(mark);lookup(mark[0],mark[3]);}
    for(const marks of points.values()){
      const visible=marks.filter(m=>active.has(m[0]));visible.forEach((m,i)=>svg(picture,'circle',{cx:80+60*m[1],cy:80-60*m[2],r:4+5*i,fill:'none',stroke:colour(m[0],m[3]),'stroke-width':3}));
    }
    const cap=text(fig,'figcaption',math(`\\tau_{${tile.id}},\\quad g=(2\\cdot${translation[0]/2},2\\cdot${translation[1]/2})`));
    text(cap,'span',' · translation only','tm-meta');
    return fig;
  }
  function pointTable(parent,tile,translation=[0,0]){
    text(parent,'p',math(`t(${translation[0]},${translation[1]})=1`));
    const table=document.createElement('table');parent.append(table);const head=document.createElement('thead');table.append(head);const hr=document.createElement('tr');head.append(hr);
    for(const label of ['Channel','Assigned point value','Actual colour meaning'])text(hr,'th',label);
    const body=document.createElement('tbody');table.append(body);
    for(const [channel,x,y,id] of tile.m){if(!active.has(channel))continue;const r=document.createElement('tr');body.append(r);
      const c=text(r,'td',channel);c.style.borderLeft=`5px solid ${colour(channel,id)}`;
      text(r,'td',math(`m_{\\mathtt{${tex(channel)}}}(${x+translation[0]},${y+translation[1]})=${id}`));
      text(r,'td',math(colourValue(lookup(channel,id))));}
  }
  function fillSelect(n,rows,label){clear(n);rows.forEach((row,i)=>{const o=document.createElement('option');o.value=String(i);o.textContent=label(row,i);n.append(o);});}
  async function fetched(record){
    need(record&&typeof record.url==='string'&&typeof record.sha256==='string'&&Number.isInteger(record.bytes),'Missing prospective artifact binding');
    const u=new URL(record.url,location.href);need(u.origin===location.origin,'Reader artifacts must share this public origin');
    const key=`${u.href}#${record.sha256}`;if(cache.has(key))return cache.get(key);
    const response=await fetch(u.href,{cache:'no-store'});need(response.ok,`Artifact failed: ${response.status}`);
    const raw=new Uint8Array(await response.arrayBuffer());need(raw.byteLength===record.bytes,'Artifact byte length mismatch');
    const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),b=>b.toString(16).padStart(2,'0')).join('');need(hash===record.sha256,'Artifact SHA-256 mismatch');
    const v=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));cache.set(key,v);return v;
  }
  async function pinned(pin){const r=summary.routes.find(r=>r.source_path===pin.path);need(r&&r.sha256===pin.sha256&&r.bytes===pin.bytes,'Saved raw pin has no exact public route');return fetched(r);}
  function mode(){return byId('tm-boundary-mode').value;}
  function currentOutcomes(){return selectedCase?.modes?.[mode()]?.outcomes||[];}
  function renderTile(){
    const phase=byId('tm-phase').value,kind=byId('tm-mode').value;
    const list=palette.tiles.filter(t=>(phase==='all'||t.logical_window.phase===phase)&&(kind==='all'||t.logical_window.mode===kind));
    let id=Number(byId('tm-tile').value);if(!list.some(t=>t.id===id))id=list[0]?.id;
    clear(byId('tm-tile'));for(const tile of list){const o=document.createElement('option');o.value=String(tile.id);o.textContent=`Tile ${tile.id}`;byId('tm-tile').append(o);}byId('tm-tile').value=String(id);
    const view=byId('tm-palette-view');clear(view);if(id===undefined){text(view,'p','No actual palette tile matches these UI filters.');return;}
    text(view,'p',`The current display filter contains ${list.length} members of the whole ${palette.tiles.length}-tile palette.`);const tile=palette.tiles[id];view.append(tilePicture(tile));const w=tile.logical_window;
    text(view,'p',math(`(${token(w.window[0])},${token(w.window[1])},${token(w.window[2])})\\;\\longmapsto\\;${token(w.output)}`));
    text(view,'p',`Saved phase: ${w.phase}. Saved mode: ${w.mode}. ${tokenEnglish(w.output)}`);
    pointTable(view,tile);const details=document.createElement('details');view.append(details);text(details,'summary','Exact saved tile record');text(details,'pre',JSON.stringify(tile,null,2));typeset(view);
  }
  function renderRows(){
    const view=byId('tm-row-view');clear(view);if(!selectedCase)return;
    const lane=selectedCase.modes[mode()],outcomes=lane.outcomes;outcomeIndex=Math.min(outcomeIndex,Math.max(0,outcomes.length-1));
    fillSelect(byId('tm-outcome'),outcomes,(_,i)=>`Joined outcome ${i+1}`);byId('tm-outcome').value=String(outcomeIndex);
    text(view,'p',math(`C_{\\mathrm{in}}=${config(selectedCase.configuration)}`));text(view,'p',configEnglish(selectedCase.configuration));
    text(view,'p',`The whole saved case has ${selectedCase.modes.normal.outcomes.length} NORMAL outcome(s) and ${selectedCase.modes.accept_scan.outcomes.length} ACCEPT/FINAL outcome(s). This selected ${mode()==='normal'?'NORMAL step-relation':'ACCEPT/FINAL'} boundary has ${outcomes.length} complete joined outcome(s). The independent direct-oracle record is shown below.`);
    if(outcomes.length){const o=outcomes[outcomeIndex];need(o.rows.length===2,'Expected complete two-microrow patch');
      for(let row=0;row<2;row++){
        const section=document.createElement('section');view.append(section);text(section,'h3',row===0?'Latch row':'Apply row');
        text(section,'p',math(`W_{${row+1}}=(${o.rows[row].output_tokens.map(token).join(',\\,')})`));
        const grid=document.createElement('div');grid.className='tm-row';grid.style.gridTemplateColumns=`repeat(${o.rows[row].tile_ids.length}, minmax(120px,1fr))`;section.append(grid);
        o.rows[row].tile_ids.forEach((id,x)=>{const tile=palette.tiles[id];need(tile,'Row names an absent palette tile');const p=o.placements.find(p=>equal(p.key,[id,2*x,2*row]));
          need(p&&equal(p.t,tile.t.map(([a,b,v])=>[a+2*x,b+2*row,v]))&&equal(p.m,tile.m.map(([c,a,b,v])=>[c,a+2*x,b+2*row,v])),'Saved placement translation differs from actual palette support');
          const card=document.createElement('div');grid.append(card);card.append(tilePicture(tile,[2*x,2*row]));text(card,'p',tokenEnglish(o.rows[row].output_tokens[x]));const exact=document.createElement('details');card.append(exact);text(exact,'summary','Exact translated point marks');pointTable(exact,tile,[2*x,2*row]);});
      }
      text(view,'p',`${ruleLabel(o.transition_identity)}. Output ${math(`C_{\\mathrm{out}}=${config(o.configuration)}`)}. ${configEnglish(o.configuration)}`);
      text(view,'p',`The saved output state is ${o.accepting?'accepting':'nonaccepting'} for this configured machine.`);
      const detail=document.createElement('details');view.append(detail);text(detail,'summary','Exact translated patch and point receipt');text(detail,'pre',JSON.stringify({placements:o.placements,point_receipt:o.point_receipt},null,2));
    }else{text(view,'p','There is no saved complete patch for this boundary. This reader supplies no replacement tiles or witness.');}
    const d=document.createElement('details');view.append(d);text(d,'summary','Whole saved direct successors and declared boundary');text(d,'pre',JSON.stringify({direct:selectedCase.expected_direct,boundary:lane.boundary},null,2));typeset(view);
  }
  function renderControls(){
    const view=byId('tm-control-view');clear(view);
    for(const c of controls.controls){const s=document.createElement('section');view.append(s);text(s,'h3',c.name.replace(/_/g,' '));
      text(s,'p',`Saved control flag: ${c.passed===true?'passed':c.rejected===true?'rejected as intended':'unresolved'}. This is source-bound control evidence, not a reader-issued mathematical acceptance.`);
      if(c.actual_record){text(s,'p',math(`C_{\\mathrm{in}}=${config(c.actual_record.configuration)}`));
        text(s,'p',`Saved NORMAL outcomes: ${c.actual_record.modes.normal.outcomes.length}. Saved ACCEPT outcomes: ${c.actual_record.modes.accept_scan.outcomes.length}.`);
        for(const o of c.actual_record.modes.normal.outcomes)text(s,'p',`${ruleLabel(o.transition_identity)} produces ${math(config(o.configuration))}.`);
      }
      if(c.forbidden_configurations){text(s,'p','The saved negative control excludes these mixed configurations:');for(const f of c.forbidden_configurations)text(s,'p',math(config(f)));}
      if(c.reason)text(s,'p',c.reason);
      const details=document.createElement('details');s.append(details);text(details,'summary','Exact full saved control');text(details,'pre',JSON.stringify(c,null,2));
    }typeset(view);
  }
  function requestedDefault(id){
    if(id==='nondeterministic')return controls.controls.find(c=>c.name==='ND_shared_transition_no_mixed_choices')?.actual_record.configuration;
    if(id==='stationary-nonaccept')return controls.controls.find(c=>c.name==='valid_nonaccepting_stationary_step_FINAL_rejected')?.actual_record.configuration;
    if(id==='deterministic')return {tape:['0','_'],head:0,state:'q'};
    if(id==='stuck')return {tape:['0'],head:0,state:'q'};
    throw Error('No declared UI default for this saved program');
  }
  async function selectProgram(){
    const id=byId('tm-program').value;program=visual.programs.find(p=>p.program_id===id);need(program,'Program outside bound visual data');
    const e=evidence.programs.find(p=>p.program_id===id);need(e&&equal(e.palette,program.whole_palette),'Palette evidence/visual pins differ');
    palette=await pinned(program.whole_palette);census=await pinned(e.census);need(palette.complete_palette===true&&palette.tiles.length===e.palette_audit.tiles_checked,'Whole palette census differs');
    need(census.complete_configuration_count===census.cases.length&&census.cases.length===e.configurations,'Whole configuration census differs');
    need(equal(program.machine,census.program)&&equal(palette.channels,channels),'Palette/census machine and channel order differ');
    const defaultConfiguration=requestedDefault(id),index=census.cases.findIndex(c=>equal(c.configuration,defaultConfiguration));need(index>=0,'Declared UI input is absent from the whole saved census');
    fillSelect(byId('tm-case'),census.cases,(_,i)=>`Configuration ${i+1}`);byId('tm-case').value=String(index);selectedCase=census.cases[index];outcomeIndex=0;
    if(id==='nondeterministic'||id==='stationary-nonaccept'){
      const control=controls.controls.find(c=>equal(c.actual_record?.configuration,defaultConfiguration)&&c.name===(id==='nondeterministic'?'ND_shared_transition_no_mixed_choices':'valid_nonaccepting_stationary_step_FINAL_rejected'));
      need(control&&equal(control.actual_record,selectedCase),'Default mandatory control does not equal its saved full census case');
    }
    byId('tm-boundary-mode').value='normal';
    clear(byId('tm-program-description'));text(byId('tm-program-description'),'p',`The bound complete palette contains ${palette.tiles.length} actual tiles. The census contains ${census.cases.length} actual input configurations.`);
    text(byId('tm-program-description'),'p',`The compiled initial state is ${math(state(palette.machine.initial_state))}. Other census states are declared bottom-input tokens in the same palette.`);
    const details=document.createElement('details');byId('tm-program-description').append(details);text(details,'summary','Exact saved configured machine and palette transformations');text(details,'pre',JSON.stringify({machine:palette.machine,transformations:palette.transformations},null,2));
    renderTile();renderRows();typeset(byId('tm-program-description'));
  }
  async function start(){
    const route=new URL(document.body.dataset.summary||'summary.json',location.href);need(route.origin===location.origin,'Same-origin summary file required');
    const response=await fetch(route,{cache:'no-store'});need(response.ok,'No actual artifact summary is available yet');summary=await response.json();
    need(summary.schema==='tm-wang-visual-reader-summary-v1'&&Array.isArray(summary.routes),'Reader summary schema');
    visual=summary.visual_data;evidence=summary.evidence;controls=summary.controls;
    need(visual?.schema==='actual-two-phase-tm-point-visual-data-v1'&&evidence?.schema==='two-phase-tm-palette-relation-control-evidence-v1'&&Array.isArray(controls?.controls),'Actual saved artifact schemas');
    need(equal(visual.controls,evidence.mandatory_controls),'Control pins differ');
    need(equal(controls,await pinned(visual.controls))&&equal(visual,await pinned(evidence.visual_data)),'Inline summary/control objects differ from their complete raw artifact bindings');
    need(equal(visual.programs.map(p=>p.program_id).sort(),evidence.programs.map(p=>p.program_id).sort()),'Whole program lists differ');
    const selector=byId('tm-program');clear(selector);for(const p of visual.programs){const o=document.createElement('option');o.value=p.program_id;o.textContent=p.program_id;selector.append(o);}selector.value='deterministic';
    const banner=byId('tm-status');clear(banner);text(banner,'p',summary.independent_controls_accepted===true?'ROOT-bound control acceptance supplied; this display is a reader of those records.':'Pending independent control acceptance; data presence is not an acceptance flag.');
    if(summary.scope)text(banner,'p',summary.scope);
    if(summary.resource){const detail=document.createElement('details');banner.append(detail);text(detail,'summary','Saved resource acceptance and scope');text(detail,'pre',JSON.stringify(summary.resource,null,2));}
    for(const c of channels){const label=document.createElement('label');label.className='tm-layer';const input=document.createElement('input');input.type='checkbox';input.checked=true;
      input.addEventListener('change',()=>{input.checked?active.add(c):active.delete(c);renderTile();renderRows();});label.append(input);text(label,'span',c);label.style.borderColor=colour(c,0);byId('tm-layers').append(label);}
    selector.addEventListener('change',()=>selectProgram().catch(fail));byId('tm-phase').addEventListener('change',renderTile);byId('tm-mode').addEventListener('change',renderTile);
    byId('tm-tile').addEventListener('change',renderTile);byId('tm-case').addEventListener('change',()=>{selectedCase=census.cases[Number(byId('tm-case').value)];outcomeIndex=0;renderRows();});
    byId('tm-boundary-mode').addEventListener('change',()=>{outcomeIndex=0;renderRows();});byId('tm-outcome').addEventListener('change',()=>{outcomeIndex=Number(byId('tm-outcome').value);renderRows();});
    renderControls();await selectProgram();
  }
  function fail(error){const n=byId('tm-status');clear(n);text(n,'p',`Reader unavailable: ${error.message}`);text(n,'p','No palette, patch, outcome or acceptance is fabricated. ROOT must supply exact public artifact routes.');}
  start().catch(fail);
})();
