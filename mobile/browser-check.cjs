// Requires an already-running, authorized web app. No service is contacted:
// all /api/v1/runs requests below are intercepted synthetic fixtures.
// NODE_PATH may point to the Codex bundled node_modules containing Playwright.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright');

const appUrl = process.env.PORTFOLIO_WEB_URL || 'http://localhost:8081';
const output = path.resolve(process.env.PORTFOLIO_BROWSER_EVIDENCE || '.expo-tmp/browser-evidence');
const runId = '11111111-2222-4333-8444-555555555555';
const dates = ['2026-10-12', '2026-10-13'];
const status = { runId, state: 'COMPLETE', attemptCount: 1, manifestAvailable: true, errorCode: null };
const metrics = { cumulative_return: 0.1234, annualized_volatility: 0.2, sharpe: 0.81, sharpe_note: null, max_drawdown: 0.04, total_turnover: 1.3, total_cost_return_units: 0.00013, observations: 2 };
const report = { run_id: 'synthetic-browser-fixture', method_label: 'synthetic-smoke', test_dates: dates, cost_bps: 1, strategies: { lstm: { metrics }, equal_weight: { metrics: { ...metrics, sharpe: null, sharpe_note: 'Undefined: zero or near-zero volatility' } } } };
const fixtures = {
  report,
  manifest: { run_id: runId, attempt_id: '66666666-7777-4888-9999-aaaaaaaaaaaa', kind: 'synthetic-a0', files: [{ path: 'report.json', key: `runs/${runId}/report.json`, sha256: 'a'.repeat(64), bytes: 2048 }] },
  'equity-curve': { dates, costBps: 1, convention: 'Growth of 1 after net costs', series: [{ strategy: 'lstm', wealth: [1.01, 1.1234] }, { strategy: 'equal_weight', wealth: [1.02, 1.1234] }] },
  allocations: { assets: ['STOCK', 'BOND'], convention: 'Prior close target weights; no raw model outputs', strategies: ['lstm', 'equal_weight'].map(strategy => ({ strategy, rows: dates.map(returnDate => ({ returnDate, weights: [0.6, 0.4] })) })) },
};

async function text(page, value) { await page.getByText(value, { exact: true }).waitFor(); }
async function click(page, name) { await page.getByRole('button', { name, exact: true }).click(); }
async function screenshot(page, name) {
  await page.screenshot({ path: path.join(output, `${name}.png`), fullPage: true });
  const overflow = await page.evaluate(() => [...document.querySelectorAll('[role="button"],input,[role="heading"]')].filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && (r.left < -1 || r.right > innerWidth + 1); }).map(el => el.getAttribute('aria-label') || el.textContent));
  assert.deepEqual(overflow, [], `Horizontal overflow at ${name}`);
  const shortTargets = await page.evaluate(() => [...document.querySelectorAll('[role="button"]')].filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height < 48; }).map(el => el.getAttribute('aria-label') || el.textContent));
  assert.deepEqual(shortTargets, [], `Touch targets below 48 pixels at ${name}`);
}

async function connect(page) {
  await click(page, 'Connect to service');
  await page.getByLabel('Service base URL', { exact: true }).fill(`${appUrl}/mock-service`);
  await page.getByLabel('Operator token', { exact: true }).fill('unit-test-secret-browser-fixture');
  await click(page, 'Connect');
  await text(page, 'Live experiments');
}

