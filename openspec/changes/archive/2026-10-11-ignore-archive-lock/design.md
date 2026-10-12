## Decision

Ignore only the known OpenSpec archive lock path and remove its tracked copy. Keep actual archive contents under version control. Do not remove an active claim; inspect the recorded PID and timestamp first. The OpenSpec CLI may recreate the ignored lock while archiving this change.
