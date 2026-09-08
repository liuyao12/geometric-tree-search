import {canonical,latticeKey,cycloAdd} from './cyclotomic-five.js?v=20260908-speed';
const sub=(a,b)=>cycloAdd(a,{...canonical(b),coeff:canonical(b).coeff.map(n=>-n)});
const popcount=n=>{let c=0;while(n){n&=n-1n;c++;}return c;};

// Tile-agnostic learned point markings. The fiber is the finite universe of
// candidate moves anchored at a point. A bit certifies that a tile blocks that
// move. Values combine by OR, not by equality of preassigned line indicators.
// All geometry and optional problem constraints are supplied by the adapter.
export function createObstructionMarking({movesAt,pairAllowed,pose,anchor,
  slotCount,capacityMask,unfinished,weightAt,pointTotal,onPairProof=null,translate=null}){
  const full=(1n<<BigInt(slotCount))-1n,tables=new Map(),supports=new WeakMap(),maskCache=new Map();
  let revision=0,aggregate=new Map(),active=[];
  const stats={attempts:0,proofs:0,unsupported:0,entries:0,checks:0,prunes:0,maskChecks:0,trainingPairChecks:0,pairProofs:0,maskCacheHits:0};
  function support(tile){const old=supports.get(tile);if(old?.revision===revision)return old.rows;
    const rows=[...(tables.get(pose(tile))?.values()||[])].map(r=>({...r,point:cycloAdd(anchor(tile),r.offset)}));
    supports.set(tile,{revision,rows});return rows;}
  function rebuild(tiles){active=tiles;aggregate=new Map();for(const tile of tiles)for(const r of support(tile)){
    const key=latticeKey(r.point);aggregate.set(key,(aggregate.get(key)||0n)|r.mask);
  }}
  function rejects(tile){stats.checks++;const contributions=new Map();
    for(const r of support(tile)){const key=latticeKey(r.point),old=contributions.get(key);contributions.set(key,{point:r.point,mask:(old?.mask||0n)|r.mask});}
    // A new vertex can activate an already learned mask with no contribution
    // from this tile. Capacity changes at existing vertices matter as well.
    for(const p of tile.exactPoints){const key=latticeKey(p);if(aggregate.has(key)&&!contributions.has(key))contributions.set(key,{point:p,mask:0n});}
    for(const[key,r]of contributions){const total=pointTotal(r.point)+weightAt(tile,r.point);if(!unfinished(total))continue;
      stats.maskChecks++;if(((aggregate.get(key)||0n)|r.mask|capacityMask(total))===full){stats.prunes++;return{point:r.point};}
    }
    return null;
  }
  function learn(point,tiles=active){
    stats.attempts++;const total=tiles.reduce((s,t)=>s+weightAt(t,point),0);if(!unfinished(total))return false;
    const origin={coeff:[0,0,0,0],denominator:1};
    const moves=movesAt(translate?origin:point);if(moves.length!==slotCount)throw Error('Candidate fiber changed');
    const masks=tiles.map(tile=>{
      const key=pose(tile)+'@'+latticeKey(sub(point,anchor(tile)));
      if(maskCache.has(key)){stats.maskCacheHits++;return{tile,mask:maskCache.get(key)};}
      const relative=translate?translate(tile,sub(origin,point)):tile;stats.trainingPairChecks+=moves.length;
      const mask=moves.reduce((m,c,i)=>pairAllowed(relative,c)?m:m|(1n<<BigInt(i)),0n);maskCache.set(key,mask);return{tile,mask};
    });
    if(onPairProof){let found=false;for(let i=masks.length-1;i>=0&&!found;i--)for(let j=0;j<i;j++){
      const pairTotal=weightAt(masks[i].tile,point)+weightAt(masks[j].tile,point);
      if(unfinished(pairTotal)&&(masks[i].mask|masks[j].mask|capacityMask(pairTotal))===full&&onPairProof(masks[i].tile,masks[j].tile,point)){stats.pairProofs++;found=true;break;}
    }}
    let covered=capacityMask(total),chosen=[];
    while(covered!==full){let best=null,gain=0;for(const r of masks){const n=popcount(r.mask&~covered);if(n>gain){best=r;gain=n;}}
      if(!best){stats.unsupported++;return false;}chosen.push(best);covered|=best.mask;
    }
    // Delete redundant contributors; the resulting cover is independently
    // checkable against the exact base predicate, with no success examples.
    for(let i=chosen.length-1;i>=0;i--)if(chosen.reduce((m,r,j)=>j===i?m:m|r.mask,capacityMask(total))===full)chosen.splice(i,1);
    let changed=false;
    for(const {tile,mask}of chosen){const type=pose(tile),offset=sub(point,anchor(tile)),key=latticeKey(offset);
      if(!tables.has(type))tables.set(type,new Map());const table=tables.get(type),old=table.get(key);
      if(!old){table.set(key,{offset,mask});stats.entries++;changed=true;}else if((old.mask|mask)!==old.mask){old.mask|=mask;changed=true;}
    }
    if(changed){revision++;stats.proofs++;rebuild(tiles);}return changed;
  }
  function exportTables(){return [...tables].map(([type,rows])=>({type,rows:[...rows.values()].map(r=>({offset:r.offset,mask:r.mask.toString()}))}));}
  return{learn,rebuild,rejects,support,
    snapshot({details=true}={}){return{revision,slotCount,...stats,cachedMasks:maskCache.size,...(details?{tables:exportTables()}:{})};},
    // Exposes certified rows for independent validation, never a training oracle.
    rows(){return exportTables();}
  };
}
