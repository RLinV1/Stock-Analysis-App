## ADDED Requirements

### Requirement: Validate drafts against the request contract
The New experiment draft SHALL accept only values allowed by the synthetic request v1 contract: lookback 10–50 and epochs 1–3, whole numbers only, and SHALL name those bounds in its inline error.

#### Scenario: Enter a lookback the API would reject
- **WHEN** the user enters lookback 51 and leaves the field
- **THEN** the UI shows that lookback must be a whole number from 10 to 50
