const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(process.argv[2]||'http://localhost:8769/3d-lattice-tiler/');
  await page.getByRole('heading',{name:'Geometric research benchmarks · separate model',exact:true}).waitFor();
  for(const id of ['a2sa 10 76076','a2pair 20 4c8015f2f0fc','a2sa 10 65558']) {
   await page.locator('#systemTileList button').filter({hasText:id}).click();
   await page.locator('#candidateResearchDetail').filter({hasText:'interactive six lanes'}).waitFor();
   assert.ok((await page.locator('#selectedTiles').textContent()).includes(id));
   assert.equal(await page.locator('#runButton').textContent(),'Run');
  }
  assert.ok(!(await page.locator('#systemTileList').textContent()).includes('undefined'));
  await page.locator('input[name="criterion"][value="count"]').check();
  await page.locator('#maxTilesInput').fill('8');await page.locator('#runButton').click();
  await page.waitForFunction(()=>!document.querySelector('#growthChart').textContent.includes('No benchmark run yet')&&document.querySelector('#growthChart .plot-container'));
  await page.waitForTimeout(1500);
  assert.deepEqual(errors,[]);console.log('Browser: all three selections, scoped notes, Run reset and live six-lane chart passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
