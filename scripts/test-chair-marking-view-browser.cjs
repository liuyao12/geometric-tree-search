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
    assert.deepEqual(await page.evaluate(() => valueCheck.check()), [{ lazy: true, arrows: true }]);
    await page.evaluate(() => valueCheck.remember());
    await values.click();
    assert.deepEqual(await page.evaluate(() => valueCheck.check()), [{ lazy: false, arrows: false, values: true, points: 288, shared: 0, assignments: 288 }]);
    assert.equal(await values.getAttribute('aria-pressed'), 'true');
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
    await page.locator('#apply-one-button').click();
    await page.waitForFunction(() => !valueCheck.read().transitioning);
    assert.equal((await page.evaluate(() => valueCheck.check()))[0].assignments, 2 * 288);
    await page.locator('#run-button').click();
    await page.waitForFunction(() => valueCheck.read().count >= 4);
    await page.locator('#back-button').click();
    await page.waitForFunction(() => !valueCheck.read().transitioning);
    assert.equal((await page.evaluate(() => valueCheck.check()))[0].assignments, 2 * 288);
    await page.locator('#inflate-button').click();
    assert.equal((await page.evaluate(() => valueCheck.check()))[0].points, inflated.points);
    await page.setViewportSize({ width: 390, height: 844 });
    await values.scrollIntoViewIfNeeded();
    await page.waitForTimeout(250);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: '/tmp/chair-values-mobile.png' });
    await arrows.click();
    assert.ok((await page.evaluate(() => valueCheck.check())).every(view => view.arrows && !view.values));
    assert.deepEqual(errors, []);
    console.log('Passed scalar display: exact coordinates/values, visible shared points and zeros, transition toggle, Run/Undo, inflation return, and mobile layout.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
