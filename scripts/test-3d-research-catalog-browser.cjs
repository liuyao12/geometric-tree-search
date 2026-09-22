const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8894';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/3d-lattice-tiler/?experiment=window&tile=polycube_p10_346304');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  assert.equal(await page.locator('#tile').inputValue(),'polycube_p10_346304');
  assert.equal(await page.locator('#tile option').count(),54);
  assert.equal(await page.locator('#tile optgroup[label="Unresolved polycube research"] option').count(),10);
  assert.match(await page.locator('#tileNote').textContent(),/1,846 remain unresolved/);
  assert.match(await page.locator('#tileEvidence').getAttribute('href'),/3d-viable-frontier-search.md/);
  assert.match(await page.locator('#domainBadge').textContent(),/Voxel centers/);
  assert.match(await page.locator('#radius option:checked').textContent(),/91 points/);
  assert.ok(await page.locator('#probe').isDisabled());assert.ok(await page.locator('.marking-use').isDisabled());
  await page.waitForFunction(()=>document.querySelector('#referenceRows').textContent.includes('Hat prism'));
  assert.equal(await page.locator('#referenceRows tr').count(),5);assert.ok(!(await page.locator('#referenceRows').textContent()).includes('p10-346304'));
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/research-catalog-v2.png'});
  await page.fill('#seconds','1');await page.fill('#pairBudget','1');await page.click('.marking-new');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Marking not activated'),{},{timeout:25000});
  assert.ok(await page.locator('.marking-use').isDisabled());
  await page.selectOption('#tile','polycube_p9_48258');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  assert.match(await page.locator('#tileNote').textContent(),/non-tiling proof/);
  await page.selectOption('#tile','cube');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  assert.ok(await page.locator('#probe').isEnabled());assert.ok(await page.locator('#tileEvidence').isHidden());assert.match(await page.locator('#radius option:checked').textContent(),/27 points/);
  await page.goto(base+'/apps/3d-lattice-tiler/legacy.html?tile=polycube_p10_346304');
  await page.waitForFunction(()=>document.querySelector('#candidateResearchDetail')?.textContent.includes('1,846 remain unresolved'),{},{timeout:30000});
  assert.match(await page.locator('#candidateResearchTitle').textContent(),/p10-346304.*Unresolved/);
  assert.ok(await page.locator('#candidateResearchDetail a').isVisible());
  assert.equal(await page.locator('.figure-card-title').filter({hasText:/p(?:9|10)-\d+/}).count(),14);
  const cross=page.locator('.figure-card').filter({hasText:'p9-48258'});assert.match(await cross.textContent(),/Grid obstruction/);
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/research-catalog-v1.png'});
  assert.deepEqual(errors,[]);console.log('PASS live research catalogue in both versions: 14 entries, evidence links, exact-model controls, cold unknown learning, old controls, historical table and no page errors.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
