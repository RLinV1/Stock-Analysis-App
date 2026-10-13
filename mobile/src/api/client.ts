import { LIST_LIMIT, RUN_STATES, validateRequest } from './contract';
import type { AcceptedRun, ArtifactFile, ArtifactIndex, RunPage, RunState, RunStatus, RunSummary, SyntheticRequestV1 } from './contract';

// Typed client for the local runs API (contracts/runs-api.v1.openapi.yaml).
// It never fabricates a run ID or state: every failure throws RunsApiError.

export type RunsApiErrorKind = 'network' | 'timeout' | 'http' | 'invalid_response' | 'invalid_input';

export class RunsApiError extends Error {
  readonly kind: RunsApiErrorKind;
  readonly status?: number;
  readonly code?: string;

  constructor(kind: RunsApiErrorKind, message: string, status?: number, code?: string) {
    super(message);
    this.name = 'RunsApiError';
    this.kind = kind;
    this.status = status;
    this.code = code;
  }
}

export type FetchResponse = { ok: boolean; status: number; text(): Promise<string> };
export type FetchInit = { method: string; headers: Record<string, string>; body?: string; signal: AbortSignal };
export type FetchLike = (url: string, init: FetchInit) => Promise<FetchResponse>;

export type RunsClientOptions = { baseUrl: string; token: string; fetchImpl?: FetchLike; timeoutMs?: number };

export type RunsClient = {
  submit(request: SyntheticRequestV1, idempotencyKey: string): Promise<AcceptedRun>;
  status(runId: string): Promise<RunStatus>;
  cancel(runId: string): Promise<RunStatus>;
  manifest(runId: string): Promise<ArtifactIndex>;
  list(options?: ListOptions): Promise<RunPage>;
};

export type ListOptions = { limit?: number; cursor?: string };

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const IDEMPOTENCY_KEY = /^[A-Za-z0-9._:-]{1,128}$/;
const SHA256 = /^[0-9a-f]{64}$/;
const INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z$/;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isUuid(value: unknown): value is string {
  return typeof value === 'string' && UUID.test(value);
}

function invalidResponse(what: string): never {
  throw new RunsApiError('invalid_response', `Unexpected ${what} response from the runs service.`);
}

function parseAccepted(body: unknown): AcceptedRun {
  if (!isObject(body) || !isUuid(body.runId)) return invalidResponse('submit');
  return { runId: body.runId };
}

function parseStatus(body: unknown): RunStatus {
  if (!isObject(body)) return invalidResponse('status');
  const { runId, state, attemptCount, manifestAvailable, errorCode } = body;
  if (!isUuid(runId)
    || typeof state !== 'string' || !(RUN_STATES as readonly string[]).includes(state)
    || typeof attemptCount !== 'number' || !Number.isInteger(attemptCount) || attemptCount < 0
    || typeof manifestAvailable !== 'boolean'
    || (errorCode !== undefined && errorCode !== null && typeof errorCode !== 'string')) {
    return invalidResponse('status');
  }
  return { runId, state: state as RunState, attemptCount, manifestAvailable, errorCode: typeof errorCode === 'string' ? errorCode : null };
}

function parseFile(file: unknown): ArtifactFile {
  if (!isObject(file)) return invalidResponse('manifest');
  const { path, key, sha256, bytes } = file;
  if (typeof path !== 'string' || path.length === 0 || typeof key !== 'string' || key.length === 0
    || typeof sha256 !== 'string' || !SHA256.test(sha256)
    || typeof bytes !== 'number' || !Number.isInteger(bytes) || bytes < 0) {
    return invalidResponse('manifest');
  }
  return { path, key, sha256, bytes };
}

function parseManifest(body: unknown): ArtifactIndex {
  if (!isObject(body) || !isUuid(body.run_id) || !isUuid(body.attempt_id) || body.kind !== 'synthetic-a0'
    || !Array.isArray(body.files) || body.files.length === 0) {
    return invalidResponse('manifest');
  }
  const files = body.files.map(parseFile);
  if (!files.some((file) => file.path === 'report.json')) invalidResponse('manifest');
  return { run_id: body.run_id, attempt_id: body.attempt_id, kind: 'synthetic-a0', files };
}

function parseSummary(item: unknown): RunSummary {
  if (!isObject(item) || typeof item.createdAt !== 'string' || !INSTANT.test(item.createdAt)) return invalidResponse('list');
  let status: RunStatus;
  try {
    status = parseStatus(item);
  } catch {
    return invalidResponse('list');
  }
  return { ...status, createdAt: item.createdAt };
}

