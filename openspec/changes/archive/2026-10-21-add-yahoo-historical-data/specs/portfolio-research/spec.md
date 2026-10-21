## ADDED Requirements

### Requirement: Acquire Yahoo history as hashed local snapshots
Historical acquisition SHALL download each ticker's daily history with explicit adjustment, action, repair and date options, retain the exact downloaded bytes with SHA-256 hashes, record the client version, query and retrieval time, and write only to a new local directory that is never committed.

#### Scenario: Fetch a tier
- **WHEN** a caller fetches tier1 or tier2 with explicit start and end dates
- **THEN** the output SHALL contain each ticker's raw CSV, an acquisition record with hashes and query, and a dataset manifest accepted by the existing loader

#### Scenario: Output already exists
- **WHEN** the output directory already exists
- **THEN** acquisition SHALL fail before downloading or replacing anything

### Requirement: Build total-return prices before aligning dates
Each ticker's price series SHALL be a total-return index compounded from split-adjusted close plus same-day distributions, computed on that ticker's own calendar before keeping only dates every ticker traded. Missing, nonpositive or nonfinite values SHALL be rejected, never filled, and the number of dropped dates SHALL be recorded as a deviation.

#### Scenario: Distribution on a date another ticker lacks
- **WHEN** a ticker pays a distribution on a date missing for another ticker
- **THEN** the distribution SHALL still be included in that ticker's next retained return

### Requirement: Label tier and source limits
Every Yahoo dataset SHALL declare that it is a reconstruction rather than the authors' data, that raw ^VIX is not investable (tier1) or that VIXY replaces VIX with history from 2011 (tier2), and that close prices carry hindsight split adjustment.

#### Scenario: Tier 1 manifest
- **WHEN** tier1 data is written
- **THEN** its deviations SHALL state that the raw VIX index is not investable
