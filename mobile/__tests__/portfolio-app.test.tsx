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
    ['Lookback days', '0', /Lookback must be a whole number from 10 to 100/],
    ['Lookback days', 'not-a-number', /Lookback must be a whole number from 10 to 100/],
    ['Training epochs', '6', /Epochs must be a whole number from 1 to 5/],
  ])('validates %s value %s inline', async (label, invalidValue, error) => {
    await render(<App />);
    await fireEvent.press(screen.getByRole('button', { name: 'New experiment' }));
    const field = screen.getByLabelText(label);
    await fireEvent.changeText(field, invalidValue);
    await fireEvent(field, 'blur');
    expect(screen.getByText(error)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Start experiment' }).props.accessibilityState.disabled).toBe(true);
  });
});
