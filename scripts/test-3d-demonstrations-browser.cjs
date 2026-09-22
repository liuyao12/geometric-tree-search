const {chromium}=require('playwright'),assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8894';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/3d-lattice-tiler/');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  assert.equal(await page.locator('#tile option').count(),40);assert.equal(await page.locator('#radius').inputValue(),'18');assert.equal(await page.locator('#seconds').inputValue(),'120');assert.equal(await page.locator('#markingExtent').inputValue(),'0');assert.ok(await page.locator('#mirrors').isChecked());assert.equal(await page.locator('#markings').getAttribute('aria-pressed'),'false');assert.equal(await page.locator('#points').getAttribute('aria-pressed'),'false');assert.ok(await page.locator('#reference').isHidden());
  const ids=await page.locator('#tile option').evaluateAll(options=>options.map(o=>o.value));
  for(const id of ['a2_turtle_prism','1_cross','double_ring','tuning_fork','mathematica_16_vertex','rhombic','scd_conway','barlow_hcp'])assert.ok(ids.includes(id),id);
  assert.ok(ids.every(id=>!id.startsWith('polycube_')),'No search-generated tiles');
  await page.selectOption('#tile','cube');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));assert.equal(await page.locator('#radius').inputValue(),'3');
  await page.selectOption('#tile','a2_hat_prism');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.waitForFunction(()=>document.querySelectorAll('#demoRows tr').length===3);
  assert.ok(await page.locator('.marking-use').isDisabled(),'No bundled learned marking');
  await page.selectOption('#radius','3');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));await page.click('#useDemonstration');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));assert.equal(await page.locator('#radius').inputValue(),'18');
  await page.click('.marking-new');await page.waitForFunction(()=>document.querySelector('#status').textContent==='Marked window verified.',{},{timeout:135000});
  assert.match(await page.locator('#coverage').textContent(),/2054 \/ 2054/);assert.equal(await page.locator('.viewer').getAttribute('data-search-phase'),'tiling');assert.ok(await page.locator('#markingLearning').isVisible());
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/demonstration-desktop.png',fullPage:true});
  if(process.env.GCTS_COMPARE_SMOKE){
   await page.fill('#seconds','20');await page.click('#run');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Comparison complete'),{},{timeout:100000});
   assert.match(await page.locator('#verdict').textContent(),/at least.*faster/);console.log('Browser comparison:',await page.locator('#verdict').textContent());
  }
  await page.goto(base+'/3d-lattice-tiler/?catalogue=all');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));assert.equal(await page.locator('#tile option').count(),54);assert.ok(await page.locator('#reference').isVisible());
  await page.selectOption('#tile','cube');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));assert.ok(await page.locator('#radius option[value="18"]').isDisabled());
  await page.goto(base+'/apps/3d-lattice-tiler/index.html');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));assert.equal(await page.locator('#tile option').count(),40);assert.equal(await page.locator('#radius').inputValue(),'18');
  await page.selectOption('#radius','1');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));await page.fill('#seconds','1');await page.click('#run');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Comparison complete'),{},{timeout:25000});
  assert.equal(await page.locator('#lanes .lane').count(),4);
  await page.goto(base+'/apps/3d-lattice-tiler/legacy.html');
  await page.waitForFunction(()=>document.querySelectorAll('.figure-card-title').length>20);
  assert.equal(await page.locator('.figure-card-title').filter({hasText:/p(?:9|10)-\d+/}).count(),0);
  assert.ok(await page.locator('.figure-card-title').filter({hasText:'Buckled Ring'}).count()>0);
  assert.deepEqual(errors,[]);console.log('PASS curated defaults, measured settings, fresh learned large-window tiling, research escape, both entry URLs.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
