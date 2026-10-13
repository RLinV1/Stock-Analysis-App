import { StatusBar } from 'expo-status-bar';
import { useEffect, useRef, useState } from 'react';
import { BackHandler, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, useColorScheme, View } from 'react-native';
import { createRunsClient, RunsApiError } from './api/client';
import type { RunsClient } from './api/client';
// Synthetic request v1 bounds live in ./api/contract (contracts/synthetic-run-request.v1.schema.json).
import { EPOCHS, LOOKBACK } from './api/contract';
import type { ArtifactIndex, RunState, RunStatus, RunSummary, SyntheticRequestV1 } from './api/contract';

type Page = 'experiments' | 'service' | 'new' | 'detail' | 'results' | 'run' | 'runResults';
type Colors = { bg: string; surface: string; text: string; secondary: string; accent: string; onAccent: string; border: string; muted: string; error: string };
const light: Colors = { bg: '#F3F5F8', surface: '#FFFFFF', text: '#182437', secondary: '#45566C', accent: '#174EA6', onAccent: '#FFFFFF', border: '#D6DFE8', muted: '#E8EDF3', error: '#A4262C' };
const dark: Colors = { bg: '#101923', surface: '#1A2837', text: '#F5F7FA', secondary: '#C4D0DE', accent: '#A4C8FF', onAccent: '#102641', border: '#38506A', muted: '#26394B', error: '#FFB4B4' };

// Fixed parts of the synthetic request v1 that the form does not expose yet; shown on screen before Start.
const FIXED = { observations: 420, datasetSeed: 2026, hiddenSize: 64, executionSeed: 7, costBps: 1 };
const LIST_PAGE_SIZE = 20;

const STATE_LABEL: Record<RunState, string> = {
  QUEUED: 'Queued',
  RUNNING: 'Running',
  CANCEL_REQUESTED: 'Cancellation requested',
  CANCELLED: 'Cancelled',
  COMPLETE: 'Complete',
  FAILED: 'Failed',
};

const STATE_EXPLANATION: Record<RunState, string> = {
  QUEUED: 'Waiting for the worker to claim this run.',
  RUNNING: 'The worker reports this run in progress. No completion percentage is available.',
  CANCEL_REQUESTED: 'The run stays pending until the worker confirms it stopped. Refresh to check.',
  CANCELLED: 'The service reports this run was cancelled.',
  COMPLETE: 'The service reports this run finished. Its result files are listed under Results.',
  FAILED: 'The service reports this run failed.',
};

type Operation = 'connect' | 'list' | 'submit' | 'status' | 'cancel' | 'manifest';

// Maps a client failure to an honest, token-free message. Never implies the service confirmed anything.
function describeFailure(error: unknown, operation: Operation): string {
  let message = 'Unexpected error. The service confirmed nothing.';
  let uncertain = false;
  if (error instanceof RunsApiError) {
    if (error.kind === 'network') { message = 'Service unreachable. Check the base URL and that the service is running on this network.'; uncertain = true; }
    else if (error.kind === 'timeout') { message = 'The service did not respond in time.'; uncertain = true; }
    else if (error.kind === 'http' && error.status === 401) message = 'Token rejected (HTTP 401). Check the operator token.';
    else if (error.kind === 'http') message = `The service returned HTTP ${error.status ?? 'error'}${error.code ? ` (${error.code})` : ''}.`;
    else if (error.kind === 'invalid_response') { message = 'Response not understood. The service may run a different API version.'; uncertain = true; }
    else if (error.kind === 'invalid_input') message = error.message;
  }
  if (operation === 'submit') {
    return uncertain
      ? `${message} The service may or may not have received the request. Start again resends it with the same idempotency key.`
      : `${message} No experiment was accepted.`;
  }
  if (operation === 'cancel') return `${message} Cancellation is not confirmed.`;
  return message;
}

