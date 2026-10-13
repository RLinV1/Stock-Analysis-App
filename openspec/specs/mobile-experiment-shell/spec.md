# Mobile Experiment Shell Specification

## Purpose

Provide an honest, accessible Android/web research preview that helps users understand the planned experiment flow without presenting synthetic content as a live or historical result.

## Requirements

### Requirement: Identify demo research data
The mobile shell SHALL identify synthetic demonstration results on every surface where they appear and SHALL show a research-only, not-investment-advice notice wherever allocations or performance metrics appear.

#### Scenario: Inspect demonstration results
- **WHEN** a user opens the demo experiment and its results
- **THEN** the UI labels the preview synthetic and states that research results are not investment advice or future-return predictions

### Requirement: Never fabricate a service outcome
Without a configured reachable service, the client SHALL prevent experiment submission and cancellation and SHALL not invent a job ID, accepted state, or successful cancellation.

#### Scenario: Service unavailable
- **WHEN** the user opens New experiment while the client has no service configuration
- **THEN** Start experiment is unavailable with an explanation and no job is created

### Requirement: Provide accessible first navigation
The Android/web client SHALL expose named navigation actions for Experiments, New experiment, Experiment detail, and Results using native touch controls with immediate press feedback and essential targets at least 48 logical pixels tall.

#### Scenario: Open the demonstration report
- **WHEN** a user activates the demo experiment and then Results
- **THEN** the UI shows the report and offers a named Back action on each deeper screen

### Requirement: Cover the first client states with executable tests
Automated tests SHALL cover the visible demo labels, offline-disabled mutation, basic navigation, result comparison/notice, and invalid draft input. The implementation record SHALL distinguish these from pending live API and physical Android verification.

#### Scenario: Run client tests
- **WHEN** the documented test command is run on the supported Node environment
- **THEN** the suite checks behavior and reports a passing or failing exit status

### Requirement: Validate drafts against the request contract
The New experiment draft SHALL accept only values allowed by the synthetic request v1 contract: lookback 10–50 and epochs 1–3, whole numbers only, and SHALL name those bounds in its inline error.

#### Scenario: Enter a lookback the API would reject
- **WHEN** the user enters lookback 51 and leaves the field
- **THEN** the UI shows that lookback must be a whole number from 10 to 50
