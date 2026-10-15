import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { ResultSeries } from '../src/ResultSeries';
import { RunsApiError } from '../src/api/client';
import type { RunsClient } from '../src/api/client';
import type { Allocations, EquityCurve, RunReport } from '../src/api/contract';
import { dark, light } from '../src/theme';

const report: RunReport = {
  researchRunId: 'synthetic-fixture', methodLabel: 'synthetic-smoke', costBps: 1,
  testDates: ['2026-10-12', '2026-10-13'],
  strategies: Object.fromEntries(['lstm', 'equal_weight'].map((name) => [name, { cumulativeReturn: 0.02, annualizedVolatility: 0.1, sharpe: 0.2, sharpeNote: null, maxDrawdown: 0, totalTurnover: 1, totalCostReturnUnits: 0.0001, observations: 2 }])),
};
const curve: EquityCurve = { dates: report.testDates, costBps: 1, convention: 'Growth of 1 after net costs', series: [{ strategy: 'lstm', wealth: [1.01, 1.02] }, { strategy: 'equal_weight', wealth: [1.03, 1.04] }] };
const allocations: Allocations = { assets: ['STOCK', 'BOND'], convention: 'Prior close target weights; raw model outputs not recorded', strategies: [{ strategy: 'lstm', rows: [{ returnDate: report.testDates[0], weights: [0.7, 0.3] }, { returnDate: report.testDates[1], weights: [0.6, 0.4] }] }, { strategy: 'equal_weight', rows: report.testDates.map((returnDate) => ({ returnDate, weights: [0.5, 0.5] })) }] };

function makeClient() {
  return {
    equityCurve: jest.fn(async (_id: string) => curve),
    allocations: jest.fn(async (_id: string) => allocations),
    report: jest.fn(), manifest: jest.fn(), list: jest.fn(), submit: jest.fn(), status: jest.fn(), cancel: jest.fn(),
  } satisfies RunsClient;
}

function pending<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

test.each([light, dark])('shows real values, conventions, asset order and accessible date/strategy controls', async (colors) => {
  const client = makeClient();
  await render(<ResultSeries client={client} runId="run-a" report={report} colors={colors} />);
  expect(await screen.findByText('LSTM wealth: 1.0200')).toBeTruthy();
  expect(screen.getByText('Equal weight wealth: 1.0400')).toBeTruthy();
  expect(screen.getByText('Growth of 1 after net costs')).toBeTruthy();
  expect(screen.getByText(/raw model outputs not recorded/)).toBeTruthy();
  expect(screen.getAllByText(/^(STOCK|BOND):/).map((node) => node.props.children)).toEqual(['STOCK: 60.00%', 'BOND: 40.00%']);
  expect(screen.getByRole('button', { name: 'Next date' })).toBeDisabled();
  await fireEvent.press(screen.getByRole('button', { name: 'Previous date' }));
  expect(screen.getByText('Date: 2026-10-12 · 1 of 2')).toBeTruthy();
  expect(screen.getByText('LSTM wealth: 1.0100')).toBeTruthy();
  expect(screen.getByText('STOCK: 70.00%')).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Previous date' })).toBeDisabled();
  await fireEvent.press(screen.getByRole('button', { name: 'Inspect Equal weight' }));
  expect(screen.getByRole('button', { name: 'Inspect Equal weight' }).props.accessibilityState.selected).toBe(true);
  expect(screen.getByRole('header', { name: 'Equal weight allocations' })).toBeTruthy();
  expect(screen.getByText('STOCK: 50.00%')).toBeTruthy();
  // Exercise native chart layout after changing the selected strategy.
  await fireEvent(screen.getByRole('image'), 'layout', { nativeEvent: { layout: { width: 280 } } });
  await fireEvent.press(screen.getByRole('button', { name: 'Next date' }));
  expect(screen.getByText('Date: 2026-10-13 · 2 of 2')).toBeTruthy();
  expect(client.equityCurve).toHaveBeenCalledTimes(1);
  expect(client.allocations).toHaveBeenCalledTimes(1);
});

