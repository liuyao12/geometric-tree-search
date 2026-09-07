const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{
    window.structuralEvents=[];const NativeWorker=window.Worker;
    window.Worker=class extends NativeWorker {
      constructor(...args){super(...args);this.addEventListener('message',e=>{
        if(['mode-paused','series-finished'].includes(e.data.type))window.structuralEvents.push({type:e.data.type,mode:e.data.mode??e.data.result?.mode});
      });}
    };
  });
  await page.goto(process.argv[2]||'http://localhost:8769/3d-lattice-tiler/');
  await page.locator('#systemTileList button').filter({hasText:'Size-9 Candidate 11364'}).waitFor();
  if(!(await page.locator('#selectedTiles').textContent()).includes('11364'))await page.locator('#systemTileList button').filter({hasText:'Size-9 Candidate 11364'}).click();
  await page.locator('input[name="criterion"][value="count"]').check();
  await page.locator('#maxTilesInput').fill('1');
  await page.locator('#timeCapInput').evaluate(el=>{el.value='1';el.dispatchEvent(new Event('change',{bubbles:true}));});
  await page.locator('#runButton').click();
  await page.waitForFunction(()=>['translational','isohedral'].every(mode=>window.structuralEvents.some(e=>e.type==='mode-paused'&&e.mode===mode)),{timeout:15000});
  console.log('Pause state:',await page.locator('#runButton').textContent(),await page.evaluate(()=>window.structuralEvents));
  await page.locator('#runButton').filter({hasText:'Continue'}).click();
  await page.waitForFunction(()=>['translational','isohedral'].every(mode=>window.structuralEvents.filter(e=>e.type==='mode-paused'&&e.mode===mode).length>=2),{timeout:15000});
  const events=await page.evaluate(()=>window.structuralEvents);
  assert.ok(!events.some(e=>e.type==='series-finished'&&['translational','isohedral'].includes(e.mode)));
  assert.deepEqual(errors,[]);console.log('Browser: both structural lanes continue discovery past the one-tile display goal and survive two clock pauses with Continue.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
