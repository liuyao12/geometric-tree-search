// Independent playback audit: every delta, stable-state nonoverlap, complete
// event counts, recorded maximum, and the largest patch's rooted connectivity.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
const dir=path.resolve(process.argv[2]??'data/nonacube-search-replay');
const m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const key=([x,y,z])=>{assert(x>=-16&&x<16&&y>=-16&&y<16&&z>=-16&&z<16);return (x+16)*1024+(y+16)*32+z+16;};
const all=[m.root,...m.placements.map(([orientation,center])=>{
  const result=[center],normal=[2,1,0][orientation];
  for(let axis=0;axis<3;axis++)if(axis!==normal)for(const offset of [-2,-1,1,2]){const p=[...center];p[axis]+=offset;result.push(p);}return result;
})];
const codes=all.map(vs=>vs.map(key)),occupancy=new Int16Array(32768),live=new Set();
for(const k of codes[0])occupancy[k]++;
let frame=0,overlap=0,maximum=1,stable=0,terminal=0;
const counts={decisions:0,conflicts:0,backtracks:0,searchStarts:0};
for(const entry of m.chunks){
  const c=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(dir,entry.file))));
  assert.equal(c.start,frame);assert.equal(c.frames.length,entry.count);
  assert.deepEqual([...live].sort((a,b)=>a-b),c.initial);assert.deepEqual(c.counters,counts);
  for(const [op,a,b,delta,size,expectedOverlap] of c.frames){
    for(const d of delta){
      const id=Math.abs(d);assert(id>=1&&id<=m.placements.length);
      if(d>0){assert(!live.has(id));live.add(id);for(const k of codes[id]){occupancy[k]++;if(occupancy[k]===2)overlap++;}}
      else {assert(live.has(id));live.delete(id);for(const k of codes[id]){if(occupancy[k]===2)overlap--;occupancy[k]--;}}
    }
    assert.equal(size,live.size+1);assert.equal(expectedOverlap,overlap);
    const name={3:'decisions',4:'conflicts',5:'backtracks',6:'searchStarts'}[op];if(name)counts[name]++;
    if(op===3){assert.equal(overlap,0);stable++;maximum=Math.max(maximum,size);}
    if(frame===m.largestConnected.frame){
      assert.equal(op,3);assert.equal(overlap,0);
      assert.deepEqual([...live].sort((a,b)=>a-b),m.largestConnected.selected);
      const chosen=[0,...live],reached=new Set([0]);
      // Direct pairwise Chebyshev contact, independent of the exporter's masks.
      let changed=true;while(changed){changed=false;for(const a of chosen)if(reached.has(a))for(const b of chosen)if(!reached.has(b)&&all[a].some(p=>all[b].some(q=>p.every((v,i)=>Math.abs(v-q[i])<=1)))){reached.add(b);changed=true;}}
      assert.equal(reached.size,m.largestConnected.tileCount);
      const root=new Set(codes[0]),near=new Set();for(const p of all[0])for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++){const k=key([p[0]+x,p[1]+y,p[2]+z]);if(!root.has(k))near.add(k);}
      assert.equal(near.size,90);assert.equal([...near].filter(k=>occupancy[k]>0).length,m.largestConnected.rootHaloCovered);
    }
    if(op===7){assert.equal(a,0);terminal++;assert.equal(frame,m.frames-1);}
    frame++;
  }
}
assert.equal(frame,m.frames);assert.equal(terminal,1);assert.deepEqual(counts,m.counts);
assert.equal(stable,m.verifiedStableStates);assert.equal(maximum,m.largest.tileCount);
// A connected 39-tile witness meets the upper bound of 39 on ALL stable
// selections, independently proving the claimed connected run maximum.
assert.equal(maximum,m.largestConnected.tileCount);
console.log(JSON.stringify({verified:true,frames:frame,stableStates:stable,counts,largestConnected:maximum,rootHaloCovered:m.largestConnected.rootHaloCovered}));
