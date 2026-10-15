// Explicitly authorized local API/PostgreSQL smoke. No fixtures/interception.
// Never writes credentials or raw responses; output is bounded state evidence.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright');

async function main() {
  const appUrl = process.env.PORTFOLIO_WEB_URL || 'http://localhost:8081';
  const apiUrl = process.env.PORTFOLIO_LIVE_API_URL || 'http://localhost:8080';
  const key = process.env.PORTFOLIO_RUNTIME_TOKEN_KEY || 'PORTFOLIO_OPERATOR_TOKEN';
  const credentialFile = path.resolve(process.env.PORTFOLIO_RUNTIME_ENV_PATH || '../.env.runtime-test');
  const lines = (await fs.readFile(credentialFile, 'utf8')).split(/\r?\n/);
  const entry = lines.find(line => line.startsWith(`${key}=`));
  assert.ok(entry, 'Configured runtime credential key is absent');
  const token = entry.slice(key.length + 1).replace(/^(['"])(.*)\1$/, '$2');
  assert.ok(token.length >= 1, 'Runtime credential is empty');
  const output = path.resolve(process.env.PORTFOLIO_BROWSER_EVIDENCE || '.expo-tmp/browser-live-evidence');
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ channel: process.env.PORTFOLIO_BROWSER_CHANNEL || 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, colorScheme: 'dark' });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message.replaceAll(token, '[redacted]')));
    const button = name => page.getByRole('button', { name, exact: true });
    await page.goto(appUrl);
    await button('Connect to service').click();
    await page.getByLabel('Service base URL', { exact: true }).fill(apiUrl);
    await page.getByLabel('Operator token', { exact: true }).fill(token);
    await button('Connect').click();
    await page.getByText('Connected to ', { exact: false }).waitFor();
    await button('New experiment').click();
    await page.getByLabel('Training epochs', { exact: true }).fill('1');
    const acceptedResponse = page.waitForResponse(response => response.url() === `${apiUrl}/api/v1/runs` && response.request().method() === 'POST');
    await button('Start experiment').click();
    const accepted = await acceptedResponse;
    assert.equal(accepted.status(), 202);
    const { runId } = await accepted.json();
    assert.match(runId, /^[a-f0-9-]{36}$/i);
    await page.getByText('State: Queued', { exact: true }).waitFor();
    const statusResponse = page.waitForResponse(response => response.url() === `${apiUrl}/api/v1/runs/${runId}` && response.request().method() === 'GET');
    await button('Refresh status').click();
    const refreshed = await statusResponse;
    assert.equal(refreshed.status(), 200);
    const status = await refreshed.json();
    assert.equal(status.runId, runId);
    assert.equal(status.state, 'QUEUED');
    await page.getByText('State: Queued', { exact: true }).waitFor();
    const cancellation = page.waitForResponse(response => response.url() === `${apiUrl}/api/v1/runs/${runId}/cancel`);
    await button('Cancel run').click();
    const cancelled = await cancellation;
    assert.ok(cancelled.ok());
    const terminal = await cancelled.json();
    assert.equal(terminal.state, 'CANCELLED');
    await page.getByText('State: Cancelled', { exact: true }).waitFor();
    await page.screenshot({ path: path.join(output, 'real-api-cancelled.png'), fullPage: true });
    await button('Back').click();
    await button('Refresh list').click();
    await button(`Open run ${runId.slice(0, 8)}, Cancelled`).waitFor();
    assert.deepEqual(errors, []);
    const evidence = { kind: 'real-api-browser-smoke', appUrl, apiUrl, browser: browser.version(), runId, checks: ['authenticated-connect-list', 'real-request-202', 'queued-status-refresh', 'queued-cancelled', 'refreshed-run-list', 'no-page-errors'], excluded: ['LocalStack', 'S3', 'worker-training', 'completed-results', 'physical-Android'] };
    await fs.writeFile(path.join(output, 'live-results.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log(JSON.stringify(evidence, null, 2));
  } finally { await browser.close(); }
}
main().catch(() => { console.error('Live browser smoke failed; credential and raw HTTP details suppressed. Inspect local API/application state.'); process.exitCode = 1; });
