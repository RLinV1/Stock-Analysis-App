import { createRunsClient, RunsApiError } from '../src/api/client';
import type { FetchInit, FetchLike, FetchResponse } from '../src/api/client';
import { validateRequest } from '../src/api/contract';
import type { SyntheticRequestV1 } from '../src/api/contract';

const TOKEN = 'operator-secret-token-0123456789';
const RUN_ID = '3f2b8c1e-4d5a-4b6c-8d7e-9f0a1b2c3d4e';
const ATTEMPT_ID = '7a6b5c4d-3e2f-4a1b-9c8d-7e6f5a4b3c2d';
const HASH = 'a'.repeat(64);

// Inlined copy of contracts/examples/synthetic-smoke.v1.json.
const SMOKE: SyntheticRequestV1 = {
  contract_version: 1,
  dataset: { kind: 'synthetic', observations: 140, seed: 2026 },
  model: { lookback: 10, hidden_size: 8, epochs: 1 },
  execution: { seed: 7, cost_bps: 1 },
};

type Call = { url: string; init: FetchInit };

function fakeFetch(status: number, body: string) {
  const calls: Call[] = [];
  const fetchImpl: FetchLike = async (url, init) => {
    calls.push({ url, init });
    const response: FetchResponse = { ok: status >= 200 && status < 300, status, text: async () => body };
    return response;
  };
  return { calls, fetchImpl };
}

function client(fetchImpl: FetchLike, baseUrl = 'http://127.0.0.1:8080', timeoutMs?: number) {
  return createRunsClient({ baseUrl, token: TOKEN, fetchImpl, timeoutMs });
}

async function caught(promise: Promise<unknown>): Promise<RunsApiError> {
  try {
    await promise;
  } catch (error) {
    expect(error).toBeInstanceOf(RunsApiError);
    expect((error as Error).message).not.toContain(TOKEN);
    return error as RunsApiError;
  }
  throw new Error('Expected a RunsApiError');
}

const problem = (status: number, code: string) => JSON.stringify({ type: 'about:blank', title: 'Problem', status, code });

describe('validateRequest', () => {
  test('accepts the synthetic smoke example', () => {
    expect(validateRequest(SMOKE)).toEqual([]);
  });

  test('reports out-of-range, non-integer and unexpected fields', () => {
    const problems = validateRequest({ ...SMOKE, model: { lookback: 9, hidden_size: 8.5, epochs: 1 }, extra: true });
    expect(problems).toEqual(expect.arrayContaining([
      expect.stringMatching(/model\.lookback/),
      expect.stringMatching(/model\.hidden_size/),
      expect.stringMatching(/unexpected field "extra"/),
    ]));
  });
});

