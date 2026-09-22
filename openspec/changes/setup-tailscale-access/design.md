## Context
The app is still in planning. Windows Package Manager is available. The standard Tailscale executable and service were not found before setup.

## Goals / Non-Goals
Install and verify PC Tailscale and prepare private phone access. No application backend exists to expose yet.

## Decisions
Use the exact Tailscale.Tailscale winget package from the winget source, inspecting publisher/source first. Use the vendor's normal interactive account authentication; do not ask for passwords or auth keys in chat. Preserve existing tailnet policies. Configure Serve only after an actual loopback-bound app endpoint exists and is verified.

## Risks / Trade-offs
Windows may require administrator consent. User authentication and phone enrollment require direct user interaction. A running service does not prove enrollment or phone connectivity.
