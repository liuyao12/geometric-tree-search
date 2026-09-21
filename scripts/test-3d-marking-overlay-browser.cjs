const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8893';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try {
 const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{const Original=Worker;window.workResults=[];window.Worker=class extends Original{constructor(...args){super(...args);this.addEventListener('message',({data})=>{if(data.type==='result')window.workResults.push(data);});}};});
 await page.goto(base+'/3d-lattice-tiler/');
 await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
 assert.ok(await page.locator('#markings').isDisabled());
 const findTooltip=(selector='#canvas canvas')=>page.evaluate(selector=>{
  const c=document.querySelector(selector),b=c.getBoundingClientRect(),tip=document.querySelector('.marking-tooltip');
  for(let y=25;y<b.height-10;y+=9)for(let x=10;x<b.width-10;x+=9){c.dispatchEvent(new PointerEvent('pointermove',{clientX:b.left+x,clientY:b.top+y}));if(!tip.hidden)return tip.textContent;}
  return null;
 },selector);
 for(const tile of ['a2_turtle_prism','a2_hat_prism']){
  await page.selectOption('#tile',tile);await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  if(!(await page.locator('#mirrors').isChecked())){await page.check('#mirrors');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));}
  await page.fill('#seconds','60');await page.click('.marking-new');
  await page.waitForFunction(()=>document.querySelector('#status').textContent==='Marked window verified.',{},{timeout:75000});
  assert.ok(await page.locator('#markings').isEnabled());assert.ok(await page.locator('#markingLearning').isHidden());
  const tip=await findTooltip();assert.ok(tip, 'Assigned values are inspectable');
  const match=tip.match(/^\((.*?)\) · m\[(\d+)\] = (\d+)\n(\d+) tile/);assert.ok(match,tip);
  const expected=await page.evaluate(({pos,component,value})=>{
   const r=window.workResults.at(-1);let count=0;
   for(const p of r.placements)for(const m of r.model.orientations[p.oi].marks??[]){if((m.component??0)===component&&m.pos.every((x,i)=>x+p.translation[i]===pos[i])){if(m.value!==value)throw Error('Wrong value in tooltip');count++;}}
   return count;
  },{pos:match[1].split(',').map(Number),component:+match[2],value:+match[3]});
  assert.equal(+match[4],expected);
  await page.click('#markings');assert.equal(await findTooltip(),null);await page.click('#markings');assert.ok(await findTooltip());
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+`/overlay-${tile}.png`});
  console.log(tile,tip.replace('\n','; '));
 }
 await page.selectOption('#tile','cube');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
 assert.ok(await page.locator('#markings').isDisabled());assert.ok(await page.locator('.marking-tooltip').isHidden());
 // Legacy browser transport uses a freshly validated, synthetic constant-zero
 // control. Production learning is still tested above and by the cube run here.
 await page.goto(base+'/apps/3d-lattice-tiler/legacy.html?tile=cube');
 await page.waitForFunction(()=>document.querySelector('.marking-new')&&!document.querySelector('.marking-new').disabled);
 await page.fill('#maxTilesInput','8');await page.click('.marking-new');
 await page.waitForFunction(()=>!document.querySelector('.marking-use').disabled);
 assert.ok(await page.locator('#markings').isDisabled(),'Production cube field is empty');
 await page.evaluate(()=>{
  const key='gcts-3d-markings-v1',entries=JSON.parse(localStorage.getItem(key));
  const entry=entries.find(e=>e.domain.orientations.length===1&&!e.domain.allowReflections);
  if(!entry)throw Error('Missing fresh cube control');
  entry.marking.fields=entry.domain.orientations.map(o=>o.cells.map(c=>({pos:c.pos,component:0,value:0})));
  localStorage.setItem(key,JSON.stringify([entry]));
 });
 await page.reload();await page.waitForFunction(()=>document.querySelector('.marking-use')&&!document.querySelector('.marking-use').disabled);
 await page.fill('#maxTilesInput','8');await page.click('.marking-use');
 await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Patch found'));
 assert.ok(await page.locator('#markings').isEnabled());
 const legacyTip=await findTooltip('#viewport canvas');assert.match(legacyTip,/m\[0\] = 0/);
 console.log('v1 validated control:',legacyTip.replace('\n','; '));
 if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/overlay-v1-control.png'});
 assert.deepEqual(errors,[]);console.log('PASS live Turtle/Hat learning, actual selected marking values/counts, toggles, and clearing on system change.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