function parsePage(body: unknown): RunPage {
  if (!isObject(body) || !Array.isArray(body.items)) return invalidResponse('list');
  const { nextCursor } = body;
  if (nextCursor !== undefined && nextCursor !== null && !isUuid(nextCursor)) return invalidResponse('list');
  return { items: body.items.map(parseSummary), nextCursor: isUuid(nextCursor) ? nextCursor : null };
}

function problemCode(text: string): string | undefined {
  try {
    const body: unknown = JSON.parse(text);
    return isObject(body) && typeof body.code === 'string' ? body.code : undefined;
  } catch {
    return undefined;
  }
}

function requireRunId(runId: string) {
  if (!isUuid(runId)) throw new RunsApiError('invalid_input', 'Run ID must be a UUID.');
}

// A status for a different run than requested is a server fault, never a result to show.
function statusFor(runId: string) {
  return (body: unknown) => {
    const status = parseStatus(body);
    if (status.runId.toLowerCase() !== runId.toLowerCase()) return invalidResponse('status');
    return status;
  };
}

export function createRunsClient({ baseUrl, token, fetchImpl = fetch, timeoutMs = 15000 }: RunsClientOptions): RunsClient {
  if (!/^https?:\/\//.test(baseUrl)) throw new RunsApiError('invalid_input', 'Base URL must start with http:// or https://.');
  const root = baseUrl.replace(/\/+$/, '');

  async function call<T>(method: 'GET' | 'POST', path: string, parse: (body: unknown) => T, extra?: { headers: Record<string, string>; body: string }): Promise<T> {
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
    try {
      let response: FetchResponse;
      let text: string;
      try {
        response = await fetchImpl(`${root}${path}`, {
          method,
          headers: { Accept: 'application/json', Authorization: `Bearer ${token}`, ...extra?.headers },
          body: extra?.body,
          signal: controller.signal,
        });
        text = await response.text();
      } catch {
        if (timedOut) throw new RunsApiError('timeout', `Runs service did not respond within ${timeoutMs} ms.`);
        throw new RunsApiError('network', 'Runs service could not be reached.');
      }
      if (!response.ok) {
        const code = problemCode(text) ?? (response.status === 404 && text.trim() === '' ? 'not_found' : undefined);
        throw new RunsApiError('http', `Runs service returned HTTP ${response.status}${code ? ` (${code})` : ''}.`, response.status, code);
      }
      let body: unknown;
      try {
        body = JSON.parse(text);
      } catch {
        throw new RunsApiError('invalid_response', 'Runs service returned a body that is not JSON.');
      }
      return parse(body);
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    async submit(request, idempotencyKey) {
      const problems = validateRequest(request);
      if (problems.length > 0) throw new RunsApiError('invalid_input', `Invalid request: ${problems.join(' ')}`);
      if (typeof idempotencyKey !== 'string' || !IDEMPOTENCY_KEY.test(idempotencyKey)) {
        throw new RunsApiError('invalid_input', 'Idempotency key must be 1-128 characters of A-Z, a-z, 0-9, ".", "_", ":" or "-".');
      }
      return call('POST', '/api/v1/runs', parseAccepted, {
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idempotencyKey },
        body: JSON.stringify(request),
      });
    },
    async status(runId) {
      requireRunId(runId);
      return call('GET', `/api/v1/runs/${runId}`, statusFor(runId));
    },
    async cancel(runId) {
      requireRunId(runId);
      return call('POST', `/api/v1/runs/${runId}/cancel`, statusFor(runId));
    },
    async manifest(runId) {
      requireRunId(runId);
      return call('GET', `/api/v1/runs/${runId}/manifest`, parseManifest);
    },
    async list(options = {}) {
      const { limit = LIST_LIMIT.default, cursor } = options;
      if (typeof limit !== 'number' || !Number.isInteger(limit) || limit < LIST_LIMIT.min || limit > LIST_LIMIT.max) {
        throw new RunsApiError('invalid_input', `Limit must be a whole number from ${LIST_LIMIT.min} to ${LIST_LIMIT.max}.`);
      }
      if (cursor !== undefined && !isUuid(cursor)) throw new RunsApiError('invalid_input', 'Cursor must be a run ID (UUID).');
      let query = `limit=${encodeURIComponent(String(limit))}`;
      if (cursor !== undefined) query += `&cursor=${encodeURIComponent(cursor)}`;
      return call('GET', `/api/v1/runs?${query}`, parsePage);
    },
  };
}
