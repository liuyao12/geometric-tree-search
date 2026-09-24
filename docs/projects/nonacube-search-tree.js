const $=id=>document.getElementById(id),base='../../data/nonacube-search-tree/',fmt=n=>n.toLocaleString();
const GROUP=64,PAGE=100,HEIGHT=36,loaded=new Map(),loading=new Map(),childCache=new WeakMap();
const openGroups=new Set(),openPhases=new Set(),openNodes=new Set(),pages=new Map();
let index,rows=[],selected=null,selectionToken=0,focusKey=null,choiceRow=null,choicePage=0;
const nodeKey=(p,n)=>`n:${p}:${n}`,phaseKey=p=>`p:${p}`,groupKey=g=>`g:${g}`;
function fail(e){$('error').textContent=`Unable to load this part of the tree: ${e.message}`;console.error(e);}
function safe(action){return Promise.resolve().then(action).catch(fail);}
function phaseForFrame(frame){
  let lo=0,hi=index.phases.length;
  while(lo+1<hi){const mid=(lo+hi)>>1;if(index.phases[mid].start<=frame)lo=mid;else hi=mid;}return lo;
}
function phaseForConflict(ordinal){
  let lo=0,hi=index.phases.length;
  while(lo+1<hi){const mid=(lo+hi)>>1;if(index.phases[mid].firstConflict<=ordinal)lo=mid;else hi=mid;}
  // Empty phases can share the next conflict's ordinal.
  while(lo<index.phases.length-1&&ordinal>=index.phases[lo].firstConflict+index.phases[lo].conflictCount)lo++;
  return lo;
}
async function phase(p){
  if(loaded.has(p))return loaded.get(p);
  if(loading.has(p))return loading.get(p);
  const promise=(async()=>{
    const response=await fetch(base+index.phases[p].file);if(!response.ok)throw Error(`Phase ${p+1}: HTTP ${response.status}`);
    const data=JSON.parse(await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).text());
    if(data.start!==index.phases[p].start||data.nodes.length!==index.phases[p].nodeCount)throw Error('Tree segment does not match its index');
    loaded.set(p,data);loading.delete(p);return data;
  })();loading.set(p,promise);try{return await promise;}catch(e){loading.delete(p);throw e;}
}
function children(data,n){
  if(!childCache.has(data))childCache.set(data,new Map());const cache=childCache.get(data);
  if(!cache.has(n)){const result=[];for(let c=data.nodes[n][4];c>=0;c=data.nodes[c][5])result.push(c);cache.set(n,result);}return cache.get(n);
}
function chain(data,n){
  const result=[n];while(data.nodes[n][0]===3){const c=data.nodes[n][4];if(c<0||data.nodes[c][0]!==3||data.nodes[c][5]>=0)break;result.push(c);n=c;}return result;
}
function decisionLabel(literal){
  if(literal===0)return 'Unused variable 0';
  const id=Math.abs(literal);return id<=8140?`${literal>0?'Select':'Exclude'} tile ${fmt(id)}`:`Aux ${fmt(id)} ← ${literal>0?'true':'false'}`;
}
function rowLabel(r){
  if(r.type==='group')return `Phases ${fmt(r.group*GROUP+1)}–${fmt(Math.min(index.phases.length,(r.group+1)*GROUP))}`;
  if(r.type==='phase')return `${r.phase===0?'Start':'Restart'} · phase ${fmt(r.phase+1)}`;
  if(r.type==='page')return `${r.direction<0?'← Previous':'Next →'} ${PAGE} entries`;
  const data=loaded.get(r.phase),n=data.nodes[r.node];
  if(r.chain.length>1){const end=data.nodes[r.end];return `${fmt(r.chain.length)} decisions · levels ${n[2]+1}–${end[2]+1}`;}
  return n[0]===3?decisionLabel(n[1]):n[0]===4?`● Conflict ${fmt(n[6])}`:n[0]===5?`↩ Backjump to level ${n[1]}`:'■ Final contradiction';
}
function isOpen(r){return r.type==='group'?openGroups.has(r.group):r.type==='phase'?openPhases.has(r.phase):r.type==='node'&&openNodes.has(nodeKey(r.phase,r.end));}
function isFolder(r){return r.type==='group'||r.type==='phase'||r.type==='node'&&loaded.get(r.phase).nodes[r.end][4]>=0;}
function selectedRow(r){return selected&&r.type==='node'&&r.phase===selected.phase&&r.chain.includes(selected.node)||selected&&r.type==='phase'&&r.phase===selected.phase&&selected.node===0;}
function buildRows(){
  rows=[];const pending=[];
  for(let g=Math.ceil(index.phases.length/GROUP)-1;g>=0;g--)pending.push({type:'group',group:g,depth:0,key:groupKey(g)});
  function pushChildren(p,parent,depth){
    const data=loaded.get(p),list=children(data,parent),start=pages.get(nodeKey(p,parent))??0,end=Math.min(start+PAGE,list.length);
    if(end<list.length)pending.push({type:'page',phase:p,parent,direction:1,offset:end,depth,key:`more:${p}:${parent}:${end}`});
    for(let i=end-1;i>=start;i--)pending.push({type:'node',phase:p,node:list[i],depth});
    if(start>0)pending.push({type:'page',phase:p,parent,direction:-1,offset:Math.max(0,start-PAGE),depth,key:`less:${p}:${parent}:${start}`});
  }
  while(pending.length){const r=pending.pop();
    if(r.type==='node'){r.chain=chain(loaded.get(r.phase),r.node);r.end=r.chain.at(-1);r.key=nodeKey(r.phase,r.end);}
    rows.push(r);
    if(r.type==='group'&&isOpen(r))for(let p=Math.min(index.phases.length,(r.group+1)*GROUP)-1;p>=r.group*GROUP;p--)pending.push({type:'phase',phase:p,depth:1,key:phaseKey(p)});
    if(r.type==='phase'&&isOpen(r)&&loaded.has(r.phase))pushChildren(r.phase,0,r.depth+1);
    if(r.type==='node'&&isFolder(r)&&isOpen(r))pushChildren(r.phase,r.end,r.depth+1);
  }
  paint();
  window.nonacubeTree={frames:index.frames,conflicts:index.conflicts,phases:index.phases.length,visibleRows:rows.length,loadedPhases:loaded.size,selected:selected?{...selected}:null};
}
function paint(){
  const tree=$('tree'),first=Math.max(0,Math.floor(tree.scrollTop/HEIGHT)-10),last=Math.min(rows.length,Math.ceil((tree.scrollTop+tree.clientHeight)/HEIGHT)+10),fragment=document.createDocumentFragment();
  const top=document.createElement('div');top.style.height=`${first*HEIGHT}px`;top.setAttribute('aria-hidden','true');fragment.append(top);
  for(let i=first;i<last;i++){
    const r=rows[i],el=document.createElement('div'),folder=isFolder(r);
    el.className=`tree-row ${r.type}${selectedRow(r)?' selected':''}`;el.dataset.key=r.key;el.dataset.row=String(i);
    el.style.paddingLeft=`${8+Math.min(r.depth,9)*12}px`;el.setAttribute('role','treeitem');el.setAttribute('aria-level',String(r.depth+1));
    el.setAttribute('aria-label',rowLabel(r));el.setAttribute('aria-selected',String(!!selectedRow(r)));el.tabIndex=r.key===focusKey?0:-1;
    if(folder)el.setAttribute('aria-expanded',String(!!isOpen(r)));
    if(r.type==='node'){const op=loaded.get(r.phase).nodes[r.node][0];if(op===4)el.classList.add('leaf');if(op===5)el.classList.add('return');}
    const toggle=document.createElement('button');toggle.className='toggle';toggle.tabIndex=-1;toggle.textContent=folder?(isOpen(r)?'▾':'▸'):'·';toggle.setAttribute('aria-label',`${isOpen(r)?'Collapse':'Expand'} ${rowLabel(r)}`);
    if(!folder)toggle.disabled=true;toggle.onclick=e=>{e.stopPropagation();safe(()=>toggleRow(r));};
    const label=document.createElement('span');label.className='label';label.textContent=rowLabel(r);el.append(toggle,label);
    const count=r.type==='phase'?index.phases[r.phase].conflictCount:r.type==='node'?loaded.get(r.phase).nodes[r.node][7]:null;
    if(folder&&count!==null){const n=document.createElement('span');n.className='number';n.textContent=`${fmt(count)} ${count===1?'leaf':'leaves'}`;el.append(n);}
    if(r.chain?.length>1){const btn=document.createElement('button');btn.className='inspect';btn.textContent='Choices';btn.setAttribute('aria-label',`Inspect ${r.chain.length} compacted decisions`);btn.onclick=e=>{e.stopPropagation();showChoices(r);};el.append(btn);}
    el.onclick=()=>safe(()=>activate(r));el.onkeydown=e=>keyboard(e,r,i);fragment.append(el);
  }
  const bottom=document.createElement('div');bottom.style.height=`${Math.max(0,(rows.length-last)*HEIGHT)}px`;bottom.setAttribute('aria-hidden','true');fragment.append(bottom);
  $('tree-content').replaceChildren(fragment);
}
function focusRow(i){
  i=Math.max(0,Math.min(rows.length-1,i));focusKey=rows[i].key;const t=$('tree');
  if(i*HEIGHT<t.scrollTop)t.scrollTop=i*HEIGHT;if((i+1)*HEIGHT>t.scrollTop+t.clientHeight)t.scrollTop=(i+1)*HEIGHT-t.clientHeight;
  paint();$('tree-content').querySelector(`[data-row="${i}"]`)?.focus({preventScroll:true});
}
function keyboard(e,r,i){
  if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Home','End','Enter',' '].includes(e.key))return;e.preventDefault();e.stopPropagation();
  safe(async()=>{
    if(e.key==='ArrowUp')focusRow(i-1);else if(e.key==='ArrowDown')focusRow(i+1);else if(e.key==='Home')focusRow(0);else if(e.key==='End')focusRow(rows.length-1);
    else if(e.key==='ArrowRight'){if(isFolder(r)&&!isOpen(r)){await toggleRow(r);focusRow(rows.findIndex(x=>x.key===r.key));}else if(isFolder(r))focusRow(i+1);}
    else if(e.key==='ArrowLeft'){if(isFolder(r)&&isOpen(r)){await toggleRow(r);focusRow(rows.findIndex(x=>x.key===r.key));}else{let p=i-1;while(p>0&&rows[p].depth>=r.depth)p--;focusRow(p);}}
    else await activate(r);
  });
}
async function toggleRow(r){
  if(r.type==='group')openGroups.has(r.group)?openGroups.delete(r.group):openGroups.add(r.group);
  else if(r.type==='phase'){
    if(openPhases.has(r.phase))openPhases.delete(r.phase);else{await phase(r.phase);openPhases.add(r.phase);}
  }else if(r.type==='node'){const k=nodeKey(r.phase,r.end);openNodes.has(k)?openNodes.delete(k):openNodes.add(k);}
  buildRows();
}
async function activate(r){
  focusKey=r.key;
  if(r.type==='page'){pages.set(nodeKey(r.phase,r.parent),r.offset);buildRows();return;}
  if(r.type==='group'||r.type==='phase'){await toggleRow(r);return;}
  await revealFrame(index.phases[r.phase].start+r.end);
}
function locateSelected(){
  const i=rows.findIndex(selectedRow);if(i<0)return;const t=$('tree');t.scrollTop=Math.max(0,i*HEIGHT-t.clientHeight/2);paint();
}
function sendFrame(){if(selected)$('patch').contentWindow.postMessage({type:'nonacube-seek',frame:selected.frame},location.origin);}
async function revealFrame(frame,history=true,ticket=++selectionToken){
  if(!Number.isSafeInteger(frame)||frame<0||frame>=index.frames)throw Error(`Event must be from 1 to ${fmt(index.frames)}`);
  const p=phaseForFrame(frame),data=await phase(p);if(ticket!==selectionToken)return;
  const n=frame-data.start,path=[];for(let a=n;a>0;a=data.nodes[a][3])path.push(a);path.push(0);path.reverse();
  openGroups.add(Math.floor(p/GROUP));openPhases.add(p);
  for(let i=0;i<path.length-1;i++){
    const parent=path[i],child=path[i+1];openNodes.add(nodeKey(p,parent));
    const position=children(data,parent).indexOf(child);pages.set(nodeKey(p,parent),Math.floor(position/PAGE)*PAGE);
  }
  const node=data.nodes[n];selected={phase:p,node:n,frame,ordinal:node[6]||null};
  buildRows();locateSelected();updateSelection(data,node);sendFrame();
  if(history){const hash=node[6]?`#conflict=${node[6]}`:`#event=${frame+1}`;if(location.hash!==hash)window.history.pushState(null,'',hash);}
  $('status').textContent=`Selected ${$('selection-title').textContent}`;
}
function updateSelection(data,node){
  const [op,a,b]=node,phaseMeta=index.phases[selected.phase];
  $('selection-path').textContent=`Phase ${fmt(selected.phase+1)} / ${fmt(index.phases.length)} · event ${fmt(selected.frame+1)} / ${fmt(index.frames)}`;
  $('selection-title').textContent=op===4?`Conflict leaf ${fmt(node[6])}`:op===3?decisionLabel(a):op===5?`Backjump to level ${a}`:op===6?`Search phase ${fmt(selected.phase+1)}`:'Final contradiction · UNSAT';
  $('selection-detail').textContent=op===4?`At decision level ${a}, a clause with ${b} literals became false. The preview shows the exact conflicting assignment, including any transient overlaps.`:op===3?`Recorded state immediately before this decision at level ${b+1}. Consequences appear in the following replay event.`:op===5?'Recorded state after undoing the assignments above this level. The entry sits under the decision path being left.':op===6?'A new search phase starts with retained learned clauses.':'The complete recorded search ends with the checked contradiction.';
  $('full-replay').href=`nonacube-search-replay.html?frame=${selected.frame}`;
  const pos=data.conflicts.filter(n=>n<selected.node).length;
  const prior=phaseMeta.firstConflict+pos-1,next=node[6]?node[6]+1:phaseMeta.firstConflict+pos;
  $('previous').disabled=prior<1;$('previous').dataset.target=prior;
  $('next-leaf').disabled=next>index.conflicts;$('next-leaf').dataset.target=next;
  $('leaf-number').value=node[6]??Math.min(index.conflicts,Math.max(1,next));
  $('copy-link').disabled=false;$('reveal').disabled=false;
}
async function revealConflict(ordinal,history=true){
  if(!Number.isSafeInteger(ordinal)||ordinal<1||ordinal>index.conflicts)throw Error(`Conflict must be from 1 to ${fmt(index.conflicts)}`);
  const ticket=++selectionToken,p=phaseForConflict(ordinal),data=await phase(p);if(ticket!==selectionToken)return;
  const n=data.conflicts[ordinal-index.phases[p].firstConflict];
  if(n===undefined)throw Error('Conflict is absent from its phase');await revealFrame(data.start+n,history,ticket);
}
function showChoices(r){choiceRow=r;choicePage=0;paintChoices();$('choices').showModal();}
function paintChoices(){
  const r=choiceRow,data=loaded.get(r.phase),start=choicePage*PAGE,end=Math.min(start+PAGE,r.chain.length),fragment=document.createDocumentFragment();
  $('choices-title').textContent=`${fmt(r.chain.length)} decisions in this path`;
  for(let i=start;i<end;i++){const n=r.chain[i],node=data.nodes[n],button=document.createElement('button');button.className='choice';button.textContent=`Level ${node[2]+1} · ${decisionLabel(node[1])} · event ${fmt(data.start+n+1)}`;button.onclick=()=>safe(async()=>{$('choices').close();await revealFrame(data.start+n);});fragment.append(button);}
  $('choice-list').replaceChildren(fragment);$('choices-page').textContent=`${start+1}–${end} of ${fmt(r.chain.length)}`;$('choices-prev').disabled=choicePage===0;$('choices-next').disabled=end===r.chain.length;
}
async function fromHash(){
  const params=new URLSearchParams(location.hash.slice(1));
  if(params.has('event'))await revealFrame(Number(params.get('event'))-1,false);
  else await revealConflict(Number(params.get('conflict')??1),false);
}
$('tree').onscroll=paint;$('tree').onkeydown=e=>{if(e.target===$('tree')&&['ArrowDown','Home'].includes(e.key)){e.preventDefault();focusRow(0);}};
$('jump-form').onsubmit=e=>{e.preventDefault();safe(()=>revealConflict(Number($('leaf-number').value)));};
$('previous').onclick=()=>safe(()=>revealConflict(Number($('previous').dataset.target)));
$('next-leaf').onclick=()=>safe(()=>revealConflict(Number($('next-leaf').dataset.target)));
$('largest-tree').onclick=()=>safe(()=>revealFrame(index.largestFrame));
$('collapse').onclick=()=>{openGroups.clear();openPhases.clear();openNodes.clear();pages.clear();$('tree').scrollTop=0;buildRows();};
$('reveal').onclick=()=>safe(()=>revealFrame(selected.frame,false));
$('copy-link').onclick=()=>safe(async()=>{await navigator.clipboard.writeText(location.href);$('copy-link').textContent='Copied';setTimeout(()=>$('copy-link').textContent='Copy link',1500);});
$('close-choices').onclick=()=>$('choices').close();$('choices-prev').onclick=()=>{choicePage--;paintChoices();};$('choices-next').onclick=()=>{choicePage++;paintChoices();};
window.addEventListener('hashchange',()=>{if(index)safe(fromHash);});
window.addEventListener('message',e=>{
  if(e.source!==$('patch').contentWindow||e.origin!==location.origin)return;
  if(e.data?.type==='nonacube-ready')sendFrame();
  if(e.data?.type==='nonacube-height'&&Number.isFinite(e.data.height))$('patch').style.height=`${Math.max(400,Math.min(1400,e.data.height))}px`;
  if(e.data?.type==='nonacube-state')$('patch').dataset.frame=String(e.data.index);
});
$('patch').onload=sendFrame;
new ResizeObserver(paint).observe($('tree'));
try{
  const response=await fetch(base+'index.json');if(!response.ok)throw Error(`Index: HTTP ${response.status}`);index=await response.json();
  $('totals').textContent=`${fmt(index.conflicts)} conflict leaves · ${fmt(index.phases.length)} phases`;
  $('leaf-number').max=index.conflicts;for(const id of ['go','largest-tree','collapse'])$(id).disabled=false;
  buildRows();await fromHash();
}catch(e){fail(e);}
