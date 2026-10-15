import { fireEvent, render, screen } from '@testing-library/react-native';
import * as Native from 'react-native';
import { ReportView } from '../src/ReportView';
import { ResultSeries } from '../src/ResultSeries';
import type { RunsClient } from '../src/api/client';
import type { RunReport } from '../src/api/contract';
import { dark, light } from '../src/theme';

jest.mock('react-native/Libraries/Utilities/useWindowDimensions', () => ({
  __esModule: true,
  default: jest.fn(),
}));

const mockDimensions = Native.useWindowDimensions as jest.MockedFunction<typeof Native.useWindowDimensions>;

const report: RunReport = {
  researchRunId: 'synthetic-layout-fixture', methodLabel: 'synthetic-smoke', costBps: 1,
  testDates: ['2026-10-12'],
  strategies: { lstm: { cumulativeReturn: 0.1234, annualizedVolatility: 0.1, sharpe: 0.2, sharpeNote: null, maxDrawdown: 0, totalTurnover: 1, totalCostReturnUnits: 0.0001, observations: 1 } },
};

test.each([
  { width: 320, fontScale: 1, colors: light },
  { width: 720, fontScale: 2, colors: dark },
])('stacks metric groups at width $width and font scale $fontScale without suppressing text scaling', async ({ width, fontScale, colors }) => {
  mockDimensions.mockReturnValue({ width, height: 844, scale: 1, fontScale });
  await render(<ReportView report={report} colors={colors} />);

  const metric = screen.getByLabelText('Sharpe ratio: 0.20');
  expect(metric.props.accessible).toBe(true);
  expect(metric.parent).toHaveStyle({ flexDirection: 'column' });
  // Column layout must use natural content height, not the horizontal column basis.
  expect(metric).toHaveStyle({ flexBasis: 'auto', flexGrow: 0 });
  expect(screen.getByLabelText('Cumulative return: +12.34%')).toBeTruthy();
  expect(screen.getByRole('header', { name: 'Measured report' })).toBeTruthy();
  for (const text of screen.getAllByText(/./)) {
    expect(text.props.allowFontScaling).not.toBe(false);
    expect(text.props.numberOfLines).toBeUndefined();
    expect(text.props.adjustsFontSizeToFit).not.toBe(true);
  }
});

test('reflows metrics when the system text size changes, retaining measured values', async () => {
  mockDimensions.mockReturnValue({ width: 720, height: 844, scale: 1, fontScale: 1 });
  const view = await render(<ReportView report={report} colors={light} />);
  expect(screen.getByLabelText('Sharpe ratio: 0.20').parent).toHaveStyle({ flexDirection: 'row' });
  mockDimensions.mockReturnValue({ width: 720, height: 844, scale: 1, fontScale: 2 });
  await view.rerender(<ReportView report={report} colors={light} />);
  expect(screen.getByLabelText('Sharpe ratio: 0.20').parent).toHaveStyle({ flexDirection: 'column' });
  expect(screen.getByLabelText('Cumulative return: +12.34%')).toBeTruthy();
});

test('large-text series controls stay full-width, named and bounded with numerical alternatives', async () => {
  mockDimensions.mockReturnValue({ width: 390, height: 844, scale: 1, fontScale: 2 });
  const client: RunsClient = {
    equityCurve: jest.fn(async () => ({ dates: report.testDates, costBps: 1, convention: 'Growth of 1 after net costs', series: [{ strategy: 'lstm', wealth: [1.1234] }] })),
    allocations: jest.fn(async () => ({ assets: ['STOCK', 'BOND'], convention: 'Prior close target weights', strategies: [{ strategy: 'lstm', rows: [{ returnDate: report.testDates[0], weights: [0.6, 0.4] }] }] })),
    report: jest.fn(), manifest: jest.fn(), list: jest.fn(), submit: jest.fn(), status: jest.fn(), cancel: jest.fn(),
  };
  await render(<ResultSeries client={client} runId="run-layout" report={report} colors={dark} />);
  expect(await screen.findByText('LSTM wealth: 1.1234')).toBeTruthy();
  expect(screen.getByText('STOCK: 60.00%')).toBeTruthy();
  const strategy = screen.getByRole('button', { name: 'Inspect LSTM', selected: true });
  expect(strategy.parent).toHaveStyle({ flexDirection: 'column', alignItems: 'stretch' });
  expect(strategy).toHaveStyle({ minHeight: 48 });
  const previous = screen.getByRole('button', { name: 'Previous date', disabled: true });
  expect(previous.parent).toHaveStyle({ flexDirection: 'column' });
  await fireEvent.press(previous);
  expect(screen.getByText('Date: 2026-10-12 · 1 of 1')).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Next date', disabled: true })).toBeTruthy();
  expect(screen.getByRole('image').props.accessibilityLabel).toMatch(/Exact values for each date/);
});
