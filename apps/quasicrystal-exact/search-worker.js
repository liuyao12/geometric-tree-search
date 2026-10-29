import { FaceSearch, chooseFace } from '../../assets/icosahedral-face-search.js';
import { ORIENTATIONS } from '../../assets/icosahedral-exact.js';
import { displayTile } from './display-model.js';
let search=null,running=false,timer=null,delay=130;
const prototypes=['prolate','oblate'].map(kind=>displayTile(ORIENTATIONS.find(t=>t.kind===kind)));
function packet(){
 const tiles=[...search.placed.values()].map(r=>({...displayTile(r.tile),generation:r.generation}));
 const choice=chooseFace(search.frontier)?.point;
 self.postMessage({type:'snapshot',running,summary:search.summary(),event:search.lastEvent,trace:search.events.slice(-140),tree:search.tree.slice(-200),
  display:{tiles,connected:tiles.map((_,i)=>i),prototypes,window:{vertices:[],faces:[],points:[]}},
  nextFace:choice?choice.owner.tile.faces[choice.owner.faceIndex].map(i=>choice.owner.tile.vertices[i].map(x=>x.toJSON())):null});
}
function stop(){running=false;clearTimeout(timer);timer=null;}
function tick(){
 if(!running||!search)return;
 try{search.step();if(['checkpoint','budget','exhausted'].includes(search.state))stop();packet();if(running)timer=setTimeout(tick,delay);}
 catch(error){stop();self.postMessage({type:'error',error:error.message});}
}
self.onmessage=({data})=>{
 try{
  if(data.type==='init'){stop();search=new FaceSearch(data.config);delay=data.delay??130;packet();if(data.auto){running=true;timer=setTimeout(tick,delay);}return;}
  if(!search)return;
  if(data.type==='pause'){stop();packet();}
  if(data.type==='start'){
   if(Number.isSafeInteger(data.target)&&data.target>=2){search.config.target=data.target;if(search.state==='checkpoint'&&data.target>search.placed.size)search.state='ready';}
   if(!running&&!['checkpoint','budget','exhausted'].includes(search.state)){running=true;packet();timer=setTimeout(tick,0);}
  }
  if(data.type==='step'){stop();if(Number.isSafeInteger(data.target)&&data.target>=2){search.config.target=data.target;if(search.state==='checkpoint'&&data.target>search.placed.size)search.state='ready';}search.step();packet();}
  if(data.type==='speed')delay=data.delay;
  if(data.type==='export'){const json=JSON.stringify(search.export(),(_,v)=>typeof v==='bigint'?String(v):v,2);self.postMessage({type:'export',json});}
 }catch(error){stop();self.postMessage({type:'error',error:error.message});}
};