test('equity and allocations load independently, retry only the failed endpoint', async () => {
  const client = makeClient();
  const delayed = pending<EquityCurve>();
  client.equityCurve.mockReturnValueOnce(delayed.promise);
  client.allocations.mockRejectedValueOnce(new RunsApiError('http', 'ignored secret detail', 502));
  await render(<ResultSeries client={client} runId="run-a" report={report} colors={light} />);
  expect(await screen.findByText('Loading equity curve…')).toBeTruthy();
  expect(await screen.findByText(/Allocations unavailable.*502/)).toBeTruthy();
  expect(screen.queryByText('STOCK: 60.00%')).toBeNull();
  await fireEvent.press(screen.getByRole('button', { name: 'Retry allocations' }));
  expect(await screen.findByText('STOCK: 60.00%')).toBeTruthy();
  expect(client.equityCurve).toHaveBeenCalledTimes(1);
  await act(async () => delayed.resolve(curve));
  expect(await screen.findByText('LSTM wealth: 1.0200')).toBeTruthy();
});

test('incompatible equity context shows no values and can be retried', async () => {
  const client = makeClient();
  client.equityCurve.mockResolvedValueOnce({ ...curve, costBps: 5 });
  await render(<ResultSeries client={client} runId="run-a" report={report} colors={light} />);
  expect(await screen.findByText(/Equity unavailable.*does not match/)).toBeTruthy();
  expect(screen.queryByText(/LSTM wealth:/)).toBeNull();
  expect(screen.getByText('STOCK: 60.00%')).toBeTruthy();
  await fireEvent.press(screen.getByRole('button', { name: 'Retry equity' }));
  expect(await screen.findByText('LSTM wealth: 1.0200')).toBeTruthy();
});

test('incompatible allocation dates show no weights while equity remains', async () => {
  const client = makeClient();
  client.allocations.mockResolvedValueOnce({ ...allocations, strategies: allocations.strategies.map((item) => ({ ...item, rows: item.rows.slice(1) })) });
  await render(<ResultSeries client={client} runId="run-a" report={report} colors={light} />);
  expect(await screen.findByText(/Allocations unavailable.*does not match/)).toBeTruthy();
  expect(screen.queryByText(/STOCK:/)).toBeNull();
  expect(screen.getByText('LSTM wealth: 1.0200')).toBeTruthy();
});

test('late responses from a previously selected run cannot overwrite the next run', async () => {
  const client = makeClient();
  const oldEquity = pending<EquityCurve>(), oldAllocations = pending<Allocations>();
  client.equityCurve.mockReturnValueOnce(oldEquity.promise);
  client.allocations.mockReturnValueOnce(oldAllocations.promise);
  const view = await render(<ResultSeries key="run-a" client={client} runId="run-a" report={report} colors={light} />);
  expect(screen.getByText('Loading allocations…')).toBeTruthy();
  await view.rerender(<ResultSeries key="run-b" client={client} runId="run-b" report={report} colors={light} />);
  expect(await screen.findByText('LSTM wealth: 1.0200')).toBeTruthy();
  await act(async () => {
    oldEquity.resolve({ ...curve, series: curve.series.map((item) => ({ ...item, wealth: [99, 99] })) });
    oldAllocations.resolve({ ...allocations, assets: ['OLD', 'DATA'] });
  });
  expect(screen.queryByText(/99.0000/)).toBeNull();
  expect(screen.queryByText(/OLD:/)).toBeNull();
  expect(screen.getByText('LSTM wealth: 1.0200')).toBeTruthy();
  expect(client.equityCurve).toHaveBeenLastCalledWith('run-b');
});

test('single-date flat equity keeps navigation bounded and handles layout', async () => {
  const oneReport = { ...report, testDates: report.testDates.slice(0, 1) };
  const client = makeClient();
  client.equityCurve.mockResolvedValue({ ...curve, dates: oneReport.testDates, series: curve.series.map((item) => ({ ...item, wealth: [1] })) });
  client.allocations.mockResolvedValue({ ...allocations, strategies: allocations.strategies.map((item) => ({ ...item, rows: item.rows.slice(0, 1) })) });
  await render(<ResultSeries client={client} runId="run-a" report={oneReport} colors={light} />);
  expect(await screen.findByText('LSTM wealth: 1.0000')).toBeTruthy();
  await fireEvent(screen.getByRole('image'), 'layout', { nativeEvent: { layout: { width: 200 } } });
  expect(screen.getByRole('button', { name: 'Previous date' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Next date' })).toBeDisabled();
});
