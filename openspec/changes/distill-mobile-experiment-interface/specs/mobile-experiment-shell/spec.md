## ADDED Requirements

### Requirement: Keep experiment hierarchy focused on the available task
The existing experiment-list interface SHALL emphasize connecting to the service while disconnected and creating an experiment while connected. Synthetic demo exploration SHALL remain secondary. Page-level framing and header decoration SHALL NOT give every content section equal visual emphasis or repeat connection status already explained in its section. The client SHALL retain truthful unavailable states, accessible action names, font scaling, existing service behavior and measured-result boundaries.

#### Scenario: Disconnected experiment list
- **WHEN** no service connection is established
- **THEN** Connect to service is the primary action, demo exploration remains available as a secondary action, and the interface does not imply a live run can start

#### Scenario: Connected experiment list
- **WHEN** a service connection is established
- **THEN** New experiment is the primary action and refresh/settings/demo controls retain their clear names as secondary actions
