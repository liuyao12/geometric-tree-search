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
        import { latticeTile as expectedTile } from './chair-lattice.js';
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
          check() {
            return [...new Set([currentVisual, transition?.from, transition?.to])].filter(Boolean).map(visual => {
              const lattice = visual.group.getObjectByName('chair44-lattice');
              const arrows = visual.group.getObjectByName('chair44-arrows');
              if (!lattice) return { lazy: true, arrows: arrows.visible };
              const expected = new Map(), actual = new Map();
              for (const tile of visual.leaves) for (const entry of expectedTile(tile).m) {
                const key = entry.point.join(',');
                const old = expected.get(key);
                expected.set(key, [entry.value, (old?.[1] ?? 0) + 1]);
              }
              for (const points of lattice.children) {
                const positions = points.geometry.getAttribute('position');
                const assignments = points.geometry.getAttribute('assignments');
                for (let i = 0; i < positions.count; i++) {
                  const key = [positions.getX(i), positions.getY(i), positions.getZ(i)].map(v => Math.round(v * 12)).join(',');
                  if (actual.has(key)) throw Error('Duplicate displayed point');
                  actual.set(key, [points.userData.value, assignments.getX(i)]);
                }
              }
              const signature = map => JSON.stringify([...map].sort(([a], [b]) => a.localeCompare(b)));
              if (signature(actual) !== signature(expected)) throw Error('Displayed points disagree with scalar lattice model');
              return { lazy: false, arrows: arrows.visible, values: lattice.visible,
                points: actual.size, shared: [...actual.values()].filter(([, n]) => n > 1).length,
                assignments: [...actual.values()].reduce((sum, [, n]) => sum + n, 0) };
            });
          }
        };
      ` });
    });
    await page.goto(base);
    await page.waitForFunction(() => window.valueCheck);
    const arrows = page.getByRole('button', { name: 'Arrows', exact: true });
    const values = page.getByRole('button', { name: 'Lattice values', exact: true });
    const relief = page.getByRole('button', { name: 'Relief', exact: true });
    assert.deepEqual(await page.evaluate(() => valueCheck.check()), [{ lazy: true, arrows: true }]);
    await page.evaluate(() => valueCheck.remember());
    await relief.click();
    let reliefState = await page.evaluate(() => valueCheck.relief());
    assert.equal(reliefState.visible, true);
    assert.equal(reliefState.blueCreases, 8 * 14, 'Each blue pair has a joined ramp without a dividing crease');
    assert.equal(reliefState.flatBodyVisible, false);
    assert.equal(reliefState.closed, true, 'The panel cutouts and relief sides form a closed surface');
    assert.ok(Math.abs(reliefState.volume - 7) < 1e-5);
    assert.equal(reliefState.protrusions, 16); assert.equal(reliefState.indents, 16);
    assert.equal(await page.locator('#relief-legend').isVisible(), true);
    await page.screenshot({ path: '/tmp/chair-relief-single.png' });
    await values.click();
    assert.deepEqual(await page.evaluate(() => valueCheck.check()), [{ lazy: false, arrows: false, values: true, points: 288, shared: 0, assignments: 288 }]);
    assert.equal(await values.getAttribute('aria-pressed'), 'true');
    assert.equal((await page.evaluate(() => valueCheck.relief())).visible, false);
    assert.equal((await page.evaluate(() => valueCheck.relief())).flatBodyVisible, true);
    assert.equal(await page.locator('#value-legend').isVisible(), true);
    assert.equal(await page.locator('#arrow-legend').isVisible(), false);
    await page.screenshot({ path: '/tmp/chair-values-single.png' });
    await arrows.click();
    assert.equal((await page.evaluate(() => valueCheck.check()))[0].values, false);
    assert.equal(await page.evaluate(() => valueCheck.unchanged()), true);
    await page.locator('#inflate-button').click();
    await values.click(); // Also creates points safely during an inflation fade.
    assert.ok((await page.evaluate(() => valueCheck.check())).every(view => view.values && !view.arrows));
    await page.waitForFunction(() => !valueCheck.read().transitioning);
    const inflated = (await page.evaluate(() => valueCheck.check()))[0];
    assert.equal(inflated.assignments, 8 * 288);
    assert.equal(inflated.shared, 48 * 12);
    assert.equal(inflated.points, 8 * 288 - 48 * 12);
    await page.screenshot({ path: '/tmp/chair-values-supertile.png' });
    await relief.click();
    reliefState = await page.evaluate(() => valueCheck.relief());
    assert.equal(reliefState.protrusions, 8 * 16); assert.equal(reliefState.indents, 8 * 16);
    assert.ok(Math.abs(reliefState.volume - 56) < 1e-4);
    await page.screenshot({ path: '/tmp/chair-relief-supertile.png' });
    await values.click();
    await page.locator('#apply-one-button').click();
    await page.waitForFunction(() => !valueCheck.read().transitioning);
    assert.equal((await page.evaluate(() => valueCheck.check()))[0].assignments, 2 * 288);
    await relief.click();
    await page.locator('#run-button').click();
    await page.waitForFunction(() => valueCheck.read().count >= 4);
    await page.locator('#back-button').click();
    await page.waitForFunction(() => !valueCheck.read().transitioning);
    assert.equal((await page.evaluate(() => valueCheck.relief())).protrusions, 2 * 16);
    await values.click();
    assert.equal((await page.evaluate(() => valueCheck.check()))[0].assignments, 2 * 288);
    await page.locator('#inflate-button').click();
    assert.equal((await page.evaluate(() => valueCheck.check()))[0].points, inflated.points);
    await page.setViewportSize({ width: 390, height: 844 });
    await values.scrollIntoViewIfNeeded();
    await page.waitForTimeout(250);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: '/tmp/chair-values-mobile.png' });
    await relief.click();
    await page.screenshot({ path: '/tmp/chair-relief-mobile.png' });
    await arrows.click();
    assert.ok((await page.evaluate(() => valueCheck.check())).every(view => view.arrows && !view.values));
    assert.deepEqual(errors, []);
    console.log('Passed relief (closed surfaces, correct volume) and scalar display: exact coordinates/values, visible shared points and zeros, transition toggle, Run/Undo, inflation return, and mobile layout.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
