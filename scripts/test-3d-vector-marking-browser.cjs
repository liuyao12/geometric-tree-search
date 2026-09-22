const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8894';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/3d-lattice-tiler/?experiment=window&catalogue=all');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  assert.ok(await page.locator('.marking-use').isDisabled());
  await page.selectOption('#tile','a2_turtle_prism');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.check('#mirrors');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.fill('#seconds','60');await page.click('.marking-new');
  await page.waitForFunction(()=>document.querySelector('#status').textContent==='Marked window verified.',{},{timeout:75000});
  const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('gcts-3d-markings-v1')).at(-1).marking);
  assert.equal(saved.componentCount,2);assert.equal(saved.negativeBlocked,206);assert.equal(saved.positivePassed,41);
  await page.locator('.marking-inspection').evaluate(e=>e.open=true);
  assert.match(await page.locator('.marking-detail').textContent(),/2 components/);
  // Inspect the shared preview directly so coincident 3D projections do not
  // make a test depend on which projected point the mouse happens to hit.
  const preview=await page.evaluate(async()=>{
   const {MarkingPreview}=await import(new URL('marking-preview.js?v=20260921-vector-learning',document.baseURI));
   const entry=JSON.parse(localStorage.getItem('gcts-3d-markings-v1')).at(-1);
   const host=document.createElement('div');host.id='vector-preview-control';document.body.append(host);
   const view=new MarkingPreview(host);view.reset(entry.domain);view.accept({type:'marking-learned',marking:entry.marking});
   const m=entry.marking.fields[+view.select.value].find(m=>m.component===1);
   const hit=view.hits.find(h=>h.side==='marking'&&h.pos.join()===m.pos.join());
   const fields=entry.marking.fields[+view.select.value].filter(v=>v.pos.join()===m.pos.join());
   const expected=Array(entry.marking.componentCount).fill('*');for(const f of fields)expected[f.component]=f.value;
   const result={actual:hit.values,expected,text:hit.text};host.remove();return result;
  });
  assert.deepEqual(preview.actual,preview.expected);assert.ok(preview.actual.includes('*'));assert.match(preview.text,/m=\(.+, .+\)/);
  if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+'/vector-learning.png'});
  await page.reload();await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.selectOption('#tile','a2_turtle_prism');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.check('#mirrors');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  await page.click('.marking-use');await page.waitForFunction(()=>document.querySelector('#status').textContent==='Marked window verified.',{},{timeout:30000});
  assert.match(await page.locator('#inspection').textContent(),/Reused browser marking/);
  assert.deepEqual(errors,[]);console.log('PASS browser learns a two-component Turtle field, verifies marked tiling, shows the full vector with *, and reuses it after reload.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
