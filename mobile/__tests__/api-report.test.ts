import { createRunsClient } from '../src/api/client';
import type { FetchInit, FetchLike } from '../src/api/client';

const RUN_ID = '11111111-2222-4333-8444-555555555555';
const OTHER_ID = '66666666-7777-4888-9999-aaaaaaaaaaaa';
const TOKEN = 'unit-test-secret-report-0123';
const RESEARCH_ID = '20261013T081530-a1b2c3d4e5f6';

const report = {
  run_id: RESEARCH_ID,
  method_label: 'synthetic-smoke',
  test_dates: ['2026-10-12', '2026-10-13'],
  cost_bps: 1,
  strategies: {
    lstm: {
      metrics: {
        cumulative_return: 0.12,
        annualized_volatility: 0.2,
        sharpe: 0.8,
        sharpe_note: null,
        max_drawdown: 0.04,
        total_turnover: 1.3,
        total_cost_return_units: 0.00013,
        observations: 2,
      },
    },
    equal_weight: {
      metrics: {
        cumulative_return: 0.1,
        annualized_volatility: 0,
        sharpe: null,
        sharpe_note: 'Undefined: zero or near-zero volatility',
        max_drawdown: 0,
        total_turnover: 1,
        total_cost_return_units: 0.0001,
        observations: 2,
      },
    },
  },
};

function response(status: number, body: unknown) {
  const calls: { url: string; init: FetchInit }[] = [];
  const fetchImpl: FetchLike = async (url, init) => {
    calls.push({ url, init });
    return { ok: status >= 200 && status < 300, status, text: async () => typeof body === 'string' ? body : JSON.stringify(body) };
  };
  return { fetchImpl, calls };
}

describe('runs report client', () => {
  test('reads a verified report as typed display metrics, preserving undefined Sharpe', async () => {
    const fake = response(200, report);
    const result = await createRunsClient({ baseUrl: 'http://127.0.0.1:8080', token: TOKEN, fetchImpl: fake.fetchImpl }).report(RUN_ID);
    expect(fake.calls).toHaveLength(1);
    expect(fake.calls[0].url).toBe(`http://127.0.0.1:8080/api/v1/runs/${RUN_ID}/report`);
    expect(fake.calls[0].init).toMatchObject({ method: 'GET', headers: { Authorization: `Bearer ${TOKEN}` } });
    expect(result).toMatchObject({
      researchRunId: RESEARCH_ID,
      methodLabel: 'synthetic-smoke',
      testDates: ['2026-10-12', '2026-10-13'],
      costBps: 1,
      strategies: {
        lstm: { cumulativeReturn: 0.12, sharpe: 0.8, observations: 2 },
        equal_weight: { sharpe: null, sharpeNote: 'Undefined: zero or near-zero volatility' },
      },
    });
    expect(result.researchRunId).not.toBe(RUN_ID);
  });

  test('rejects invalid run IDs before fetch', async () => {
    const fake = response(200, report);
    await expect(createRunsClient({ baseUrl: 'http://127.0.0.1:8080', token: TOKEN, fetchImpl: fake.fetchImpl }).report('bad-id'))
      .rejects.toMatchObject({ kind: 'invalid_input' });
    expect(fake.calls).toHaveLength(0);
  });

  test.each([
    { ...report, strategies: {} },
    { ...report, test_dates: [] },
    { ...report, cost_bps: 101 },
    { ...report, strategies: { lstm: { metrics: { ...report.strategies.lstm.metrics, sharpe: '0.8' } } } },
    { ...report, strategies: { lstm: { metrics: { ...report.strategies.lstm.metrics, observations: 3 } } } },
    { ...report, strategies: { lstm: { metrics: { ...report.strategies.lstm.metrics, max_drawdown: -0.1 } } } },
    { ...report, strategies: { lstm: { metrics: { ...report.strategies.lstm.metrics, sharpe: null, sharpe_note: null } } } },
  ])('rejects malformed or misleading report metrics', async (body) => {
    const fake = response(200, body);
    await expect(createRunsClient({ baseUrl: 'http://127.0.0.1:8080', token: TOKEN, fetchImpl: fake.fetchImpl }).report(RUN_ID))
      .rejects.toMatchObject({ kind: 'invalid_response' });
  });

  test('maps incomplete and unavailable report responses without exposing the token', async () => {
    for (const [status, code] of [[409, 'run_not_complete'], [502, 'artifact_integrity_failure']] as const) {
      const fake = response(status, { code });
      const client = createRunsClient({ baseUrl: 'http://127.0.0.1:8080', token: TOKEN, fetchImpl: fake.fetchImpl });
      await expect(client.report(RUN_ID)).rejects.toMatchObject({ kind: 'http', status, code });
      try {
        await client.report(RUN_ID);
      } catch (error) {
        expect(String(error)).not.toContain(TOKEN);
      }
    }
  });

  test('rejects an artifact index for another service run', async () => {
    const fake = response(200, {
      run_id: OTHER_ID,
      attempt_id: OTHER_ID,
      kind: 'synthetic-a0',
      files: [{ path: 'report.json', key: 'runs/other/report.json', sha256: 'a'.repeat(64), bytes: 42 }],
    });
    await expect(createRunsClient({ baseUrl: 'http://127.0.0.1:8080', token: TOKEN, fetchImpl: fake.fetchImpl }).manifest(RUN_ID))
      .rejects.toMatchObject({ kind: 'invalid_response' });
  });
});
