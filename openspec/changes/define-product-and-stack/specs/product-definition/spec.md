## Purpose

Define Portfolio Lab as infrastructure for reproducible quantitative research, bounded so that it cannot be mistaken for, or evolve into, an investment product. Public licensing remains a separate decision.

## ADDED Requirements

### Requirement: Provide responsive accessible interactions
The client SHALL give immediate press feedback while committing actions on release. Gesture transitions SHALL permit interruption and reversal from the displayed state. Essential actions SHALL have accessible non-gesture alternatives, support platform navigation/text scaling, and preserve feedback with reduced motion.

#### Scenario: User reverses an active sheet gesture
- **WHEN** a user grabs a moving sheet and changes direction
- **THEN** it follows from its displayed position without a jump or input lock

#### Scenario: Reduced motion or large text is enabled
- **WHEN** a user enables reduced motion or increases text size
- **THEN** the interface retains readable content, reachable actions and state feedback without mandatory large spatial animations

### Requirement: Show authoritative experiment transitions
The client SHALL distinguish local input feedback from server acceptance or completion. It SHALL retain submission identity across retry, label pending cancellation until acknowledged, and never invent progress or infer cancellation from a lost connection.

#### Scenario: Acceptance response is lost
- **WHEN** the server accepts a run but the client loses its response
- **THEN** retry uses the original submission identity and resolves the existing job rather than creating another

#### Scenario: Connection is lost during cancellation
- **WHEN** a cancellation request has no confirmed terminal outcome
- **THEN** the client reports pending or stale state rather than claiming cancellation completed

### Requirement: Bound the product away from regulated activity
The system SHALL NOT contain any code path to a brokerage, order-execution venue, or real-money account. Interfaces presenting portfolio allocations SHALL display a notice that outputs are historical research results, are not investment advice, and do not predict future returns. The system SHALL NOT collect user risk profiles or produce personalized recommendations.

#### Scenario: Allocation is displayed
- **WHEN** any interface renders portfolio weights or performance figures
- **THEN** the not-investment-advice notice is present on that surface

#### Scenario: Execution capability is proposed
- **WHEN** a change would introduce order placement, broker credentials, or account linkage
- **THEN** the change is rejected as outside the product boundary

### Requirement: Report findings honestly regardless of direction
Published results SHALL state the outcome obtained, including failure to reproduce the source paper. The project SHALL NOT adjust configuration for the purpose of matching a published number, and any configuration change made after observing test results SHALL be recorded as such.

#### Scenario: Reproduction does not match the paper
- **WHEN** the measured Sharpe ratio diverges materially from the paper's reported value
- **THEN** the divergence and its probable cause are published as the finding, and the result is not withheld or retuned to match

#### Scenario: Configuration changes after seeing test results
- **WHEN** a parameter is altered following inspection of test-period outcomes
- **THEN** the alteration is recorded as a post-hoc change and results before and after are both retained

### Requirement: Never present a metric without comparison
Any interface or report presenting a performance metric SHALL present the corresponding baseline metrics computed on identical data, folds, cost assumptions, and annualization convention.

#### Scenario: Results are rendered
- **WHEN** a run's Sharpe ratio is displayed
- **THEN** baseline Sharpe ratios computed under identical conditions are displayed alongside it

### Requirement: Distinguish cached data from live data
Client interfaces SHALL indicate when displayed data was served from cache and SHALL show the time at which it was fetched. Cached data SHALL NOT be presented as current.

#### Scenario: Client is offline
- **WHEN** the client cannot reach the API and renders previously fetched results
- **THEN** the interface marks the data as cached and states its fetch time

#### Scenario: Mutation attempted offline
- **WHEN** an offline client attempts to submit, cancel, or verify a run
- **THEN** the action is disabled with an explanation and is not automatically replayed on reconnection

### Requirement: Submit experiments idempotently
The service SHALL persist each operator-scoped idempotency key, canonical request hash and job identity atomically. Identical retries SHALL return the original job; reuse with different content SHALL return a conflict. Accepted jobs SHALL expose asynchronous progress and terminal outcomes.

#### Scenario: Client retries after losing the response
- **WHEN** the same request is retried with its original key
- **THEN** the client receives the same job ID without creating another job

### Requirement: Recover jobs without stale completion
Job execution SHALL have bounded attempts/deadlines and expiring ownership. Reclaimed jobs SHALL reject writes from previous owners. Completion SHALL become visible only after all referenced artifacts are verified and terminal registration succeeds atomically. Unreferenced uploads SHALL NOT count as completed results.

#### Scenario: Worker dies after uploading artifacts
- **WHEN** the worker exits before committing completion and its ownership expires
- **THEN** the job can be retried within its budget and the abandoned upload is not exposed as a completed result

#### Scenario: Stale worker resumes
- **WHEN** a previous owner tries to complete a reclaimed job
- **THEN** its completion is rejected and the current owner's result is preserved

#### Scenario: Lease expires before reclamation
- **WHEN** a worker's lease has expired even though no replacement has claimed the job
- **THEN** its committed state updates are rejected and it cannot renew that expired ownership

### Requirement: Make cancellation bounded and observable
Queued jobs SHALL cancel immediately. Running cancellation SHALL show pending status until acknowledged or forcibly terminated within the documented bound. Completion and cancellation SHALL race through a single authoritative state transition, and no cancelled attempt SHALL publish a completed result.

#### Scenario: Cancellation races completion
- **WHEN** cancellation and completion are requested concurrently
- **THEN** only one terminal outcome is committed and subsequent reads report it consistently
