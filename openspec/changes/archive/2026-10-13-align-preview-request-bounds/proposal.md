## Why

The mobile draft form accepts lookback 10–100 and epochs 1–5, but the published synthetic request v1 contract and the API accept only lookback 10–50 and epochs 1–3. Drafts that look valid on the phone would be rejected once submission is connected.

## What Changes

- Validate the preview's lookback and epoch drafts against the request v1 bounds and say so in the error text.
- Update the component tests for the new bounds and add boundary cases.

## Capabilities

### Modified Capabilities

- `mobile-experiment-shell`: draft validation matches the request contract.

## Impact

Mobile preview only. No submission is added; Start experiment stays disabled while no service is configured.
