// Render the exact live relief, one slow full turn, for GIF encoding.
const {createServer}=require('node:http');
const {readFileSync,mkdirSync}=require('node:fs');
const {resolve,extname}=require('node:path');
const {chromium}=require('playwright');
const root=resolve(__dirname,'..'),out=resolve(process.argv[2]??'/tmp/chair-rotation-frames');
const html=`<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;background:#edf1ef;width:720px;height:720px;overflow:hidden}
canvas{position:absolute;inset:0}h1{position:absolute;top:36px;width:100%;margin:0;text-align:center;color:#24443d;font:500 25px Georgia,serif;z-index:1}
</style><script type="importmap">{"imports":{"three":"/3d-reptiles/vendor/three.module.min.js"}}</script></head>
<body><h1>3d aperiodic monotile: chair44</h1><script type="module">
import * as THREE from 'three';
import {makeReliefVisual} from '/3d-reptiles/chair/relief-visual.js';
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setSize(720,720);renderer.setPixelRatio(1);document.body.appendChild(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color(0xedf1ef);
scene.add(new THREE.HemisphereLight(0xffffff,0x72877e,1.5));
const light=new THREE.DirectionalLight(0xffffff,2.2);light.position.set(4,8,7);scene.add(light);
const camera=new THREE.PerspectiveCamera(35,1,.01,100);
camera.position.set(5.3,3.9,5.9);camera.lookAt(0,.12,0);
const turn=new THREE.Group(),tile=makeReliefVisual([{variantId:0,origin:[0,0,0]}]);
tile.group.position.set(-1,-1,-1);turn.add(tile.group);scene.add(turn);
window.drawFrame=i=>{turn.rotation.y=2*Math.PI*i/450;renderer.render(scene,camera);};
window.drawFrame(0);window.ready=true;
</script></body></html>`;
(async()=>{
 mkdirSync(out,{recursive:true});
 const server=createServer((req,res)=>{try{
  const path=new URL(req.url,'http://localhost').pathname;
  if(path==='/render'){res.setHeader('Content-Type','text/html');res.end(html);return;}
  const file=resolve(root,'.'+decodeURIComponent(path));if(!file.startsWith(root+'/'))throw Error('Invalid path');
  res.setHeader('Content-Type',extname(file)==='.js'?'text/javascript':'application/octet-stream');res.end(readFileSync(file));
 }catch{res.writeHead(404);res.end();}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH??'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--enable-webgl','--use-gl=angle','--use-angle=swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:720,height:720}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:'+server.address().port+'/render');await page.waitForFunction(()=>window.ready);
  for(let i=0;i<450;i++){
   await page.evaluate(i=>window.drawFrame(i),i);await page.screenshot({path:resolve(out,String(i).padStart(4,'0')+'.png')});
   if(i%90===0)console.log('Rendered',i,'of 450 frames');
  }
  if(errors.length)throw Error(errors.join('\n'));console.log('Rendered 30-second seamless turn to',out);
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
