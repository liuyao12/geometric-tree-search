/** Explicit registry of concrete search definitions. Reference families are
 * not silently substituted for an input tile set. Source gaps stay visible.
 */
import {PolyhedralModel} from '../../assets/polyhedral-exact-search.js';
import {Golden as G} from '../../assets/golden-field.js';
import {WANG21} from '../../assets/aperiodic-wang-cubes.js';
export const SEARCH_MODELS={
 ammann:{rules:'Supplied Ammann face dots',source:true,scope:'Supplied-rule Ammann geometric search; exact point values and optional validated learning.'},
 danzer:{rules:'Danzer blue-edge reflection rule',source:true,scope:'Exact ABCK carriers, both hands; whole-facet growth with the documented blue-edge reflection rule. No infinite-extension certificate.'},
 danzerOcta:{rules:'Danzer compound face-to-face rule',source:true,scope:'Exact nonconvex compounds; whole-facet attachments and exact boundary-feature contacts. The source identifies the face-to-face system with ABCK tilings.'},
 wang:{rules:'Fixed-frame Wang face symbols',source:true,scope:'All 21 source-transcribed cube labels, fixed orientation and integer translations. Source transcription inconsistencies remain documented; no independent aperiodicity proof is claimed.'},
 socolar:{rules:'Geometry only · source markings not ported',source:false,scope:'Geometry-only carrier experiment. All exact rigid full-facet attachments are enumerated; the Socolar–Steinhardt face decorations are not enforced. Periodic or non-quasicrystalline patches may occur.'},
 goodman:{rules:'Geometry only · boundary colours not ported',source:false,scope:'Geometry-only I/L carrier experiment. Disconnected interiors are retained. The source boundary-colour function is not enforced; no aperiodicity claim.'},
 goodmanCross:{rules:'Geometry only · cross colours not ported',source:false,scope:'Geometry-only connected carriers, retaining X0/X1 inventory identities. Source boundary markings are not enforced; no aperiodicity claim.'},
 scd:{rules:'Geometry only · discrete screw layers',source:false,scope:'Proper copies of the exact rational SCD biprism. This whole-facet control does not enumerate the continuously sliding, partly face-overlapping layers of the full source system. An exhausted control is not a non-tiling claim for SCD.'},
 taylor:{rules:'Original print mesh · display only',source:false,displayOnly:true,scope:'The original attributed print mesh is retained for inspection. It has open and non-manifold boundary edges; no solid-volume search or replacement proxy is used.'}
};
export const CONCRETE_SYSTEMS=Object.keys(SEARCH_MODELS).filter(id=>!SEARCH_MODELS[id].displayOnly);
export function wangTiles(){
 const vertices=Array.from({length:8},(_,m)=>[0,1,2].map(i=>[String((m>>i)&1),'0','1'])),faces=[[0,4,6,2],[1,3,7,5],[0,1,5,4],[2,6,7,3],[0,2,3,1],[4,5,7,6]],order=[0,3,5,4,1,2],palette=['#dc9c64','#68b6af','#bba1d5','#7ba2cc','#c7bf77','#df8f9b','#a1b98a'],symbols=[...new Set(WANG21.flatMap(t=>t.colors.map(v=>JSON.stringify(v))))].sort();
 return WANG21.map(w=>({id:w.id,name:`Cube ${w.id}`,vertices,faces,faceSymbols:order.map(j=>w.colors[j]),faceColors:order.map(j=>palette[symbols.indexOf(JSON.stringify(w.colors[j]))%palette.length]),pointMarkings:faces.map((f,i)=>({point:[0,1,2].map(axis=>new G(f.reduce((s,j)=>s+BigInt(vertices[j][axis][0]),0n),0n,4n).toJSON()),components:{symbol:w.colors[order[i]]}}))}));
}
export function createSearchModel(system,data,{geometryOnly=false}={}){
 const entry=SEARCH_MODELS[system];if(!entry||entry.displayOnly||system==='ammann')throw Error('No generic concrete model for this selection');
 let tiles=system==='wang'?wangTiles():data.systems[system];
 if(!tiles?.length)throw Error('The selected reference does not specify concrete tiles');
 const colors=['#e1b679','#68b5af','#aa92d2','#84a7cd','#c4c073'];tiles=tiles.map((t,i)=>({...t,color:colors[i%colors.length],pointMarkings:system==='wang'&&!geometryOnly?t.pointMarkings:undefined}));
 return new PolyhedralModel({id:system,tiles,mode:geometryOnly?'geometry':system==='danzer'?'danzer':system==='wang'?'wang':'geometry',fixedFrame:system==='wang',mirrors:!['wang','scd','taylor'].includes(system),scope:geometryOnly&&entry.source?`Explicit unmarked control on the exact carriers. The ${entry.rules} are not enforced. Wang copies retain their fixed frame; other models enumerate rigid whole-facet attachments. No aperiodicity claim.`:entry.scope,proxy:!!entry.proxy});
}
