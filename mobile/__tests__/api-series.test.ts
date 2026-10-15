/// <reference types="node" />
import { createRunsClient, validateAllocationContext, validateEquityContext } from '../src/api/client';
import type { Allocations, EquityCurve, RunReport } from '../src/api/contract';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const ID = '11111111-2222-4333-8444-555555555555';
const dates = ['2026-10-12', '2026-10-13'];
const equity: EquityCurve = { dates, costBps: 1, convention: 'Growth of 1 after net costs', series: [{ strategy: 'lstm', wealth: [1.01, 1.02] }] };
const allocations: Allocations = { assets: ['STOCK', 'BOND'], convention: 'Prior close long-only target weights', strategies: [{ strategy: 'lstm', rows: dates.map((returnDate) => ({ returnDate, weights: [0.6, 0.4] })) }] };
const report: RunReport = { researchRunId: 'fixture', methodLabel: 'synthetic-smoke', testDates: dates, costBps: 1, strategies: { lstm: { cumulativeReturn: 0.02, annualizedVolatility: 0.1, sharpe: 0.2, sharpeNote: null, maxDrawdown: 0, totalTurnover: 1, totalCostReturnUnits: 0.0001, observations: 2 } } };

function fake(body: unknown, status = 200) {
  const fetchImpl = jest.fn(async () => ({ ok: status === 200, status, text: async () => JSON.stringify(body) }));
  const client = createRunsClient({ baseUrl: 'http://127.0.0.1:8080', token: 'unit-test-secret-series', fetchImpl });
  return { client, fetchImpl };
}

