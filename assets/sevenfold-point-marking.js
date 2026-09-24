// Fixed, published m-values. Missing and zero are different. Reference counts
// make additions/removals exact even where several tiles share an assignment.
export function createPointMarking() {
  const field=new Map();let checks=0,prunes=0,references=0;
  return {
    add(tile){for(const m of tile.marks){const old=field.get(m.address);if(old&&old.value!==m.value)throw Error('Conflicting point marking');if(old)old.count++;else field.set(m.address,{value:m.value,count:1,point:m.point,channel:m.channel});references++;}},
    remove(tile){for(const m of tile.marks){const old=field.get(m.address);if(!old||old.value!==m.value)throw Error('Invalid marking rollback');if(--old.count===0)field.delete(m.address);references--; }},
    rejects(tile){checks++;for(const m of tile.marks){const old=field.get(m.address);if(old&&old.value!==m.value){prunes++;return true;}}return false;},
    snapshot(){return {points:new Set([...field.values()].map(m=>m.point.join(','))).size,values:field.size,references,checks,prunes};},
    inspect(){return [...field].map(([address,m])=>[address,m.value,m.count]).sort();}
  };
}

// Exact finite relaxation at ONE vertex: fourteen angular sectors and the
// published marking values on its radial edges. It checks every possible
// gap-filling chain. Failure is a proved local obstruction; success is only
// local feasibility. This is propagation/memoization, NOT a trained marking.
export function createVertexCompletion(corners,{cacheLimit=32768}={}) {
  const transitions=Array.from({length:14},()=>Array.from({length:7},()=>Array(8).fill(0)));
  for(const c of corners)transitions[c.start][c.width][c.from]|=1<<c.to;
  const cache=new Map(),stats={checks:0,hits:0,proofs:0,prunes:0};let negativeCached=0;
  function solve(corners){
    const occupied=Array(14).fill(false),labels=Array(14).fill(-1);
    for(const c of corners){
      for(let j=0;j<c.width;j++){const s=(c.start+j)%14;if(occupied[s])return false;occupied[s]=true;}
      for(const [ray,value]of [[c.start,c.from],[(c.start+c.width)%14,c.to]]){if(labels[ray]!==-1&&labels[ray]!==value)return false;labels[ray]=value;}
    }
    if(!corners.length)return true;
    for(let start=0;start<14;start++)if(!occupied[start]&&occupied[(start+13)%14]){
      let length=1;while(!occupied[(start+length)%14])length++;
      const reachable=Array(length+1).fill(0);reachable[0]=1<<labels[start];
      for(let offset=0;offset<length;offset++)if(reachable[offset]){
        const row=transitions[(start+offset)%14];
        for(let width=1;width<=6&&offset+width<=length;width++)for(let value=0;value<8;value++)if(reachable[offset]&(1<<value))reachable[offset+width]|=row[width][value];
      }
      if(!(reachable[length]&(1<<labels[(start+length)%14])))return false;
    }
    return true;
  }
  return {
    allows(corners){stats.checks++;const signature=corners.map(c=>`${c.start}.${c.width}.${c.from}.${c.to}`).sort().join('|');
      if(cache.has(signature)){stats.hits++;const result=cache.get(signature);if(!result)stats.prunes++;return result;}
      const result=solve(corners);if(cache.size>=cacheLimit){const oldest=cache.keys().next().value;if(!cache.get(oldest))negativeCached--;cache.delete(oldest);}cache.set(signature,result);if(!result)negativeCached++;
      if(!result){stats.proofs++;stats.prunes++;}return result;
    },
    snapshot:()=>({...stats,cached:cache.size,negativeCached}),
    // Uncached entry point for independent replay and exhaustive tiny tests.
    solve
  };
}
