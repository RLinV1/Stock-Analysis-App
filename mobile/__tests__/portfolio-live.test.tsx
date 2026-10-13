import { fireEvent, render, screen } from '@testing-library/react-native';
import PortfolioApp from '../src/PortfolioApp';
import { RunsApiError } from '../src/api/client';
import type { ListOptions, RunsClient, RunsClientOptions } from '../src/api/client';
import type { AcceptedRun, ArtifactIndex, RunPage, RunState, RunStatus, RunSummary, SyntheticRequestV1 } from '../src/api/contract';

const RUN_ID = '11111111-2222-4333-8444-555555555555';
const ATTEMPT_ID = '66666666-7777-4888-9999-aaaaaaaaaaaa';
const BASE_URL = 'http://10.0.2.2:8080';
const TOKEN = 'operator-secret-token-0123';

function statusOf(state: RunState): RunStatus {
  return { runId: RUN_ID, state, attemptCount: 1, manifestAvailable: state === 'COMPLETE', errorCode: null };
}

function summaryOf(state: RunState): RunSummary {
  return { ...statusOf(state), createdAt: '2026-10-13T08:15:30.123456Z' };
}

const MANIFEST: ArtifactIndex = {
  run_id: RUN_ID,
  attempt_id: ATTEMPT_ID,
  kind: 'synthetic-a0',
  files: [
    { path: 'report.json', key: `runs/${RUN_ID}/report.json`, sha256: 'a'.repeat(64), bytes: 2048 },
    { path: 'weights.csv', key: `runs/${RUN_ID}/weights.csv`, sha256: 'b'.repeat(64), bytes: 1 },
  ],
};

type FakeClient = {
  submit: jest.Mock<Promise<AcceptedRun>, [SyntheticRequestV1, string]>;
  status: jest.Mock<Promise<RunStatus>, [string]>;
  cancel: jest.Mock<Promise<RunStatus>, [string]>;
  manifest: jest.Mock<Promise<ArtifactIndex>, [string]>;
  list: jest.Mock<Promise<RunPage>, [ListOptions?]>;
};

function fakeService(state: RunState = 'QUEUED') {
  const client: FakeClient = {
    submit: jest.fn<Promise<AcceptedRun>, [SyntheticRequestV1, string]>(async () => ({ runId: RUN_ID })),
    status: jest.fn<Promise<RunStatus>, [string]>(async () => statusOf(state)),
    cancel: jest.fn<Promise<RunStatus>, [string]>(async () => statusOf('CANCEL_REQUESTED')),
    manifest: jest.fn<Promise<ArtifactIndex>, [string]>(async () => MANIFEST),
    list: jest.fn<Promise<RunPage>, [ListOptions?]>(async () => ({ items: [summaryOf(state)], nextCursor: null })),
  };
  const createClient = jest.fn<RunsClient, [RunsClientOptions]>(() => client);
  return { client, createClient };
}

async function enterConnection(createClient: (options: RunsClientOptions) => RunsClient) {
  await render(<PortfolioApp createClient={createClient} />);
  await fireEvent.press(screen.getByRole('button', { name: 'Connect to service' }));
  expect(screen.getByRole('header', { name: 'Service connection' })).toBeTruthy();
  await fireEvent.changeText(screen.getByLabelText('Service base URL'), BASE_URL);
  await fireEvent.changeText(screen.getByLabelText('Operator token'), TOKEN);
  await fireEvent.press(screen.getByRole('button', { name: 'Connect' }));
}

