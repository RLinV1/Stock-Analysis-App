import { fireEvent, render, screen } from '@testing-library/react-native';
import App from '../App';

describe('Portfolio Lab preview', () => {
  test('identifies synthetic content and never presents a live job', async () => {
    await render(<App />);

    expect(screen.getByRole('header', { name: 'Experiments' })).toBeTruthy();
    expect(screen.getByText('Synthetic demonstration')).toBeTruthy();
    expect(screen.getByText(/not a submitted job or a historical result/i)).toBeTruthy();
    expect(screen.getByText('No live experiments yet')).toBeTruthy();
  });

  test('navigates to the sample report with truthful comparison and research notice', async () => {
    await render(<App />);

    await fireEvent.press(screen.getByRole('button', { name: 'Open demo experiment' }));
    expect(screen.getByRole('header', { name: 'Experiment detail' })).toBeTruthy();
    expect(screen.getByText(/No job ID exists/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /cancel/i })).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: 'View results' }));
    expect(screen.getByRole('header', { name: 'Results' })).toBeTruthy();
    expect(screen.getByText('Report preview · synthetic data')).toBeTruthy();
    expect(screen.getByText(/LSTM Sharpe ratio: unavailable — no measured run/)).toBeTruthy();
    expect(screen.getByText(/Equal-weight baseline Sharpe ratio: unavailable — no measured run/)).toBeTruthy();
    expect(screen.getByText(/Not investment advice/)).toBeTruthy();
  });

  test('provides named Back navigation on deeper screens', async () => {
    await render(<App />);
    await fireEvent.press(screen.getByRole('button', { name: 'Open demo experiment' }));
    await fireEvent.press(screen.getByRole('button', { name: 'View results' }));

    await fireEvent.press(screen.getByRole('button', { name: 'Back' }));
    expect(screen.getByRole('header', { name: 'Experiment detail' })).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Back' }));
    expect(screen.getByRole('header', { name: 'Experiments' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Back' })).toBeNull();
  });

  test('activates navigation on release rather than press-down', async () => {
    await render(<App />);
    const open = screen.getByRole('button', { name: 'Open demo experiment' });
    expect(open).toHaveStyle({ minHeight: 52, minWidth: 48, paddingVertical: 12 });
    await fireEvent(open, 'pressIn');
    expect(screen.getByRole('header', { name: 'Experiments' })).toBeTruthy();
    await fireEvent(open, 'pressOut');
    expect(screen.getByRole('header', { name: 'Experiments' })).toBeTruthy();
    await fireEvent.press(open);
    expect(screen.getByRole('header', { name: 'Experiment detail' })).toBeTruthy();
  });

  test('keeps submission disabled while the service is absent', async () => {
    await render(<App />);
    await fireEvent.press(screen.getByRole('button', { name: 'New experiment' }));

    const start = screen.getByRole('button', { name: 'Start experiment' });
    expect(start.props.accessibilityState.disabled).toBe(true);
    expect(screen.getByText(/Start unavailable: the service is not connected/)).toBeTruthy();
    await fireEvent.press(start);
    expect(screen.getByRole('header', { name: 'New experiment' })).toBeTruthy();
    expect(screen.queryByText(/accepted job/i)).toBeNull();
  });

  test.each([
    ['Lookback days', '0', /Lookback must be a whole number from 10 to 50/],
    ['Lookback days', 'not-a-number', /Lookback must be a whole number from 10 to 50/],
    ['Lookback days', '51', /Lookback must be a whole number from 10 to 50/],
    ['Training epochs', '0', /Epochs must be a whole number from 1 to 3/],
    ['Training epochs', '4', /Epochs must be a whole number from 1 to 3/],
  ])('validates %s value %s inline', async (label, invalidValue, error) => {
    await render(<App />);
    await fireEvent.press(screen.getByRole('button', { name: 'New experiment' }));
    const field = screen.getByLabelText(label);
    await fireEvent.changeText(field, invalidValue);
    await fireEvent(field, 'blur');
    expect(screen.getByText(error)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Start experiment' }).props.accessibilityState.disabled).toBe(true);
  });

  test.each([
    ['Lookback days', '10'],
    ['Lookback days', '50'],
    ['Training epochs', '1'],
    ['Training epochs', '3'],
  ])('accepts %s boundary value %s', async (label, value) => {
    await render(<App />);
    await fireEvent.press(screen.getByRole('button', { name: 'New experiment' }));
    const field = screen.getByLabelText(label);
    await fireEvent.changeText(field, value);
    await fireEvent(field, 'blur');
    expect(screen.queryByRole('alert')).toBeNull();
  });
});
