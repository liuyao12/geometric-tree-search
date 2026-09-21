import {matching3DMarkings,markingSystem} from './marking-storage.js?v=20260921-marking-library';
// Assignments live in this browser only. Workers revalidate before using them.
export class MarkingLibrary{
 constructor(host,{learn,use}){
  host.innerHTML='<label>Saved marking <select aria-label="Saved marking"></select></label><button type="button" class="marking-use">Tile with marking</button><button type="button" class="marking-new">Learn new marking</button>';
  this.select=host.querySelector('select');this.use=host.querySelector('.marking-use');this.learn=host.querySelector('.marking-new');this.model=null;this.entries=[];this.visit=[];this.busy=false;
  this.use.onclick=()=>{const entry=this.entries.find(e=>e.marking.saved.id===this.select.value);if(entry)use(entry);};this.learn.onclick=learn;
  this.refresh();
 }
 refresh(model=this.model,marking=null){
  this.model=model;
  if(model&&marking?.accepted&&marking.saved){const entry={domain:{...markingSystem(model),extent:marking.extent},marking};this.visit=this.visit.filter(e=>e.marking.saved.id!==marking.saved.id);this.visit.push(entry);}
  const selected=marking?.saved?.id??this.select.value;
  const system=model&&JSON.stringify(markingSystem(model));
  const entries=model?[...matching3DMarkings(model),...this.visit.filter(e=>JSON.stringify(markingSystem(e.domain))===system)]:[];
  this.entries=[...new Map(entries.map(e=>[e.marking.saved.id,e])).values()].reverse();
  this.select.replaceChildren();
  if(!this.entries.length){const o=document.createElement('option');o.textContent='No saved markings for this system';o.value='';this.select.append(o);}
  for(const e of this.entries){const o=document.createElement('option');o.value=e.marking.saved.id;o.textContent=e.marking.saved.name;this.select.append(o);}
  if(this.entries.some(e=>e.marking.saved.id===selected))this.select.value=selected;
  this.lock(this.busy);
 }
 lock(busy){this.busy=busy;this.select.disabled=busy||!this.entries.length;this.use.disabled=busy||!this.entries.length;this.learn.disabled=busy;}
}
