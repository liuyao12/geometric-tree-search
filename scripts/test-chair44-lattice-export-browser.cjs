const {chromium}=require('playwright'),assert=require('node:assert/strict'),path=require('node:path');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8765';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH??'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--enable-webgl','--use-gl=angle','--use-angle=swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/v2/app.js?*',async route=>{const response=await route.fetch();await route.fulfill({response,body:await response.text()+`\nwindow.exportCheck={model:()=>models.preview,free:()=>results.free,busy:()=>busy};`});});
  await page.goto(base+'/3d-reptiles/?v=chair-export');
  assert.ok(await page.getByRole('link',{name:'Export exact tile JSON'}).getAttribute('download')!==null);
  const download=await page.request.get(base+'/3d-reptiles/chair/chair44-exact-points.json?v=chair-export');assert.equal(download.status(),200);assert.equal((await download.json()).point_model.format,'gcts-exact-points-v1');
  await page.getByRole('link',{name:'Open in lattice tiler'}).click();
  await page.waitForFunction(()=>window.exportCheck?.model(),null,{timeout:30000});
  assert.equal(await page.locator('#tile').inputValue(),'chair44_relief');
  assert.equal(await page.locator('#mirrors').isChecked(),false);assert.ok(await page.locator('#mirrors').isDisabled());assert.ok(await page.locator('#probe').isDisabled());
  assert.ok((await page.locator('#tileEvidence').getAttribute('href')).includes('/geometric-tree-search/')||base.includes('127.0.0.1'));
  const size=await page.evaluate(()=>{const m=exportCheck.model();return [m.capacity,m.orientations.length,m.orientations[0].cells.length];});assert.deepEqual(size,[18,24,475]);
  await page.locator('#points').click(); // Hide the domain samples for the geometry screenshot.
  await page.screenshot({path:'/tmp/chair44-lattice-import.png'});
  await page.fill('#targetTiles','8');await page.fill('#seconds','60');await page.click('#run');
  await page.waitForFunction(()=>exportCheck.free()?.result==='growth_checkpoint',null,{timeout:90000});
  const result=await page.evaluate(()=>exportCheck.free());assert.equal(result.placements.length,8);assert.ok(result.verification.ok);assert.ok(result.stats.backtracks>0);
  await page.click('#stop');await page.waitForFunction(()=>!exportCheck.busy());
  await page.selectOption('#tile','cube');await page.waitForFunction(()=>exportCheck.model()?.name==='Cube');assert.ok(await page.locator('#mirrors').isEnabled());
  await page.locator('details').filter({has:page.locator('#custom')}).locator('summary').click();
  await page.setInputFiles('#customFile',path.resolve(__dirname,'../3d-reptiles/chair/chair44-exact-points.json'));
  await page.waitForFunction(()=>document.querySelector('#tile').value==='custom'&&exportCheck.model()?.exactPointImport);
  assert.deepEqual(await page.evaluate(()=>{const m=exportCheck.model();return [m.capacity,m.orientations.length,m.orientations[0].cells.length];}),size);
  assert.ok(await page.locator('#probe').isDisabled());assert.ok(await page.locator('#mirrors').isDisabled());
  await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual(errors,[]);console.log('PASS live export link, exact preset, eight-tile growth/rollback, stop, JSON file import, reflection/probe guards, cube regression, and mobile layout.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
