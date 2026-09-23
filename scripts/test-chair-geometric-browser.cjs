const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const base=process.env.CHAIR_TEST_URL??'http://127.0.0.1:8765/3d-reptiles/';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),args:['--enable-webgl','--use-gl=angle','--use-angle=swiftshader']});
 try {
  const page=await browser.newPage({reducedMotion:'reduce',viewport:{width:1440,height:1100}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/chair/app.js?*',async route=>{
   const response=await route.fetch();await route.fulfill({response,body:(await response.text())+`
    window.geomCheck={
     read:()=>({rule:growthState.rule,count:growthState.placements.length,branches:growthState.branchDecisions,
      backtracks:growthState.solverBacktracks,pending:searchPending,running:autoRun,complete:growthState.complete,
      history:growthState.history.length,status:growthState.status}),
     save(){this.state=growthState;this.poses=JSON.stringify(growthState.placements);},
     same(){return this.state===growthState;},
     samePoses(){return this.poses===JSON.stringify(growthState.placements);},
     cancel(){runButton.click();const wasPending=searchPending;runButton.click();return {wasPending,pending:searchPending,running:autoRun};}
    };`});
  });
  await page.goto(base);await page.waitForFunction(()=>window.geomCheck);
  assert.equal((await page.evaluate(()=>geomCheck.read())).rule,'relief-tetra');
  await page.locator('#apply-one-button').click();await page.waitForFunction(()=>!geomCheck.read().pending);
  await page.evaluate(()=>geomCheck.save());
  assert.deepEqual(await page.evaluate(()=>geomCheck.cancel()),{wasPending:true,pending:false,running:false});
  await page.waitForTimeout(500);
  assert.equal(await page.evaluate(()=>geomCheck.samePoses()),true,'Cancelled worker must not deliver a late placement');
  await page.locator('#back-button').click();assert.equal(await page.evaluate(()=>geomCheck.same()),true);
  await page.getByRole('button',{name:'Arrows',exact:true}).click();
  assert.equal((await page.evaluate(()=>geomCheck.read())).rule,'relief-tetra','Display does not substitute arrow matching');
  await page.locator('#run-button').click();
  await page.waitForFunction(()=>geomCheck.read().complete&&!geomCheck.read().running,{},{timeout:120000});
  const result=await page.evaluate(()=>geomCheck.read());
  assert.equal(result.count,64);assert.equal(result.branches,4);assert.equal(result.backtracks,2);
  assert.equal(await page.locator('#branch-value').textContent(),'4');assert.equal(await page.locator('#backtrack-value').textContent(),'2');
  await page.getByRole('button',{name:'Relief',exact:true}).click();
  assert.match(await page.locator('#matching-description').textContent(),/exact tetrahedral geometry/);
  await page.screenshot({path:'/tmp/chair-tetra-growth.png'});
  await page.locator('#back-button').click();assert.equal(await page.evaluate(()=>geomCheck.same()),true);
  assert.deepEqual(errors,[]);
  console.log('Passed tetrahedral worker: 64 tiles, 4 branches, 2 backtracks, cancellation, grouped Undo, and display/rule independence.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
