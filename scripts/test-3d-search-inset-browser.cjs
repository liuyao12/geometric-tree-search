const {chromium}=require('playwright'),assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8894';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{window.searchFrames=[];setInterval(()=>{const v=document.querySelector('.viewer')??document.querySelector('#viewport');if(v?.dataset.searchPhase){const frame={phase:v.dataset.searchPhase,tiles:+v.dataset.placements,visible:!!v.getBoundingClientRect().height&&!v.hidden,inset:!document.querySelector('#markingLearning')?.hidden};if(JSON.stringify(frame)!==JSON.stringify(window.searchFrames.at(-1)))window.searchFrames.push(frame);}},20);});
  await page.goto(base+'/3d-lattice-tiler/?experiment=window&catalogue=all&tile=a2_turtle_prism');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.check('#mirrors');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.fill('#seconds','60');await page.click('.marking-new');
  await page.waitForFunction(()=>document.querySelector('.viewer').dataset.searchPhase==='corona'&&+document.querySelector('.viewer').dataset.placements>=2);
  assert.ok(await page.locator('.viewer').isVisible());assert.ok(await page.locator('#markingLearning').isVisible());
  const box=await page.locator('.viewer').boundingBox(),inset=await page.locator('#markingLearning').boundingBox();assert.ok(inset.width<box.width*.4);assert.ok(inset.x+inset.width<=box.x+box.width);assert.ok(inset.height<box.height*.75);
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/corona-main-v2.png'});
  await page.waitForFunction(()=>document.querySelector('#status').textContent==='Marked window verified.',{},{timeout:75000});
  assert.equal(await page.locator('.viewer').getAttribute('data-search-phase'),'tiling');assert.ok(await page.locator('#markingLearning').isVisible());assert.ok(await page.locator('#markings').isEnabled());
  const frames=await page.evaluate(()=>searchFrames);assert.ok(frames.filter(f=>f.phase==='corona').length>3);assert.ok(frames.every(f=>f.visible));
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/marked-main-v2.png'});
  await page.locator('.marking-inspection summary').click();await page.selectOption('.marking-pair','1');assert.equal(await page.locator('.viewer').getAttribute('data-search-phase'),'sample');
  await page.click('#showTiling');assert.equal(await page.locator('.viewer').getAttribute('data-search-phase'),'tiling');
  await page.click('#showLearning');assert.ok(await page.locator('#markingLearning').isHidden());assert.ok(await page.locator('.viewer').isVisible());await page.click('#showLearning');
  await page.setViewportSize({width:390,height:844});await page.locator('.viewer').scrollIntoViewIfNeeded();
  const mobile=await page.locator('.viewer').boundingBox(),small=await page.locator('#markingLearning').boundingBox();assert.ok(small.width<mobile.width*.5);assert.ok(small.height<=270);assert.ok(small.x>=mobile.x&&small.x+small.width<=mobile.x+mobile.width);
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/marked-main-mobile.png'});await page.setViewportSize({width:1440,height:1050});
  await page.goto(base+'/apps/3d-lattice-tiler/legacy.html?tile=polycube_p10_346304&time_limit=2');await page.waitForFunction(()=>document.querySelector('.marking-new')&&!document.querySelector('.marking-new').disabled);
  await page.fill('#markingPairBudget','1');await page.click('.marking-new');
  await page.waitForFunction(()=>document.querySelector('#viewport').dataset.searchPhase==='corona'&&+document.querySelector('#viewport').dataset.placements>=2,{},{timeout:20000});
  assert.ok(await page.locator('#viewport').isVisible());assert.ok(await page.locator('#markingLearning').isVisible());
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/corona-main-v1.png'});
  await page.goto(base+'/apps/3d-lattice-tiler/legacy.html?tile=cube');await page.waitForFunction(()=>document.querySelector('.marking-new')&&!document.querySelector('.marking-new').disabled);await page.fill('#maxTilesInput','8');await page.click('.marking-new');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Patch found'),{},{timeout:30000});
  assert.ok(await page.locator('#viewport').isVisible());assert.ok(await page.locator('#markingLearning').isVisible());assert.equal(await page.locator('#viewport').getAttribute('data-search-phase'),'tiling');
  await page.locator('.marking-inspection summary').click();await page.selectOption('.marking-pair','1');assert.equal(await page.locator('#viewport').getAttribute('data-search-phase'),'sample');await page.click('#showTiling');assert.equal(await page.locator('#viewport').getAttribute('data-search-phase'),'tiling');
  assert.deepEqual(errors,[]);console.log('PASS both main viewports show real corona frames, keep a small marking inset, automatically show marked tiling, and restore live search after pair inspection.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
