const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.GCTS_TEST_URL??'http://127.0.0.1:8893';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 for(const legacy of [false,true]){
  await page.goto(base+(legacy?'/apps/3d-lattice-tiler/legacy.html?tile=cube':'/3d-lattice-tiler/?catalogue=all'));
  if(!legacy){await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));await page.selectOption('#tile','cube');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));}
  await page.waitForFunction(()=>document.querySelector('.marking-new')&&!document.querySelector('.marking-new').disabled);
  if(legacy)await page.fill('#maxTilesInput','8');
  assert.ok(await page.locator('.marking-continue').isHidden());
  await page.fill(legacy?'#markingPairBudget':'#pairBudget','1');
  await page.click('.marking-new');
  await page.waitForFunction(()=>!document.querySelector('.marking-continue').hidden&&!document.querySelector('.marking-continue').disabled);
  assert.ok(await page.locator('#markingLearning').isVisible());assert.ok(await page.locator('.marking-use').isDisabled(),'Unknowns cannot be activated');
  assert.match(await page.locator('.marking-progress').textContent(),/not activated/);
  await page.fill(legacy?'#markingPairBudget':'#pairBudget','500');
  await page.click('.marking-continue');
  await page.waitForFunction(()=>!document.querySelector('.marking-use').disabled);
  assert.ok(await page.locator('#markingLearning').isVisible(),'Accepted continuation tiles with the marking inset visible');
  assert.ok(await page.locator('.marking-continue').isHidden());
  const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('gcts-3d-markings-v1')).at(-1).marking);
  assert.ok(saved.continued);assert.equal(saved.counts.unresolved,0);assert.equal(saved.totalPairs,26);assert.ok(saved.trainingMs>saved.elapsedMs);
  await page.locator('.marking-inspection').evaluate(e=>e.open=true);assert.match(await page.locator('.marking-detail').textContent(),/accepts 26\/26/);
  console.log(`${legacy?'V1':'V2'}: incomplete run, continuation, accepted browser-local marking, automatic tiling passed`);
  await page.evaluate(()=>localStorage.clear());
 }
 // A worker may deliver a newer corona frame before an update is painted.
 const preview=await page.evaluate(async()=>{
  const {MarkingPreview}=await import(new URL('./marking-preview.js',location.href).href);
  const {prepareModel}=await import(new URL('./v2/model.js',location.href).href);
  const host=document.createElement('div'),p=new MarkingPreview(host);p.reset(prepareModel({tile:'cube',radius:1}));
  p.accept({type:'marking-learning',phase:'corona',totalPairs:26,pairs:2,counts:{valid:2},snapshot:{fields:[[{pos:[0,0,0],component:0,value:7}]],extent:1,counts:{valid:2},positivePassed:2,points:1,values:1}});
  return {value:p.snapshot.fields[0][0].value,status:p.status.textContent,detail:p.detail.textContent};
 });
 assert.equal(preview.value,7);assert.match(preview.status,/26 pairs/);assert.match(preview.detail,/accepts 2\/2/);
 assert.deepEqual(errors,[]);console.log('PASS coalesced live marking frames and no page errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
