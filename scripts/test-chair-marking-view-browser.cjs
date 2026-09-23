const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const base = process.env.CHAIR_TEST_URL ?? 'http://127.0.0.1:8765/3d-reptiles/';

(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
    args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/chair/app.js?*', async route => {
      const response = await route.fetch();
      await route.fulfill({ response, body: (await response.text()) + `
        window.valueCheck = {
          read: () => ({ markingView, mode, generation, count: growthState.placements.length,
            running: autoRun, transitioning: Boolean(transition) }),
          remember() { this.growth = growthState; this.inflation = currentInflationState; },
          unchanged() { return this.growth === growthState && this.inflation === currentInflationState; },
          relief() {
            const relief = currentVisual.group.getObjectByName('chair44-relief');
            if (!relief) return null;
            const geometry = [...new Set(relief.children.filter(object => object.isMesh).map(object => object.geometry))];
            const edges = new Map(); let volume = 0;
            const key = p => p.map(v => Math.round(v * 1e6)).join(',');
            for (const mesh of geometry) {
              const positions = mesh.getAttribute('position');
              for (let i = 0; i < positions.count; i += 3) {
                const points = [0, 1, 2].map(offset => [positions.getX(i + offset), positions.getY(i + offset), positions.getZ(i + offset)]);
                const [a,b,c] = points;
                volume += (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;
                for(let j=0;j<3;j++) {
                  const a=key(points[j]),b=key(points[(j+1)%3]),id=[a,b].sort().join('|');
                  const edge=edges.get(id)??{count:0,balance:0};edge.count++;edge.balance+=a<b?1:-1;edges.set(id,edge);
                }
              }
            }
            return {blueCreases:relief.getObjectByName('chair44-relief-blue-creases').geometry.getAttribute('position').count/2,
              visible:relief.visible,protrusions:relief.userData.protrusions,indents:relief.userData.indents,volume,
              badEdges:[...edges.entries()].filter(([,edge])=>edge.count!==2||edge.balance!==0).slice(0,12),
              closed:[...edges.values()].every(edge=>edge.count===2&&edge.balance===0),
              flatBodyVisible:currentVisual.group.children.some(object=>object.userData.flatChairBody&&object.visible)};
          },
          highlight() {
            let bright = 0, dim = 0;
            for (const visual of new Set([currentVisual, transition?.from, transition?.to])) {
              if (!visual) continue;
              const directions = new Set(visual.chairs.map(chair => chair.orientation));
              for (const name of ['chair44-arrows', 'chair44-relief']) {
                const group = visual.group.getObjectByName(name);
                if (!group) continue;
                const seen = new Set();
                group.traverse(object => {
                  const material = object.material;
                  if (!material) return;
                  const orientation = material.userData.orientation;
                  if (!directions.has(orientation)) throw Error('Marking lost its tile orientation');
                  seen.add(orientation);
                  const selected = selectedChairOrientation === null || orientation === selectedChairOrientation;
                  const factor = selected ? 1 : .12;
                  const edge = visual.chairs.find(chair => chair.orientation === orientation).edgeMaterial;
                  const ratio = material.opacity / material.userData.baseOpacity;
                  const edgeRatio = edge.opacity / edge.userData.baseOpacity;
                  if (Math.abs(ratio - edgeRatio) > 1e-10 || material.userData.highlightFactor !== factor)
                    throw Error('Markings must dim with their tile edges, including transition opacity');
                  if (selected) bright++; else dim++;
                });
                if (seen.size !== directions.size) throw Error('Missing marking orientation batch');
              }
            }
            return { bright, dim, selected: selectedChairOrientation };
          },
          check() {
            return [...new Set([currentVisual, transition?.from, transition?.to])].filter(Boolean).map(visual => {
              return { arrows: visual.group.getObjectByName('chair44-arrows').visible,
                relief: visual.group.getObjectByName('chair44-relief')?.visible ?? false };
            });
          }
        };
      ` });
    });
    await page.goto(base);
    await page.waitForFunction(() => window.valueCheck);
    const arrows = page.getByRole('button', { name: 'Arrows', exact: true });
    const relief = page.getByRole('button', { name: 'Relief', exact: true });
    assert.deepEqual(await page.evaluate(() => valueCheck.check()), [{ arrows: true, relief: false }]);
    assert.deepEqual(await page.locator('.marking-toggle button').allTextContents(), ['Arrows', 'Relief']);
    assert.equal(await page.locator('main > section').count(), 1);
    assert.equal(await page.locator('main > footer').count(), 0);
    assert.equal(await page.locator('.orientation-panel .scene-citation a').first().getAttribute('href'), 'https://arxiv.org/abs/2609.24779');
    await page.screenshot({ path: '/tmp/chair-half-arrows.png' });
    await page.evaluate(() => valueCheck.remember());
    const graph = page.locator('#orientation-plot');
    await graph.press('ArrowRight'); // Select a different direction before relief is created.
    assert.ok((await page.evaluate(() => valueCheck.highlight())).dim > 0);
    await relief.click();
    assert.ok((await page.evaluate(() => valueCheck.highlight())).dim > 0);
    await graph.press('Escape');
    assert.equal((await page.evaluate(() => valueCheck.highlight())).dim, 0);
    let reliefState = await page.evaluate(() => valueCheck.relief());
    assert.equal(reliefState.visible, true);
    assert.equal(reliefState.blueCreases, 8 * 14, 'Each blue pair has a joined ramp without a dividing crease');
    assert.equal(reliefState.flatBodyVisible, false);
    assert.equal(reliefState.closed, true, 'The panel cutouts and relief sides form a closed surface');
    assert.ok(Math.abs(reliefState.volume - 7) < 1e-5);
    assert.equal(reliefState.protrusions, 16); assert.equal(reliefState.indents, 16);
    assert.equal(await page.locator('#relief-legend').isVisible(), true);
    await page.screenshot({ path: '/tmp/chair-relief-single.png' });
    await arrows.click();
    assert.equal(await arrows.getAttribute('aria-pressed'), 'true');
    assert.equal((await page.evaluate(() => valueCheck.relief())).visible, false);
    assert.equal((await page.evaluate(() => valueCheck.relief())).flatBodyVisible, true);
    assert.equal(await page.locator('#arrow-legend').isVisible(), true);
    assert.equal(await page.locator('#relief-legend').isVisible(), false);
    assert.equal(await page.evaluate(() => valueCheck.unchanged()), true);
    await graph.press('ArrowLeft');
    await page.locator('#inflate-button').click();
    await relief.click(); // Toggle both visuals during an inflation fade.
    assert.ok((await page.evaluate(() => valueCheck.check())).every(view => view.relief && !view.arrows));
    assert.equal(await relief.getAttribute('aria-pressed'), 'true');
    await page.evaluate(() => valueCheck.highlight());
    await page.waitForFunction(() => !valueCheck.read().transitioning);
    reliefState = await page.evaluate(() => valueCheck.relief());
    assert.equal(reliefState.protrusions, 8 * 16); assert.equal(reliefState.indents, 8 * 16);
    assert.ok(Math.abs(reliefState.volume - 56) < 1e-4);
    await page.screenshot({ path: '/tmp/chair-relief-supertile.png' });
    await graph.press('Escape');
    for (let orientation = 0; orientation < 8; orientation++) {
      await graph.press('ArrowRight');
      assert.equal((await page.evaluate(() => valueCheck.highlight())).selected, orientation);
      await arrows.click();
      assert.ok((await page.evaluate(() => valueCheck.highlight())).dim > 0);
      await relief.click();
      assert.ok((await page.evaluate(() => valueCheck.highlight())).dim > 0);
    }
    await graph.press('ArrowRight');
    for (let attempt = 0; attempt < 8 && !(await page.evaluate(() => valueCheck.highlight())).bright; attempt++) {
      await graph.press('ArrowRight');
    }
    assert.ok((await page.evaluate(() => valueCheck.highlight())).bright > 0);
    await page.screenshot({ path: '/tmp/chair-relief-highlight.png' });
    await arrows.click();
    await page.screenshot({ path: '/tmp/chair-arrows-highlight.png' });
    await relief.click();
    await page.locator('#apply-one-button').click();
    await page.waitForFunction(() => !valueCheck.read().transitioning);
    assert.equal((await page.evaluate(() => valueCheck.relief())).protrusions, 9 * 16);
    await page.evaluate(() => valueCheck.highlight());
    await relief.click();
    await page.locator('#run-button').click();
    await page.waitForFunction(() => valueCheck.read().count >= 11);
    await page.locator('#back-button').click();
    await page.waitForFunction(() => !valueCheck.read().transitioning);
    assert.equal((await page.evaluate(() => valueCheck.relief())).protrusions, 9 * 16);
    await page.evaluate(() => valueCheck.highlight());
    await page.locator('#inflate-button').click();
    assert.equal((await page.evaluate(() => valueCheck.relief())).protrusions, 8 * 16);
    await page.setViewportSize({ width: 390, height: 844 });
    await relief.scrollIntoViewIfNeeded();
    await page.waitForTimeout(250);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await relief.click();
    await page.screenshot({ path: '/tmp/chair-relief-mobile.png' });
    await arrows.click();
    assert.ok((await page.evaluate(() => valueCheck.check())).every(view => view.arrows && !view.relief));
    await graph.press('Escape');
    assert.equal((await page.evaluate(() => valueCheck.highlight())).dim, 0);
    assert.deepEqual(errors, []);
    console.log('Passed all eight orientation highlights and Arrows/Relief toggle: closed surfaces, correct volume, transition toggle, Run/Undo, inflation return, and mobile layout.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