describe('Portfolio Lab live service', () => {
  test('connects and shows a live run beside the labeled synthetic demo', async () => {
    const { client, createClient } = fakeService();
    await enterConnection(createClient);

    expect(await screen.findByText('Live experiments')).toBeTruthy();
    expect(createClient).toHaveBeenCalledWith({ baseUrl: BASE_URL, token: TOKEN });
    expect(client.list).toHaveBeenCalledWith({ limit: 20 });
    expect(screen.getByRole('header', { name: 'Experiments' })).toBeTruthy();
    expect(screen.getByText('Queued')).toBeTruthy();
    expect(screen.getByText('Created 2026-10-13 08:15:30 UTC')).toBeTruthy();
    expect(screen.getByText('Attempts: 1 · Run 11111111')).toBeTruthy();
    expect(screen.getByText('Synthetic demonstration')).toBeTruthy();
    expect(screen.queryByText('No live experiments yet')).toBeNull();
  });

  test('a rejected token shows an honest message and no live runs', async () => {
    const { client, createClient } = fakeService();
    client.list.mockRejectedValueOnce(new RunsApiError('http', 'Runs service returned HTTP 401.', 401));
    await enterConnection(createClient);

    expect(await screen.findByText(/Token rejected \(HTTP 401\)/)).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Service connection' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Disconnect' })).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: 'Back' }));
    expect(screen.getByText('No live experiments yet')).toBeTruthy();
    expect(screen.getByText(/Not connected/)).toBeTruthy();
    expect(screen.queryByText('Live experiments')).toBeNull();
    expect(screen.queryByText('Queued')).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: 'New experiment' }));
    expect(screen.getByRole('button', { name: 'Start experiment' }).props.accessibilityState.disabled).toBe(true);
    expect(screen.getByText(/Start unavailable: the service is not connected/)).toBeTruthy();
  });

  test('an unreachable service is reported without connecting', async () => {
    const { client, createClient } = fakeService();
    client.list.mockRejectedValueOnce(new RunsApiError('network', 'Runs service could not be reached.'));
    await enterConnection(createClient);

    expect(await screen.findByText(/Service unreachable/)).toBeTruthy();
    expect(screen.queryByText('Live experiments')).toBeNull();
  });

  test('never renders the operator token', async () => {
    const { createClient } = fakeService();
    await render(<PortfolioApp createClient={createClient} />);
    await fireEvent.press(screen.getByRole('button', { name: 'Connect to service' }));
    const tokenField = screen.getByLabelText('Operator token');
    expect(tokenField.props.secureTextEntry).toBe(true);
    expect(tokenField.props.autoCapitalize).toBe('none');
    expect(tokenField.props.autoCorrect).toBe(false);
    await fireEvent.changeText(screen.getByLabelText('Service base URL'), BASE_URL);
    await fireEvent.changeText(tokenField, TOKEN);
    expect(JSON.stringify(screen.toJSON())).not.toContain(TOKEN);

    await fireEvent.press(screen.getByRole('button', { name: 'Connect' }));
    expect(await screen.findByText('Live experiments')).toBeTruthy();
    expect(JSON.stringify(screen.toJSON())).not.toContain(TOKEN);
    expect(screen.queryByText(TOKEN)).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: 'Service settings' }));
    expect(JSON.stringify(screen.toJSON())).not.toContain(TOKEN);
  });

  test('submits the form values and reuses the idempotency key after a network error', async () => {
    const { client, createClient } = fakeService();
    client.submit.mockRejectedValueOnce(new RunsApiError('network', 'Runs service could not be reached.'));
    await enterConnection(createClient);
    await screen.findByText('Live experiments');

    await fireEvent.press(screen.getByRole('button', { name: 'New experiment' }));
    expect(screen.getByText(/420 observations, dataset seed 2026 · hidden size 64 · execution seed 7 · cost 1 bp/)).toBeTruthy();
    await fireEvent.changeText(screen.getByLabelText('Lookback days'), '30');
    await fireEvent.changeText(screen.getByLabelText('Training epochs'), '2');
    const start = screen.getByRole('button', { name: 'Start experiment' });
    expect(start.props.accessibilityState.disabled).toBe(false);

    await fireEvent.press(start);
    expect(await screen.findByText(/Service unreachable.*same idempotency key/)).toBeTruthy();
    expect(screen.getByRole('header', { name: 'New experiment' })).toBeTruthy();
    expect(screen.queryByText(/Run ID/)).toBeNull();

    await fireEvent.press(screen.getByRole('button', { name: 'Start experiment' }));
    expect(await screen.findByText('State: Queued')).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Experiment detail' })).toBeTruthy();
    expect(screen.getByText(`Run ID: ${RUN_ID}`)).toBeTruthy();

    const expected: SyntheticRequestV1 = {
      contract_version: 1,
      dataset: { kind: 'synthetic', observations: 420, seed: 2026 },
      model: { lookback: 30, hidden_size: 64, epochs: 2 },
      execution: { seed: 7, cost_bps: 1 },
    };
    expect(client.submit).toHaveBeenCalledTimes(2);
    const [[firstRequest, firstKey], [secondRequest, secondKey]] = client.submit.mock.calls;
    expect(firstRequest).toEqual(expected);
    expect(secondRequest).toEqual(expected);
    expect(firstKey).toMatch(/^draft-[a-z0-9]+-[a-z0-9]*$/);
    expect(secondKey).toBe(firstKey);
    expect(client.status).toHaveBeenCalledWith(RUN_ID);
  });

  test('cancel shows the state the service returned', async () => {
    const { client, createClient } = fakeService('RUNNING');
    await enterConnection(createClient);
    await screen.findByText('Live experiments');

    await fireEvent.press(screen.getByRole('button', { name: /Open run 11111111/ }));
    expect(await screen.findByText('State: Running')).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: 'Cancel run' }));

    expect(await screen.findByText('State: Cancellation requested')).toBeTruthy();
    expect(screen.getByText(/The service reports: Cancellation requested/)).toBeTruthy();
    expect(client.cancel).toHaveBeenCalledWith(RUN_ID);
    expect(screen.queryByRole('button', { name: 'Cancel run' })).toBeNull();
  });

  test('refresh fetches status again only when asked', async () => {
    const { client, createClient } = fakeService('QUEUED');
    await enterConnection(createClient);
    await screen.findByText('Live experiments');
    await fireEvent.press(screen.getByRole('button', { name: /Open run 11111111/ }));
    expect(await screen.findByText('State: Queued')).toBeTruthy();
    expect(client.status).toHaveBeenCalledTimes(1);

    client.status.mockResolvedValueOnce(statusOf('RUNNING'));
    await fireEvent.press(screen.getByRole('button', { name: 'Refresh status' }));
    expect(await screen.findByText('State: Running')).toBeTruthy();
    expect(client.status).toHaveBeenCalledTimes(2);
  });

  test('lists manifest files for a complete run without inventing metrics', async () => {
    const { client, createClient } = fakeService('COMPLETE');
    await enterConnection(createClient);
    await screen.findByText('Live experiments');

    await fireEvent.press(screen.getByRole('button', { name: /Open run 11111111/ }));
    expect(await screen.findByText('State: Complete')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Cancel run' })).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'View results' }));

    expect(await screen.findByText('report.json · 2048 bytes')).toBeTruthy();
    expect(screen.getByText('weights.csv · 1 byte')).toBeTruthy();
    expect(client.manifest).toHaveBeenCalledWith(RUN_ID);
    expect(screen.getByRole('header', { name: 'Results' })).toBeTruthy();
    expect(screen.getByText('Report viewer not built yet')).toBeTruthy();
    expect(screen.queryByText(/Sharpe/)).toBeNull();
    expect(screen.getByText(/Not investment advice/)).toBeTruthy();
  });
});
