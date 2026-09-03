// Run with CANVAS_MODULE pointing to @napi-rs/canvas if it is not installed locally.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { createCanvas } = require(process.env.CANVAS_MODULE || '@napi-rs/canvas');
const source = fs.readFileSync(new URL('../GCTS-I.html', import.meta.url), 'utf8');
const names = ['worldToScreen', 'drawLine', 'tracePolygon', 'drawMarkings',
  'drawExteriorMarkingPoints', 'drawTurtle', 'drawValues', 'drawFrontier',
  'hoverTooltipLayout', 'drawHoverTooltip', 'unionPaintBounds', 'paintBoundsIntersect',
  'pointPaintBounds', 'placementPaintBounds', 'transientPaintBounds', 'draw', 'formatFrontierPoint'];
const functions = names.map(name => {
  const match = source.match(new RegExp(`      function ${name}\\([^]*?\\n      }`));
  assert.ok(match, `Missing function ${name}`);
  return match[0];
}).join('\n');

function tile(x, y, id) {
  const vertices3d = [[x,y,0],[x+28,y,0],[x+28,y+28,0],[x,y+28,0]];
  return { orientation: { orientationIndex: id % 2, planeSign: id % 2 ? -1 : 1 },
    translation: [x,y,0], vertices3d, points: vertices3d.map(([x,y])=>({x,y})),
    occupancy: vertices3d.map(point=>({point,value:6})),
    markings: [{point:[x-12,y+14,0],component:0,value:1}, {point:[x+40,y+14,0],component:0,value:1}],
    markSegments: [{fromPoint:[x,y+14,0],toPoint:[x+28,y+14,0],
      displayFromPoint:[x-12,y+14,0],displayToPoint:[x+40,y+14,0],value:1}] };
}

let checks = 0;
for (const ratio of [1, 2]) {
  const canvas = createCanvas(640 * ratio, 480 * ratio);
  canvas.dataset = {};
  canvas.getBoundingClientRect = () => ({width:640,height:480});
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio,0,0,ratio,0,0);
  const state = {canvas,ctx,renderCache:null,visible:[],scale:1,offset:{x:25,y:25},
    showMarkings:true,markingRank:3,markingExtension:1,latticeToggle:{checked:true},
    seedOrientationIndex:0,trialGhost:null,hoveredPoint:null,hoverKey:null,
    shownTiles:1,statusText:'test',statusReadout:{textContent:''},
    tileColors:{directFill:'rgba(145,195,180,0.6)',reflectedFill:'rgba(160,175,220,0.6)',directStroke:'#245',reflectedStroke:'#426'},
    markValueColors:{positive:'#bc6530',negative:'#357abb'},
    document:{createElement:()=>createCanvas(1,1)},window:{devicePixelRatio:ratio,requestAnimationFrame:()=>0},
    key3:p=>p.join(','),markingKey:e=>`${e.point.join(',')}|${e.component}`,
    projectA2:p=>({x:p[0],y:p[1]}),usingSublattice:()=>false,updateTextWrap:()=>{},
    clamp:(v,a,b)=>Math.max(a,Math.min(b,v))};
  state.visiblePlacements=()=>state.visible;
  state.refreshHoveredPoint=sums=>{state.hoveredPoint=state.hoverKey?sums.get(state.hoverKey):null;};
  state.hoverLinesForPoint=e=>[`t=${e.value}`, `point ${e.point.join(',')}`];
  state.drawGridLines=()=>{ctx.save();ctx.strokeStyle='#ddd';for(let x=0;x<640;x+=28){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,480);ctx.stroke();}ctx.restore();};
  vm.createContext(state);
  vm.runInContext(functions,state);
  function verify(label, expectIncremental) {
    state.shownTiles=state.visible.length;
    state.draw();
    if (expectIncremental !== undefined) assert.equal(canvas.dataset.renderMode,expectIncremental?'incremental':'full',label);
    const painted=Number(canvas.dataset.paintedTiles);
    const actual=ctx.getImageData(0,0,canvas.width,canvas.height).data;
    state.renderCache=null;
    state.draw();
    const expected=ctx.getImageData(0,0,canvas.width,canvas.height).data;
    let different=0, maxDifference=0;
    for(let i=0;i<actual.length;i++){const d=Math.abs(actual[i]-expected[i]);if(d>2)different++;maxDifference=Math.max(maxDifference,d);}
    if(different){const pixels=[];for(let i=0;i<actual.length&&pixels.length<10;i+=4){if([0,1,2,3].some(k=>Math.abs(actual[i+k]-expected[i+k])>2))pixels.push({x:(i/4)%canvas.width,y:Math.floor(i/4/canvas.width),actual:Array.from(actual.slice(i,i+4)),expected:Array.from(expected.slice(i,i+4))});}console.log(label,pixels);}
    assert.equal(different,0,`${label}, DPR ${ratio}: ${different} channels differ; max ${maxDifference}`);
    checks++;
    return painted;
  }
  state.visible=[tile(0,0,0)];verify('seed',false);
  for(let i=1;i<45;i++){
    state.visible.push(tile((i%9)*28,Math.floor(i/9)*28,i));
    verify(`append ${i}`,true);
  }
  state.visible.push(tile(252,140,46));
  assert.ok(verify('local paint count',true)<state.visible.length/2,'An append should paint fewer than half the tiles');
  state.hoverKey='28,28,0';verify('hover on',true);
  state.hoverKey='112,112,0';verify('hover move',true);
  state.hoverKey=null;verify('hover off',true);
  state.trialGhost={placement:tile(280,140,0),valid:true};verify('ghost on',true);
  state.trialGhost={placement:tile(308,140,0),valid:false};verify('ghost move',true);
  state.trialGhost=null;verify('ghost off',true);
  state.visible.pop();verify('backtrack',false);
  state.visible[state.visible.length-1]=tile(280,168,0);verify('branch replacement',false);
  state.offset.x+=30;verify('pan',false);
  state.scale=0.6;verify('zoom out',false);
  state.visible.push(tile(252,168,2));verify('append zoomed out',true);
  state.scale=1.75;verify('zoom in',false);
  state.showMarkings=false;verify('hide markings',false);
  state.showMarkings=true;state.markingRank=1;verify('rank 1',false);
  state.visible.push(tile(280,196,3));verify('rank 1 append',true);
  state.latticeToggle.checked=false;verify('hide grid',false);
  verify('unchanged frame',true);
  state.visible.push(tile(1000,1000,0));assert.equal(verify('offscreen append',true),0);
}
console.log(`PASS: ${checks} incremental/full pixel comparisons, including overlap, hover, ghosts, view changes, and rollback.`);
