const {chromium}=require('playwright'),assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8894';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/3d-lattice-tiler/?experiment=window');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.fill('#seconds','15');await page.click('#run');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Free-range · cold'),{},{timeout:35000});
  const inset=page.locator('#markingLearning');assert.ok(await inset.isVisible());assert.equal(await inset.getAttribute('data-marking-lane'),'gcts');assert.equal(await inset.getAttribute('data-reference'),'true');
  assert.match(await page.locator('.marking-lane-context').textContent(),/Free-range uses no marking/);assert.match(await page.locator('.marking-meta').textContent(),/Validated/);
  await page.waitForFunction(()=>document.querySelector('#markings').disabled);
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/marking-during-free-range.png'});
  await page.click('#lane-gcts');assert.ok(await inset.isVisible());assert.equal(await inset.getAttribute('data-reference'),'false');assert.ok(await page.locator('#markings').isEnabled());
  await page.click('#lane-free');assert.ok(await inset.isVisible());assert.equal(await inset.getAttribute('data-reference'),'true');
  await page.click('#showLearning');assert.ok(await inset.isHidden());await page.click('#showLearning');assert.ok(await inset.isVisible());
  await page.click('#stop');await page.waitForFunction(()=>document.querySelector('#stop').disabled);assert.ok(await inset.isVisible());assert.deepEqual(errors,[]);
  console.log('PASS learned inset persists through automatic and manual lane changes; unmarked main model remains unmarked; toggling and cancellation preserve the reference.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