describe('runs client', () => {
  test('submit sends method, path, headers and body and returns the run ID', async () => {
    const fake = fakeFetch(202, JSON.stringify({ runId: RUN_ID }));
    await expect(client(fake.fetchImpl).submit(SMOKE, 'smoke-key:1')).resolves.toEqual({ runId: RUN_ID });

    expect(fake.calls).toHaveLength(1);
    const [{ url, init }] = fake.calls;
    expect(url).toBe('http://127.0.0.1:8080/api/v1/runs');
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({
      Accept: 'application/json',
      Authorization: `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
      'Idempotency-Key': 'smoke-key:1',
    });
    expect(JSON.parse(init.body ?? '')).toEqual(SMOKE);
  });

  test('rejects an invalid request or idempotency key without calling fetch', async () => {
    const fake = fakeFetch(202, JSON.stringify({ runId: RUN_ID }));
    const bad = { ...SMOKE, model: { ...SMOKE.model, epochs: 4 } };
    expect((await caught(client(fake.fetchImpl).submit(bad, 'key'))).kind).toBe('invalid_input');
    expect((await caught(client(fake.fetchImpl).submit(SMOKE, 'has space'))).kind).toBe('invalid_input');
    expect((await caught(client(fake.fetchImpl).submit(SMOKE, ''))).kind).toBe('invalid_input');
    expect((await caught(client(fake.fetchImpl).submit(SMOKE, 'k'.repeat(129)))).kind).toBe('invalid_input');
    expect((await caught(client(fake.fetchImpl).status('not-a-uuid'))).kind).toBe('invalid_input');
    expect(fake.calls).toHaveLength(0);
  });

  test('rejects a base URL without an http scheme', () => {
    expect(() => createRunsClient({ baseUrl: '127.0.0.1:8080', token: TOKEN })).toThrow(RunsApiError);
  });

  test('status parses the body and normalizes a missing errorCode to null', async () => {
    const fake = fakeFetch(200, JSON.stringify({ runId: RUN_ID, state: 'RUNNING', attemptCount: 1, manifestAvailable: false }));
    await expect(client(fake.fetchImpl).status(RUN_ID)).resolves.toEqual({
      runId: RUN_ID, state: 'RUNNING', attemptCount: 1, manifestAvailable: false, errorCode: null,
    });
    expect(fake.calls[0].url).toBe(`http://127.0.0.1:8080/api/v1/runs/${RUN_ID}`);
    expect(fake.calls[0].init.method).toBe('GET');
    expect(fake.calls[0].init.body).toBeUndefined();
  });

  test('cancel posts to the cancel path and returns the resulting state', async () => {
    const fake = fakeFetch(200, JSON.stringify({ runId: RUN_ID, state: 'CANCELLED', attemptCount: 0, manifestAvailable: false, errorCode: null }));
    await expect(client(fake.fetchImpl).cancel(RUN_ID)).resolves.toMatchObject({ state: 'CANCELLED', errorCode: null });
    expect(fake.calls[0].url).toBe(`http://127.0.0.1:8080/api/v1/runs/${RUN_ID}/cancel`);
    expect(fake.calls[0].init.method).toBe('POST');
  });

  test('maps problem codes and an empty 404', async () => {
    const unauthorized = await caught(client(fakeFetch(401, problem(401, 'unauthorized')).fetchImpl).status(RUN_ID));
    expect(unauthorized).toMatchObject({ kind: 'http', status: 401, code: 'unauthorized' });

    const conflict = await caught(client(fakeFetch(409, problem(409, 'idempotency_conflict')).fetchImpl).submit(SMOKE, 'key'));
    expect(conflict).toMatchObject({ kind: 'http', status: 409, code: 'idempotency_conflict' });

    const missing = await caught(client(fakeFetch(404, '').fetchImpl).status(RUN_ID));
    expect(missing).toMatchObject({ kind: 'http', status: 404, code: 'not_found' });
  });

  test('rejects malformed JSON and unexpected body shapes', async () => {
    const cases: [number, string][] = [
      [200, '{not json'],
      [200, ''],
      [200, JSON.stringify({ runId: RUN_ID, state: 'DONE', attemptCount: 1, manifestAvailable: true })],
      [200, JSON.stringify({ runId: RUN_ID, state: 'QUEUED', attemptCount: 1.5, manifestAvailable: false })],
      [200, JSON.stringify({ runId: 'abc', state: 'QUEUED', attemptCount: 0, manifestAvailable: false })],
      [200, JSON.stringify({ runId: RUN_ID, state: 'FAILED', attemptCount: 3, manifestAvailable: false, errorCode: 5 })],
      [200, JSON.stringify({ runId: ATTEMPT_ID, state: 'QUEUED', attemptCount: 0, manifestAvailable: false })],
    ];
    for (const [status, body] of cases) {
      expect((await caught(client(fakeFetch(status, body).fetchImpl).status(RUN_ID))).kind).toBe('invalid_response');
    }
    expect((await caught(client(fakeFetch(202, '{}').fetchImpl).submit(SMOKE, 'key'))).kind).toBe('invalid_response');
  });

  test('maps a fetch rejection to a network error', async () => {
    const fetchImpl: FetchLike = async () => { throw new TypeError(`Network request failed for ${TOKEN}`); };
    expect(await caught(client(fetchImpl).status(RUN_ID))).toMatchObject({ kind: 'network' });
  });

  test('aborts after timeoutMs and reports a timeout', async () => {
    let aborted = false;
    const fetchImpl: FetchLike = (_url, init) => new Promise((_resolve, reject) => {
      init.signal.addEventListener('abort', () => { aborted = true; reject(new Error('aborted')); });
    });
    expect(await caught(client(fetchImpl, 'http://127.0.0.1:8080', 5).status(RUN_ID))).toMatchObject({ kind: 'timeout' });
    expect(aborted).toBe(true);
  });

  test('manifest returns the parsed artifact index', async () => {
    const index = {
      run_id: RUN_ID,
      attempt_id: ATTEMPT_ID,
      kind: 'synthetic-a0',
      files: [{ path: 'report.json', key: `runs/${RUN_ID}/attempts/${ATTEMPT_ID}/report.json`, sha256: HASH, bytes: 512 }],
    };
    const fake = fakeFetch(200, JSON.stringify(index));
    await expect(client(fake.fetchImpl).manifest(RUN_ID)).resolves.toEqual(index);
    expect(fake.calls[0].url).toBe(`http://127.0.0.1:8080/api/v1/runs/${RUN_ID}/manifest`);

    const noReport = { ...index, files: [{ ...index.files[0], path: 'other.json' }] };
    expect((await caught(client(fakeFetch(200, JSON.stringify(noReport)).fetchImpl).manifest(RUN_ID))).kind).toBe('invalid_response');
  });

  test('strips trailing slashes from the base URL', async () => {
    const fake = fakeFetch(200, JSON.stringify({ runId: RUN_ID, state: 'COMPLETE', attemptCount: 1, manifestAvailable: true, errorCode: null }));
    await client(fake.fetchImpl, 'http://127.0.0.1:8080//').status(RUN_ID);
    expect(fake.calls[0].url).toBe(`http://127.0.0.1:8080/api/v1/runs/${RUN_ID}`);
  });
});
