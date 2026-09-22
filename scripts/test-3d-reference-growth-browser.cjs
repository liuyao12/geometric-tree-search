const {chromium}=require('playwright'),assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8894';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{window.growthFrames=[];setInterval(()=>{const v=document.querySelector('.viewer');if(v?.dataset.searchPhase){const frame={phase:v.dataset.searchPhase,tiles:+v.dataset.placements};if(JSON.stringify(frame)!==JSON.stringify(window.growthFrames.at(-1)))window.growthFrames.push(frame);}},20);});
  await page.goto(base+'/3d-lattice-tiler/');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  assert.equal(await page.locator('#tile option').count(),40);assert.equal(await page.locator('#seed').inputValue(),'10');assert.equal(await page.locator('#targetTiles').inputValue(),'1000');assert.ok(await page.locator('#windowSettings').isHidden());assert.ok(await page.locator('#demoEvidence').isHidden());assert.ok(await page.locator('.marking-use').isDisabled());
  await page.fill('#targetTiles','30');await page.fill('#seconds','20');await page.click('.marking-new');
  await page.waitForFunction(()=>document.querySelector('.viewer').dataset.searchPhase==='corona');
  assert.ok(await page.locator('#markingLearning').isVisible());
  await page.waitForFunction(()=>document.querySelector('#status').textContent==='Marked growth checkpoint verified.',{},{timeout:40000});
  assert.match(await page.locator('#coverage').textContent(),/30 \/ 30 tiles.*frontier verified viable/);assert.ok(await page.locator('#markingLearning').isVisible());
  assert.ok((await page.evaluate(()=>growthFrames)).some(f=>f.phase==='corona'&&f.tiles>2));
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/reference-growth-v2.png'});
  await page.click('#run');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Comparison complete'),{},{timeout:100000});
  for(const id of ['free','gcts','rl','both'])assert.match(await page.locator('#lane-'+id).textContent(),/Growth checkpoint/);
  await page.click('#lane-free');assert.ok(await page.locator('#markings').isDisabled());assert.ok(await page.locator('#markingLearning').isVisible());assert.equal(await page.locator('#markingLearning').getAttribute('data-reference'),'true');
  const downloadPromise=page.waitForEvent('download');await page.click('#export');const download=await downloadPromise,stream=await download.createReadStream(),chunks=[];for await(const c of stream)chunks.push(c);const exported=JSON.parse(Buffer.concat(chunks));
  const results=exported.experiments.at(-1).results;
  for(const id of ['free','gcts','rl','both']){assert.equal(results[id].config.searchProtocol,'seed-growth');assert.equal(results[id].placements.length,30);assert.equal(results[id].verification.frontierViable,true);assert.equal(results[id].placements[0].generation,0);}
  assert.ok(results.free.model.orientations.every(o=>!o.marks?.length));assert.ok(results.gcts.model.orientations.some(o=>o.marks.length));assert.ok(results.gcts.marking.accepted);assert.equal(results.free.config.seed,results.gcts.config.seed);
  await page.goto(base+'/apps/3d-lattice-tiler/index.html');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));assert.ok(await page.locator('#growthSettings').isVisible());
  await page.goto(base+'/apps/3d-lattice-tiler/legacy.html?tile=cube');await page.waitForFunction(()=>document.querySelector('.marking-new')&&!document.querySelector('.marking-new').disabled);
  await page.fill('#maxTilesInput','12');await page.click('.marking-new');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Patch found'),{},{timeout:30000});
  assert.ok(await page.locator('#markingLearning').isVisible());assert.ok(await page.locator('#viewport').isVisible());assert.equal(await page.locator('#viewport').getAttribute('data-search-phase'),'tiling');
  assert.match(await page.locator('#strategyDescription').textContent(),/Seed-based point growth/);
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/reference-growth-v1.png'});
  assert.deepEqual(errors,[]);console.log('PASS both live growth UIs, training-to-marked-growth, four matched lanes, unmarked free-range, viable checkpoints and original catalogue.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
