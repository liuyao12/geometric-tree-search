// The browser reads only the first source frame; no coordinates are bundled.
export function parseFrame(text) {
  const lines=text.trimEnd().split(/\r?\n/),n=Number(lines[0]);
  if(!Number.isInteger(n)||n<1||n>10000||lines.length!==n+2)throw Error('Invalid first-frame length');
  const props=/Properties=([^\s]+)/.exec(lines[1])?.[1].split(':');
  const lattice=/Lattice="([^"]+)"/.exec(lines[1])?.[1].trim().split(/\s+/).map(Number);
  if(!props||props.length%3||!lattice||lattice.length!==9||!lattice.every(Number.isFinite))throw Error('Missing frame schema or cell');
  let offset=0,speciesOffset,positionOffset;
  for(let i=0;i<props.length;i+=3){const size=Number(props[i+2]);if(!Number.isInteger(size)||size<1)throw Error('Invalid property width');if(props[i]==='species'&&size===1)speciesOffset=offset;if(props[i]==='pos'&&size===3)positionOffset=offset;offset+=size;}
  if(speciesOffset===undefined||positionOffset===undefined)throw Error('Missing atom fields');
  const atoms=lines.slice(2).map(line=>{const fields=line.trim().split(/\s+/),position=fields.slice(positionOffset,positionOffset+3).map(Number);if(fields.length!==offset||position.length!==3||!position.every(Number.isFinite))throw Error('Invalid atom row');return {species:fields[speciesOffset],position};});
  return {atoms,cell:[lattice.slice(0,3),lattice.slice(3,6),lattice.slice(6,9)]};
}
export function reorderFrame(frame,config){
  if(frame.atoms.length!==config.atoms||config.sourceOrder.length!==config.atoms||new Set(config.sourceOrder).size!==config.atoms||config.sourceOrder.some(i=>!Number.isInteger(i)||i<0||i>=config.atoms))throw Error('Source atom mapping mismatch');
  return {...frame,atoms:config.sourceOrder.map(i=>frame.atoms[i])};
}
export function coverage(state,n,count=state.supports.length){
  if(!Number.isInteger(count)||count<0||count>state.supports.length)throw Error('Invalid reveal count');
  const totals=Array(n).fill(0);
  for(const ids of state.supports.slice(0,count)){if(new Set(ids).size!==ids.length)throw Error('Repeated support atom');for(const i of ids){if(!Number.isInteger(i)||i<0||i>=n)throw Error('Support atom outside frame');if(++totals[i]>2)throw Error('Overfilled atom');}}
  return totals;
}
export async function readSourceFrame(config,{fetcher=fetch,cryptoApi=crypto}={}){
  const response=await fetcher(config.sourceUrl,{credentials:'omit',referrerPolicy:'no-referrer'});
  if(!response.ok||!response.body)throw Error('Author coordinate source unavailable');
  const reader=response.body.getReader(),decoder=new TextDecoder();let text='',frameText;
  try{while(true){const {value,done}=await reader.read();if(done)break;text+=decoder.decode(value,{stream:true});if(text.length>2000000)throw Error('First-frame size limit');let end=-1;for(let i=0;i<config.atoms+2;i++){end=text.indexOf('\n',end+1);if(end<0)break;}if(end>=0){frameText=text.slice(0,end+1);break;}}}finally{await reader.cancel();}
  if(!frameText)throw Error('Truncated source frame');
  const digest=await cryptoApi.subtle.digest('SHA-256',new TextEncoder().encode(frameText));
  const hash=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');
  if(hash!==config.firstFrameHash)throw Error('Source frame hash mismatch');
  return reorderFrame(parseFrame(frameText),config);
}
