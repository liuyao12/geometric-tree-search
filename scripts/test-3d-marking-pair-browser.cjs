const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8893';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/3d-lattice-tiler/?experiment=window&catalogue=all');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
  for(const tile of ['a2_turtle_prism','a2_hat_prism']){
   await page.selectOption('#tile',tile);await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));
   if(!(await page.locator('#mirrors').isChecked())){await page.check('#mirrors');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));}
   await page.fill('#seconds','60');await page.click('.marking-new');
   await page.waitForFunction(()=>document.querySelector('#status').textContent==='Marked window verified.',{},{timeout:75000});
   assert.ok(await page.locator('#markingLearning').isVisible());
   await page.locator('.marking-inspection').evaluate(e=>e.open=true);
   const rows=await page.evaluate(()=>{
    const m=JSON.parse(localStorage.getItem('gcts-3d-markings-v1')).at(-1).marking;
    return {count:m.evidence.length,valid:m.evidence.findIndex(r=>r.status==='valid'),negative:m.evidence.findIndex(r=>{
     if(r.status!=='invalid')return false;
     const values=new Map();for(const p of r.pair)for(const v of m.fields[p.oi]){const key=v.pos.map((x,i)=>x+p.translation[i]).join()+':'+(v.component??0);if(values.has(key)&&values.get(key)!==v.value)return true;values.set(key,v.value);}return false;
    })};
   });
   assert.equal(await page.locator('.marking-pair option').count(),rows.count);assert.ok(rows.negative>=0);
   await page.selectOption('.marking-pair',String(rows.negative));
   assert.match(await page.locator('.marking-pair-detail').textContent(),/Invalid:.*rejects this pair \(correct\).*conflicts/);
   assert.ok(await page.locator('.marking-witness').isDisabled());
   await page.click('#showTiling');await page.click('#showLearning');await page.click('#showLearning');
   assert.equal(await page.locator('.marking-pair').inputValue(),String(rows.negative),'Selection survives repeated final events and view switching');
   if(process.env.GCTS_SCREENSHOTS)await page.screenshot({path:process.env.GCTS_SCREENSHOTS+`/pair-${tile}.png`});
   await page.selectOption('.marking-pair',String(rows.valid));
   assert.match(await page.locator('.marking-pair-detail').textContent(),/Valid: complete 1-corona with viable frontier.*accepts this pair \(correct\)/);
   assert.ok(await page.locator('.marking-witness').isEnabled());await page.uncheck('.marking-witness');await page.check('.marking-witness');
   await page.selectOption('.marking-pair','0');assert.ok(await page.locator('.marking-previous').isDisabled());
   await page.click('.marking-next');assert.equal(await page.locator('.marking-pair').inputValue(),'1');await page.click('.marking-previous');
   console.log(`${tile}: ${rows.count} browsable pairs, actual positive/negative marking decisions, witness toggle, stable selection`);
  }
  await page.evaluate(()=>localStorage.clear());
  await page.goto(base+'/apps/3d-lattice-tiler/legacy.html?tile=cube');
  await page.waitForFunction(()=>document.querySelector('.marking-new')&&!document.querySelector('.marking-new').disabled);
  await page.fill('#maxTilesInput','8');await page.fill('#markingPairBudget','1');await page.click('.marking-new');
  await page.waitForFunction(()=>!document.querySelector('.marking-continue').hidden&&!document.querySelector('.marking-continue').disabled);
  await page.locator('.marking-inspection').evaluate(e=>e.open=true);
  const unknown=await page.locator('.marking-pair option').evaluateAll(options=>options.find(o=>o.textContent.includes('unresolved')).value);
  await page.selectOption('.marking-pair',unknown);
  assert.match(await page.locator('.marking-pair-detail').textContent(),/Unresolved:.*not a validity label/);
  assert.ok(await page.locator('.marking-witness').isDisabled());assert.ok(await page.locator('.marking-use').isDisabled());
  await page.fill('#markingPairBudget','500');await page.click('.marking-continue');
  await page.waitForFunction(()=>!document.querySelector('.marking-use').disabled);
  await page.locator('.marking-inspection').evaluate(e=>e.open=true);assert.equal(await page.locator('.marking-pair option').count(),26);
  assert.match(await page.locator('.marking-pair-detail').textContent(),/Valid:.*accepts this pair \(correct\)/);
  assert.deepEqual(errors,[]);console.log('PASS V1 unknown labels, continuation and validated pair inspection; no page errors.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
