// Synthetic request v1 bounds (contracts/synthetic-run-request.v1.schema.json).
export const CONTRACT_VERSION = 1;
export const DATASET_KIND = 'synthetic';
export const OBSERVATIONS = { min: 140, max: 420 };
export const DATASET_SEED = { min: 0, max: 4294967295 };
export const LOOKBACK = { min: 10, max: 50 };
export const HIDDEN_SIZE = { min: 8, max: 64 };
export const EPOCHS = { min: 1, max: 3 };
export const EXECUTION_SEED = { min: 0, max: 4294967295 };
export const COST_BPS = { min: 0, max: 100 };

export type SyntheticRequestV1 = {
  contract_version: 1;
  dataset: { kind: 'synthetic'; observations: number; seed: number };
  model: { lookback: number; hidden_size: number; epochs: number };
  execution: { seed: number; cost_bps: number };
};

// Runs API v1 shapes (contracts/runs-api.v1.openapi.yaml).
export const RUN_STATES = ['QUEUED', 'RUNNING', 'CANCEL_REQUESTED', 'CANCELLED', 'COMPLETE', 'FAILED'] as const;
export type RunState = typeof RUN_STATES[number];
export type AcceptedRun = { runId: string };
export type RunStatus = { runId: string; state: RunState; attemptCount: number; manifestAvailable: boolean; errorCode: string | null };

// Artifact index v1 (contracts/artifact-index.v1.schema.json).
export type ArtifactFile = { path: string; key: string; sha256: string; bytes: number };
export type ArtifactIndex = { run_id: string; attempt_id: string; kind: 'synthetic-a0'; files: ArtifactFile[] };

type Range = { min: number; max: number };

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function checkKeys(value: Record<string, unknown>, allowed: string[], where: string, problems: string[]) {
  for (const key of Object.keys(value)) if (!allowed.includes(key)) problems.push(`${where} has unexpected field "${key}".`);
}

function checkInteger(value: unknown, range: Range, name: string, problems: string[]) {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < range.min || value > range.max) {
    problems.push(`${name} must be a whole number from ${range.min} to ${range.max}.`);
  }
}

/** Returns human-readable problems with a synthetic request v1; empty when valid. */
export function validateRequest(request: unknown): string[] {
  const problems: string[] = [];
  if (!isObject(request)) return ['Request must be an object.'];
  checkKeys(request, ['contract_version', 'dataset', 'model', 'execution'], 'Request', problems);
  if (request.contract_version !== CONTRACT_VERSION) problems.push(`contract_version must be ${CONTRACT_VERSION}.`);

  const { dataset, model, execution } = request;
  if (!isObject(dataset)) problems.push('dataset must be an object.');
  else {
    checkKeys(dataset, ['kind', 'observations', 'seed'], 'dataset', problems);
    if (dataset.kind !== DATASET_KIND) problems.push(`dataset.kind must be "${DATASET_KIND}".`);
    checkInteger(dataset.observations, OBSERVATIONS, 'dataset.observations', problems);
    checkInteger(dataset.seed, DATASET_SEED, 'dataset.seed', problems);
  }
  if (!isObject(model)) problems.push('model must be an object.');
  else {
    checkKeys(model, ['lookback', 'hidden_size', 'epochs'], 'model', problems);
    checkInteger(model.lookback, LOOKBACK, 'model.lookback', problems);
    checkInteger(model.hidden_size, HIDDEN_SIZE, 'model.hidden_size', problems);
    checkInteger(model.epochs, EPOCHS, 'model.epochs', problems);
  }
  if (!isObject(execution)) problems.push('execution must be an object.');
  else {
    checkKeys(execution, ['seed', 'cost_bps'], 'execution', problems);
    checkInteger(execution.seed, EXECUTION_SEED, 'execution.seed', problems);
    checkInteger(execution.cost_bps, COST_BPS, 'execution.cost_bps', problems);
  }
  return problems;
}
