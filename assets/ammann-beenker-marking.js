// Supplemental exact corner completion, conditioned on the shared house label.
// A failed finite sector-cover test is sound pruning, not a learned marking.
export function createABCompletion(corners){
 const transitions=Array.from({length:8},()=>Array.from({length:8},()=>Array.from({length:4},()=>Array(8).fill(0))));
 for(const c of corners)transitions[c.house][c.start][c.width][c.from]|=1<<c.to;
 const cache=new Map(),stats={checks:0,hits:0,prunes:0};
 function solve(cs){
  if(!cs.length)return true;const h=cs[0].house,occupied=Array(8).fill(false),labels=Array(8).fill(-1);
  for(const c of cs){if(c.house!==h)return false;for(let j=0;j<c.width;j++){const r=(c.start+j)%8;if(occupied[r])return false;occupied[r]=true;}
   for(const [r,v]of [[c.start,c.from],[(c.start+c.width)%8,c.to]]){if(labels[r]!==-1&&labels[r]!==v)return false;labels[r]=v;}}
  for(let start=0;start<8;start++)if(!occupied[start]&&occupied[(start+7)%8]){
   let length=1;while(!occupied[(start+length)%8])length++;
   const reachable=Array(length+1).fill(0);reachable[0]=1<<labels[start];
   for(let offset=0;offset<length;offset++)for(let width=1;width<=3&&offset+width<=length;width++)for(let v=0;v<8;v++)if(reachable[offset]&(1<<v))reachable[offset+width]|=transitions[h][(start+offset)%8][width][v];
   if(!(reachable[length]&(1<<labels[(start+length)%8])))return false;
  }return true;
 }
 return {allows(cs){stats.checks++;const key=cs.map(c=>[c.start,c.width,c.from,c.to,c.house].join('.')).sort().join('|');let result;
  if(cache.has(key)){stats.hits++;result=cache.get(key);}else{result=solve(cs);if(cache.size>=32768)cache.delete(cache.keys().next().value);cache.set(key,result);}if(!result)stats.prunes++;return result;},solve,snapshot:()=>({...stats,cached:cache.size})};
}