test('reads authenticated equity and allocations in declared order', async () => {
  const curve = fake(equity);
  expect(await curve.client.equityCurve(ID)).toEqual(equity);
  expect(curve.fetchImpl).toHaveBeenCalledWith(`http://127.0.0.1:8080/api/v1/runs/${ID}/equity-curve`, expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer unit-test-secret-series' }) }));
  const weights = fake(allocations);
  expect(await weights.client.allocations(ID)).toEqual(allocations);
  expect(weights.fetchImpl).toHaveBeenCalledWith(`http://127.0.0.1:8080/api/v1/runs/${ID}/allocations`, expect.objectContaining({ method: 'GET' }));
});

test.each([
  { ...equity, dates: ['2026-02-30', '2026-03-01'] },
  { ...equity, dates: [...dates].reverse() },
  { ...equity, dates: [dates[0], dates[0]] },
  { ...equity, costBps: 101 },
  { ...equity, series: [{ strategy: 'lstm', wealth: [1] }] },
  { ...equity, series: [{ strategy: 'lstm', wealth: [1, null] }] },
  { ...equity, series: [...equity.series, ...equity.series] },
  { ...equity, series: [] },
  { ...equity, convention: '' },
])('rejects invalid equity before display', async (body) => {
  await expect(fake(body).client.equityCurve(ID)).rejects.toMatchObject({ kind: 'invalid_response' });
});

test.each([
  { ...allocations, assets: ['STOCK', 'STOCK'] },
  { ...allocations, assets: ['STOCK'] },
  { ...allocations, strategies: [] },
  { ...allocations, strategies: [...allocations.strategies, ...allocations.strategies] },
  ...[[1.1, -0.1], [0.4, 0.4], [null, 1], ['0.6', 0.4]].map((weights) => ({ ...allocations, strategies: [{ strategy: 'lstm', rows: [{ returnDate: dates[0], weights }] }] })),
  { ...allocations, strategies: [{ strategy: 'lstm', rows: [...allocations.strategies[0].rows].reverse() }] },
  { ...allocations, strategies: [{ strategy: 'lstm', rows: [{ returnDate: '2026-02-30', weights: [0.6, 0.4] }] }] },
])('rejects invalid weights, dimensions, identities or dates', async (body) => {
  await expect(fake(body).client.allocations(ID)).rejects.toMatchObject({ kind: 'invalid_response' });
});

test('permits runner rounding tolerance but rejects incompatible comparison context', () => {
  expect(validateEquityContext(equity, report)).toBe(equity);
  expect(validateAllocationContext(allocations, report)).toBe(allocations);
  expect(() => validateEquityContext({ ...equity, costBps: 2 }, report)).toThrow();
  expect(() => validateEquityContext({ ...equity, dates: ['2026-10-11', dates[1]] }, report)).toThrow();
  expect(() => validateEquityContext({ ...equity, series: [{ strategy: 'other', wealth: [1, 1] }] }, report)).toThrow();
  expect(() => validateAllocationContext({ ...allocations, strategies: [{ strategy: 'other', rows: allocations.strategies[0].rows }] }, report)).toThrow();
  expect(() => validateAllocationContext({ ...allocations, strategies: [{ strategy: 'lstm', rows: [allocations.strategies[0].rows[0]] }] }, report)).toThrow();
});

test('accepts finite exponent-sized weights within sum tolerance', async () => {
  const body = { ...allocations, strategies: [{ strategy: 'lstm', rows: [{ returnDate: dates[0], weights: [1e-7, 0.9999998] }] }] };
  expect(await fake(body).client.allocations(ID)).toEqual(body);
});

test.each(['equityCurve', 'allocations'] as const)('%s validates UUID and preserves service errors', async (method) => {
  const invalid = fake(equity);
  await expect(invalid.client[method]('bad')).rejects.toMatchObject({ kind: 'invalid_input' });
  expect(invalid.fetchImpl).not.toHaveBeenCalled();
  for (const status of [401, 409, 502]) {
    await expect(fake({ code: 'artifact_content_invalid' }, status).client[method](ID)).rejects.toMatchObject({ kind: 'http', status });
  }
});

test('accepts retained A0 runner artifacts through the documented endpoint shapes', async () => {
  const fixture = resolve(__dirname, '../../backend/src/test/resources/fixtures/a0-synthetic');
  const raw = JSON.parse(readFileSync(resolve(fixture, 'report.json'), 'utf8'));
  const measured = await fake(raw).client.report(ID);
  const endpointCurve = {
    dates: raw.test_dates, costBps: raw.cost_bps, convention: 'Growth of 1 after net costs',
    series: Object.entries(raw.strategies).map(([strategy, result]) => ({ strategy, wealth: (result as { wealth: number[] }).wealth })),
  };
  const parsedCurve = validateEquityContext(await fake(endpointCurve).client.equityCurve(ID), measured);
  const [header, ...rows] = readFileSync(resolve(fixture, 'allocations.csv'), 'utf8').trim().split(/\r?\n/).map((line) => line.split(','));
  const grouped = new Map<string, { returnDate: string; weights: number[] }[]>();
  for (const [returnDate, strategy, ...weights] of rows) {
    if (!grouped.has(strategy)) grouped.set(strategy, []);
    grouped.get(strategy)!.push({ returnDate, weights: weights.map(Number) });
  }
  const endpointAllocations = { assets: header.slice(2), convention: 'Prior close target weights', strategies: [...grouped].map(([strategy, entries]) => ({ strategy, rows: entries })) };
  const parsedAllocations = validateAllocationContext(await fake(endpointAllocations).client.allocations(ID), measured);
  expect(parsedAllocations.assets).toEqual(header.slice(2));
  expect(parsedCurve.series.map((item) => item.strategy)).toEqual(['lstm', 'equal_weight', 'stock_bond_60_40']);
  for (const item of parsedCurve.series) {
    expect(item.wealth[item.wealth.length - 1] - 1).toBeCloseTo(measured.strategies[item.strategy].cumulativeReturn, 12);
  }
  expect(parsedAllocations.strategies.every((item) => item.rows.length === measured.testDates.length)).toBe(true);
});