function newDraftKey() {
  // Uniqueness, not secrecy: the key only lets the service recognise a retried submission.
  return `draft-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

// Server instants are ISO-8601 UTC strings; show them without local-time conversion.
function formatInstant(iso: string) {
  const [date, time = ''] = iso.split('T');
  return `${date} ${time.slice(0, 8)} UTC`;
}

function nowLabel() {
  return formatInstant(new Date().toISOString());
}

function shortId(runId: string) {
  return runId.slice(0, 8);
}

function buildRequest(lookback: number, epochs: number): SyntheticRequestV1 {
  return {
    contract_version: 1,
    dataset: { kind: 'synthetic', observations: FIXED.observations, seed: FIXED.datasetSeed },
    model: { lookback, hidden_size: FIXED.hiddenSize, epochs },
    execution: { seed: FIXED.executionSeed, cost_bps: FIXED.costBps },
  };
}

function Action({ label, onPress, colors, disabled = false, quiet = false }: { label: string; onPress: () => void; colors: Colors; disabled?: boolean; quiet?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} disabled={disabled} onPress={onPress} style={({ pressed }) => [styles.action, { backgroundColor: disabled ? colors.muted : quiet ? colors.surface : colors.accent, borderColor: quiet ? colors.border : 'transparent', opacity: pressed ? 0.72 : 1 }]}>
    <Text style={[styles.actionText, { color: disabled ? colors.secondary : quiet ? colors.text : colors.onAccent }]}>{label}</Text>
  </Pressable>;
}

function Card({ children, colors }: { children: React.ReactNode; colors: Colors }) {
  return <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>{children}</View>;
}

function RunRow({ run, colors, onPress }: { run: RunSummary; colors: Colors; onPress: () => void }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={`Open run ${shortId(run.runId)}, ${STATE_LABEL[run.state]}`} onPress={onPress} style={({ pressed }) => [styles.runRow, { borderColor: colors.border, backgroundColor: colors.bg, opacity: pressed ? 0.72 : 1 }]}>
    <Text style={[styles.runState, { color: colors.text }]}>{STATE_LABEL[run.state]}</Text>
    <Text style={[styles.runMeta, { color: colors.secondary }]}>{`Created ${formatInstant(run.createdAt)}`}</Text>
    <Text style={[styles.runMeta, { color: colors.secondary }]}>{`Attempts: ${run.attemptCount} · Run ${shortId(run.runId)}`}</Text>
  </Pressable>;
}

function integerInRange(value: string, min: number, max: number) {
  return /^\d+$/.test(value) && Number(value) >= min && Number(value) <= max;
}

export type PortfolioAppProps = { createClient?: typeof createRunsClient };

export default function PortfolioApp({ createClient = createRunsClient }: PortfolioAppProps = {}) {
  const isDark = useColorScheme() === 'dark';
  const colors = isDark ? dark : light;
  const [stack, setStack] = useState<Page[]>(['experiments']);
  const [lookback, setLookback] = useState('50');
  const [epochs, setEpochs] = useState('3');
  const [edited, setEdited] = useState({ lookback: false, epochs: false });

  // Service connection: memory only, never persisted. The token is never rendered back.
  const [baseUrl, setBaseUrl] = useState('');
  const [token, setToken] = useState('');
  const [tokenFieldKey, setTokenFieldKey] = useState(0);
  const [client, setClient] = useState<RunsClient | null>(null);
  const [connectedUrl, setConnectedUrl] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState<string | null>(null);
  const generation = useRef(0);

  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [listFetchedAt, setListFetchedAt] = useState<string | null>(null);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);

  const draft = useRef<{ key: string; sentBody: string | null }>({ key: newDraftKey(), sentBody: null });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const [statusFetchedAt, setStatusFetchedAt] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [cancelNote, setCancelNote] = useState<string | null>(null);
  const statusSeq = useRef(0);

  const [manifest, setManifest] = useState<ArtifactIndex | null>(null);
  const [manifestLoading, setManifestLoading] = useState(false);
  const [manifestError, setManifestError] = useState<string | null>(null);
  const manifestSeq = useRef(0);

  const page = stack[stack.length - 1];
  const connected = client !== null;
  const back = () => setStack((current) => current.length > 1 ? current.slice(0, -1) : current);
  const open = (next: Page) => setStack((current) => [...current, next]);

  useEffect(() => {
    if (Platform.OS !== 'android' || stack.length === 1) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => { back(); return true; });
    return () => subscription.remove();
  }, [stack.length]);

  function resetLive() {
    setRuns([]);
    setListFetchedAt(null);
    setListError(null);
    setSubmitError(null);
    setSelectedRunId(null);
    setRunStatus(null);
    setStatusFetchedAt(null);
    setStatusError(null);
    setCancelNote(null);
    setManifest(null);
    setManifestError(null);
  }

  function forgetToken() {
    setToken('');
    setTokenFieldKey((key) => key + 1);
  }

  async function connect() {
    const gen = ++generation.current;
    setConnecting(true);
    setConnectError(null);
    setClient(null);
    resetLive();
    try {
      const url = baseUrl.trim();
      const candidate = createClient({ baseUrl: url, token });
      const firstPage = await candidate.list({ limit: LIST_PAGE_SIZE });
      if (gen !== generation.current) return;
      setClient(candidate);
      setConnectedUrl(url);
      setRuns(firstPage.items);
      setListFetchedAt(nowLabel());
      forgetToken();
      setStack(['experiments']);
    } catch (error) {
      if (gen === generation.current) setConnectError(describeFailure(error, 'connect'));
    } finally {
      if (gen === generation.current) setConnecting(false);
    }
  }

  function disconnect() {
    generation.current += 1;
    setClient(null);
    setConnectedUrl('');
    setConnecting(false);
    setConnectError(null);
    setSubmitting(false);
    setStatusLoading(false);
    setCancelling(false);
    setManifestLoading(false);
    setListLoading(false);
    resetLive();
    forgetToken();
  }

  async function refreshRuns(active: RunsClient | null = client) {
    if (!active) return;
    const gen = generation.current;
    setListLoading(true);
    setListError(null);
    try {
      const result = await active.list({ limit: LIST_PAGE_SIZE });
      if (gen !== generation.current) return;
      setRuns(result.items);
      setListFetchedAt(nowLabel());
    } catch (error) {
      if (gen === generation.current) setListError(describeFailure(error, 'list'));
    } finally {
      if (gen === generation.current) setListLoading(false);
    }
  }

  async function loadStatus(runId: string, active: RunsClient | null = client) {
    if (!active) return;
    const seq = ++statusSeq.current;
    const gen = generation.current;
    const current = () => seq === statusSeq.current && gen === generation.current;
    setStatusLoading(true);
    setStatusError(null);
    try {
      const status = await active.status(runId);
      if (!current()) return;
      setRunStatus(status);
      setStatusFetchedAt(nowLabel());
    } catch (error) {
      if (current()) setStatusError(describeFailure(error, 'status'));
    } finally {
      if (current()) setStatusLoading(false);
    }
  }

  async function cancelRun() {
    if (!client || !runStatus) return;
    const seq = ++statusSeq.current;
    const gen = generation.current;
    setCancelling(true);
    setStatusError(null);
    setCancelNote(null);
    try {
      const status = await client.cancel(runStatus.runId);
      if (seq !== statusSeq.current || gen !== generation.current) return;
      setRunStatus(status);
      setStatusFetchedAt(nowLabel());
      setCancelNote(`Cancel request sent. The service reports: ${STATE_LABEL[status.state]}.`);
    } catch (error) {
      if (seq === statusSeq.current && gen === generation.current) setStatusError(describeFailure(error, 'cancel'));
    } finally {
      if (gen === generation.current) setCancelling(false);
    }
  }

  async function loadManifest(runId: string) {
    if (!client) return;
    const seq = ++manifestSeq.current;
    const gen = generation.current;
    const current = () => seq === manifestSeq.current && gen === generation.current;
    setManifest(null);
    setManifestLoading(true);
    setManifestError(null);
    try {
      const index = await client.manifest(runId);
      if (current()) setManifest(index);
    } catch (error) {
      if (current()) setManifestError(describeFailure(error, 'manifest'));
    } finally {
      if (current()) setManifestLoading(false);
    }
  }

  function openNew() {
    // One idempotency key per opened draft; retries of the same request reuse it.
    draft.current = { key: newDraftKey(), sentBody: null };
    setSubmitError(null);
    open('new');
  }

  function openRun(runId: string, active: RunsClient | null = client) {
    setSelectedRunId(runId);
    setRunStatus(null);
    setStatusFetchedAt(null);
    setCancelNote(null);
    setManifest(null);
    setManifestError(null);
    void loadStatus(runId, active);
  }

  const draftValid = integerInRange(lookback, LOOKBACK.min, LOOKBACK.max) && integerInRange(epochs, EPOCHS.min, EPOCHS.max);

  async function submit() {
    const active = client;
    if (!active || !draftValid || submitting) return;
    const request = buildRequest(Number(lookback), Number(epochs));
    const body = JSON.stringify(request);
    // A changed request must not reuse a key the service may already bind to different values.
    if (draft.current.sentBody !== null && draft.current.sentBody !== body) draft.current = { key: newDraftKey(), sentBody: null };
    draft.current.sentBody = body;
    const gen = generation.current;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const accepted = await active.submit(request, draft.current.key);
      if (gen !== generation.current) return;
      setStack((current) => [...current.filter((entry) => entry !== 'new'), 'run']);
      openRun(accepted.runId, active);
      void refreshRuns(active);
    } catch (error) {
      if (gen === generation.current) setSubmitError(describeFailure(error, 'submit'));
    } finally {
      if (gen === generation.current) setSubmitting(false);
    }
  }

  const title = { experiments: 'Experiments', service: 'Service connection', new: 'New experiment', detail: 'Experiment detail', results: 'Results', run: 'Experiment detail', runResults: 'Results' }[page];
  const text = (value: string, secondary = false) => <Text style={[styles.body, { color: secondary ? colors.secondary : colors.text }]}>{value}</Text>;
  const alertText = (value: string) => <Text accessibilityRole="alert" style={[styles.error, { color: colors.error }]}>{value}</Text>;
  const notice = <Text style={[styles.notice, { color: colors.secondary }]}>Research only. Not investment advice. Historical examples do not predict future returns.</Text>;
  const cancellable = runStatus !== null && (runStatus.state === 'QUEUED' || runStatus.state === 'RUNNING');

  let startHelper = 'Start unavailable: the service is not connected. No job is queued.';
  if (connected) {
    if (submitting) startHelper = 'Submitting… waiting for the service to accept the request. No job ID yet.';
    else if (!draftValid) startHelper = 'Start unavailable until lookback and epochs are within their bounds.';
    else startHelper = 'Start sends this request to the connected service.';
  }

  return <View style={[styles.root, { backgroundColor: colors.bg }]}>
    <StatusBar style={isDark ? 'light' : 'dark'} />
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      {stack.length > 1 && <View style={styles.backRow}><Action label="Back" onPress={back} colors={colors} quiet /></View>}
      <Text style={[styles.eyebrow, { color: colors.accent }]}>PORTFOLIO LAB</Text>
      <Text accessibilityRole="header" style={[styles.title, { color: colors.text }]}>{title}</Text>
      <Text style={[styles.subheading, { color: colors.secondary }]}>{connected ? 'Research workspace · connected service' : 'Research workspace · local preview'}</Text>

      {page === 'experiments' && <>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Service connection</Text>
          {connected
            ? text(`Connected to ${connectedUrl}.${listFetchedAt ? ` List fetched ${listFetchedAt}; it does not update by itself.` : ''}`, true)
            : text('Not connected. Live runs, submission and cancellation stay unavailable.', true)}
          {connected && <Action label={listLoading ? 'Refreshing list…' : 'Refresh list'} onPress={() => { void refreshRuns(); }} colors={colors} disabled={listLoading} quiet />}
          {listError && alertText(listError)}
          <Action label={connected ? 'Service settings' : 'Connect to service'} onPress={() => open('service')} colors={colors} quiet />
        </Card>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Synthetic demonstration</Text>
          {text('Explore how a research run will look. This is sample content, not a submitted job or a historical result.', true)}
          <Action label="Open demo experiment" onPress={() => open('detail')} colors={colors} />
        </Card>
        {connected && runs.length > 0 ? <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Live experiments</Text>
          {text('Runs reported by the connected service. Every run uses the synthetic dataset.', true)}
          {runs.map((run) => <RunRow key={run.runId} run={run} colors={colors} onPress={() => { openRun(run.runId); open('run'); }} />)}
          <Action label="New experiment" onPress={openNew} colors={colors} quiet />
        </Card> : <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>No live experiments yet</Text>
          {text(connected
            ? 'The connected service reports no runs. Start one from New experiment.'
            : 'The research service is not connected. You can inspect the planned settings, but cannot start a run yet.', true)}
          <Action label="New experiment" onPress={openNew} colors={colors} quiet />
        </Card>}
      </>}

      {page === 'service' && <Card colors={colors}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>Runs service</Text>
        {text('The address and token stay in memory only. They are forgotten when the app closes and are never shown again.', true)}
        <Text style={[styles.fieldLabel, { color: colors.text }]}>Service base URL</Text>
        <TextInput accessibilityLabel="Service base URL" autoCapitalize="none" autoCorrect={false} keyboardType="url" onChangeText={setBaseUrl} placeholder="http://192.168.1.20:8080" placeholderTextColor={colors.secondary} style={[styles.input, { borderColor: colors.border, color: colors.text, backgroundColor: colors.bg }]} value={baseUrl} />
        <Text style={[styles.fieldLabel, { color: colors.text }]}>Operator token</Text>
        <TextInput key={tokenFieldKey} accessibilityLabel="Operator token" autoCapitalize="none" autoCorrect={false} onChangeText={setToken} secureTextEntry style={[styles.input, { borderColor: colors.border, color: colors.text, backgroundColor: colors.bg }]} />
        <View style={styles.gap} />
        <Action label="Connect" onPress={() => { void connect(); }} colors={colors} disabled={connecting || baseUrl.trim() === '' || token === ''} />
        {connecting && <Text style={[styles.helper, { color: colors.secondary }]}>Connecting… nothing is shown until the service responds.</Text>}
        {connectError && alertText(connectError)}
        {connected && <>
          <Text style={[styles.helper, { color: colors.secondary }]}>{`Connected to ${connectedUrl}. Enter the token again to reconnect.`}</Text>
          <Action label="Disconnect" onPress={disconnect} colors={colors} quiet />
        </>}
      </Card>}

      {page === 'new' && <Card colors={colors}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>{connected ? 'Experiment settings' : 'Preview settings'}</Text>
        {text(connected
          ? 'Synthetic sample · LSTM research baseline. Start sends these settings to the connected service.'
          : 'Synthetic sample · LSTM research baseline. These fields are a local preview; no experiment will be sent.', true)}
        <Text style={[styles.fieldLabel, { color: colors.text }]}>Lookback days</Text>
        <TextInput accessibilityLabel="Lookback days" keyboardType="number-pad" onBlur={() => setEdited((current) => ({ ...current, lookback: true }))} onChangeText={setLookback} style={[styles.input, { borderColor: colors.border, color: colors.text, backgroundColor: colors.bg }]} value={lookback} />
        {edited.lookback && !integerInRange(lookback, LOOKBACK.min, LOOKBACK.max) && <Text accessibilityRole="alert" style={[styles.error, { color: colors.error }]}>{`Lookback must be a whole number from ${LOOKBACK.min} to ${LOOKBACK.max}.`}</Text>}
        <Text style={[styles.fieldLabel, { color: colors.text }]}>Training epochs</Text>
        <TextInput accessibilityLabel="Training epochs" keyboardType="number-pad" onBlur={() => setEdited((current) => ({ ...current, epochs: true }))} onChangeText={setEpochs} style={[styles.input, { borderColor: colors.border, color: colors.text, backgroundColor: colors.bg }]} value={epochs} />
        {edited.epochs && !integerInRange(epochs, EPOCHS.min, EPOCHS.max) && <Text accessibilityRole="alert" style={[styles.error, { color: colors.error }]}>{`Epochs must be a whole number from ${EPOCHS.min} to ${EPOCHS.max}.`}</Text>}
        {connected && <Text style={[styles.helper, { color: colors.secondary }]}>{`Fixed for this request: synthetic dataset, ${FIXED.observations} observations, dataset seed ${FIXED.datasetSeed} · hidden size ${FIXED.hiddenSize} · execution seed ${FIXED.executionSeed} · cost ${FIXED.costBps} bp.`}</Text>}
        <View style={styles.gap} />
        <Action label="Start experiment" onPress={() => { void submit(); }} colors={colors} disabled={!connected || !draftValid || submitting} />
        <Text style={[styles.helper, { color: colors.secondary }]}>{startHelper}</Text>
        {submitError && alertText(submitError)}
      </Card>}

      {page === 'detail' && <Card colors={colors}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>Synthetic preview</Text>
        {text('Model: 64-unit LSTM · Dataset: synthetic sample · Status: preview only.', true)}
        {text('No job ID exists. No worker is running. Cancellation is unavailable for sample content.', true)}
        <Action label="View results" onPress={() => open('results')} colors={colors} />
      </Card>}

      {page === 'results' && <>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Report preview · synthetic data</Text>
          {text('No measured run is loaded. Performance and allocations are unavailable until a real experiment finishes.', true)}
        </Card>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Comparison</Text>
          {text('LSTM Sharpe ratio: unavailable — no measured run.')}
          {text('Equal-weight baseline Sharpe ratio: unavailable — no measured run.')}
          {text('Both strategies must use identical dates and costs before a number appears here.', true)}
        </Card>
        {notice}
      </>}

      {page === 'run' && <Card colors={colors}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>Live run · synthetic data</Text>
        {selectedRunId && text(`Run ID: ${selectedRunId}`, true)}
        {runStatus && <>
          {text(`State: ${STATE_LABEL[runStatus.state]}`)}
          {text(STATE_EXPLANATION[runStatus.state], true)}
          {text(`Attempts: ${runStatus.attemptCount}`, true)}
          {runStatus.errorCode ? text(`Error code: ${runStatus.errorCode}`, true) : null}
          {statusFetchedAt && text(`Status fetched ${statusFetchedAt}. It does not update by itself.`, true)}
        </>}
        {statusLoading && text(runStatus ? 'Refreshing status…' : 'Loading status from the service…', true)}
        {cancelNote && text(cancelNote)}
        {statusError && alertText(statusError)}
        <Action label="Refresh status" onPress={() => { if (selectedRunId) void loadStatus(selectedRunId); }} colors={colors} disabled={!connected || statusLoading || cancelling || selectedRunId === null} quiet />
        {cancellable && <Action label="Cancel run" onPress={() => { void cancelRun(); }} colors={colors} disabled={!connected || cancelling || statusLoading} quiet />}
        {cancelling && <Text style={[styles.helper, { color: colors.secondary }]}>Sending cancellation… not confirmed yet.</Text>}
        {runStatus?.state === 'COMPLETE' && <Action label="View results" onPress={() => { open('runResults'); void loadManifest(runStatus.runId); }} colors={colors} />}
      </Card>}

      {page === 'runResults' && <>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Result files · synthetic data</Text>
          {manifestLoading && text('Loading the artifact manifest…', true)}
          {manifestError && <>
            {alertText(manifestError)}
            <Action label="Retry" onPress={() => { if (selectedRunId) void loadManifest(selectedRunId); }} colors={colors} disabled={!connected || manifestLoading} quiet />
          </>}
          {manifest && <>
            {text(`Attempt ${manifest.attempt_id}`, true)}
            {manifest.files.map((file) => <Text key={file.path} style={[styles.fileRow, { color: colors.text }]}>{`${file.path} · ${file.bytes} ${file.bytes === 1 ? 'byte' : 'bytes'}`}</Text>)}
          </>}
        </Card>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Report viewer not built yet</Text>
          {text('This app does not read report contents yet, so no metrics, allocations or comparisons are shown for this run.', true)}
        </Card>
        {notice}
      </>}
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { flexGrow: 1, width: '100%', maxWidth: 720, alignSelf: 'center', paddingHorizontal: 20, paddingTop: Platform.OS === 'android' ? 48 : 32, paddingBottom: 48 },
  backRow: { alignSelf: 'flex-start', marginBottom: 20 },
  eyebrow: { fontSize: 12, fontWeight: '700', letterSpacing: 1.5, marginBottom: 8 },
  title: { fontSize: 34, lineHeight: 40, fontWeight: '700' },
  subheading: { fontSize: 14, lineHeight: 21, marginTop: 6, marginBottom: 24 },
  card: { borderWidth: 1, borderRadius: 20, padding: 20, marginBottom: 16 },
  cardTitle: { fontSize: 20, lineHeight: 27, fontWeight: '700', marginBottom: 8 },
  body: { fontSize: 16, lineHeight: 24, marginBottom: 8 },
  gap: { height: 10 },
  action: { minHeight: 52, borderRadius: 14, borderWidth: 1, paddingHorizontal: 18, justifyContent: 'center', alignItems: 'center', marginTop: 10 },
  actionText: { fontSize: 16, lineHeight: 22, fontWeight: '600', textAlign: 'center' },
  fieldLabel: { fontSize: 15, fontWeight: '600', marginTop: 16, marginBottom: 8 },
  input: { minHeight: 52, borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, fontSize: 16 },
  error: { fontSize: 14, lineHeight: 21, marginTop: 6 },
  helper: { fontSize: 14, lineHeight: 21, marginTop: 12 },
  notice: { fontSize: 14, lineHeight: 21, marginTop: 4 },
  runRow: { minHeight: 52, borderWidth: 1, borderRadius: 14, paddingHorizontal: 16, paddingVertical: 12, marginTop: 10, justifyContent: 'center' },
  runState: { fontSize: 16, lineHeight: 22, fontWeight: '600' },
  runMeta: { fontSize: 14, lineHeight: 20 },
  fileRow: { fontSize: 15, lineHeight: 22, marginTop: 6 },
});