async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ channel: process.env.PORTFOLIO_BROWSER_CHANNEL || 'chrome', headless: true });
  const evidence = { kind: 'mocked-browser-ui', appUrl, playwright: require('playwright/package.json').version, browser: browser.version(), checks: [], screenshots: [] };
  try {
    for (const mode of [{ name: 'light-desktop', width: 1280, colorScheme: 'light' }, { name: 'dark-phone', width: 390, colorScheme: 'dark' }]) {
      const context = await browser.newContext({ viewport: { width: mode.width, height: 844 }, colorScheme: mode.colorScheme });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      let reportFails = false, equityFails = false, rejectToken = false;
      const calls = [];
      await context.route('**/mock-service/api/v1/runs**', async route => {
        const request = route.request();
        calls.push({ method: request.method(), path: new URL(request.url()).pathname });
        assert.equal(request.headers().authorization, 'Bearer unit-test-secret-browser-fixture');
        if (rejectToken) return route.fulfill({ status: 401, json: {} });
        const suffix = new URL(request.url()).pathname.split('/').pop();
        if ((suffix === 'report' && reportFails) || (suffix === 'equity-curve' && equityFails)) return route.fulfill({ status: 503, json: {} });
        const body = suffix === 'runs' ? { items: [{ ...status, createdAt: '2026-10-13T08:15:30Z' }], nextCursor: null } : suffix === runId ? status : fixtures[suffix];
        assert.ok(body, `Unexpected mocked route ${suffix}`);
        return route.fulfill({ status: 200, json: body });
      });
      await page.goto(appUrl);
      await page.getByRole('heading', { name: 'Experiments', exact: true }).waitFor();
      await screenshot(page, `${mode.name}-offline`);
      await click(page, 'New experiment');
      assert.equal(await page.getByRole('button', { name: 'Start experiment', exact: true }).getAttribute('aria-disabled'), 'true');
      await page.getByLabel('Lookback days', { exact: true }).fill('51');
      await page.keyboard.press('Tab');
      await text(page, 'Lookback must be a whole number from 10 to 50.');
      await click(page, 'Back');
      // Keyboard activation follows the named focusable action.
      await page.getByRole('button', { name: 'Connect to service', exact: true }).focus();
      await page.keyboard.press('Enter');
      await page.getByRole('heading', { name: 'Service connection', exact: true }).waitFor();
      await click(page, 'Back');
      await connect(page);
      await click(page, 'Open run 11111111, Complete');
      await text(page, 'State: Complete');
      reportFails = true;
      await click(page, 'View results');
      await text(page, 'Report unavailable');
      await screenshot(page, `${mode.name}-report-error`);
      reportFails = false; equityFails = true;
      await click(page, 'Retry report');
      await text(page, 'Measured report');
      await page.getByText(/^Equity unavailable\./).waitFor();
      await text(page, 'STOCK: 60.00%');
      equityFails = false;
      await click(page, 'Retry equity');
      await text(page, 'LSTM wealth: 1.1234');
      await page.getByText('Measured report', { exact: true }).scrollIntoViewIfNeeded();
      await screenshot(page, `${mode.name}-measured-report`);
      await page.getByText('Equity & allocations', { exact: true }).scrollIntoViewIfNeeded();
      await screenshot(page, `${mode.name}-results`);
      await page.getByText('STOCK: 60.00%', { exact: true }).scrollIntoViewIfNeeded();
      await screenshot(page, `${mode.name}-allocations`);
      await click(page, 'Inspect Equal weight');
      await click(page, 'Previous date');
      await text(page, 'Date: 2026-10-12 · 1 of 2');
      await text(page, 'Equal weight wealth: 1.0200');
      if (mode.width === 390) {
        // CSS text-only enlargement is browser evidence, not Android fontScale.
        await page.evaluate(() => {
          const textNodes = [...document.querySelectorAll('body *')].filter(el => !['SCRIPT', 'STYLE'].includes(el.tagName) && (el.tagName === 'INPUT' || [...el.childNodes].some(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim())));
          const sizes = textNodes.map(el => [el, parseFloat(getComputedStyle(el).fontSize)]);
          for (const [el, size] of sizes) { el.style.fontSize = `${size * 2}px`; el.style.lineHeight = `${size * 2.8}px`; }
        });
        await page.getByText('Equity & allocations', { exact: true }).scrollIntoViewIfNeeded();
        await screenshot(page, `${mode.name}-large-text`);
        await page.getByText('STOCK: 60.00%', { exact: true }).scrollIntoViewIfNeeded();
        await screenshot(page, `${mode.name}-large-text-allocations`);
      }
      await click(page, 'Back'); await click(page, 'Back');
      await click(page, 'Service settings'); await click(page, 'Disconnect'); await click(page, 'Back');
      rejectToken = true;
      await click(page, 'Connect to service');
      await page.getByLabel('Operator token', { exact: true }).fill('unit-test-secret-browser-fixture');
      await click(page, 'Connect');
      await text(page, 'Token rejected (HTTP 401). Check the operator token.');
      assert.deepEqual(errors, []);
      assert.ok(calls.length >= 9);
      evidence.checks.push({ mode: mode.name, width: mode.width, colorScheme: mode.colorScheme, cssTextScale: mode.width === 390 ? 2 : 1, checks: ['offline-disabled', 'invalid-input', 'keyboard-enter', 'mocked-report-error-retry', 'independent-equity-retry', 'strategy-date-values', 'token-rejection', 'no-horizontal-control-overflow', '48-pixel-touch-targets', 'no-page-errors'], mockedCalls: calls.length });
      await context.close();
    }
    evidence.screenshots = (await fs.readdir(output)).filter(name => name.endsWith('.png'));
    await fs.writeFile(path.join(output, 'results.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log(JSON.stringify(evidence, null, 2));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
