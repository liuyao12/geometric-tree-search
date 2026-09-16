// Sites belong to tile prototypes: coincident coordinates on different tiles
// are separate points. Explicit zeros count as assigned values.
export function markingMetadata(model){
 const support=model?.support||[],tiles=[...new Set(support.map(e=>e.tile))];
 const perTile=tiles.map(tile=>{const entries=support.filter(e=>e.tile===tile);return {tile,points:new Set(entries.map(e=>e.point.join(','))).size,values:entries.length};});
 return {points:perTile.reduce((n,t)=>n+t.points,0),values:support.length,nonzero:support.filter(e=>e.value!==0).length,distinctValues:new Set(support.map(e=>e.value)).size,perTile};
}
export function markingMetadataText(model){
 const m=markingMetadata(model);
 return `${m.points} points${m.perTile.length>1?' across '+m.perTile.length+' tiles':''} · ${m.values} assigned values · ${m.nonzero} nonzero · ${m.distinctValues} distinct values`;
}
