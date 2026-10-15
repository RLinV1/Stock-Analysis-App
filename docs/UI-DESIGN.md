# Portfolio Lab UI direction and acceptance plan

Updated 2026-10-14. The user selected the supplied [apple-design skill](reference/apple-design.md). Android and web are the current implementation targets; the iOS port is deferred. The client has an offline preview and connected run/report flow, plus equity/allocations source and component coverage. The earlier preview had dark desktop/390×844 web review; the connected Results screens still require rendered/device and live-service checks. See the [active implementation record](../openspec/changes/connect-preview-to-service/implementation.md) for current automated evidence. This document remains the planned full client contract.

## Platform adaptation

Keep React Native/Expo/TypeScript with Android and web targets now and an iOS port later. The available physical phone is Android. Apply the skill's immediate feedback, hierarchy, restrained materials, interruptible motion and accessibility principles. Preserve Android Back, TalkBack and platform font scaling. Do not substitute a website for the phone app or force iOS navigation conventions onto Android.

DOM, Pointer Events, CSS and Motion examples apply to web, not native components. Native gesture/animation packages must match the selected Expo SDK and pass device tests before locking versions. Prefer established native scrolling/navigation over custom physics. Spring numbers are tuning starting points, not universal constants.

The supplied skill's introductory response-only instruction does not replace the user's specific ongoing UI request. Its complete source is preserved; this document defines project-specific adaptations.

## First usable flow

| Screen | Main content/action | Required states |
|---|---|---|
| Experiments | Start a run; inspect dataset, model, date and status | Loading, empty, current list, cached list with fetched time, failed fetch/retry |
| New experiment | Select available data and bounded settings; Start experiment | Inline validation, submitting, accepted job ID, rejected request, offline-disabled action |
| Experiment detail | Explain actual stage/progress; cancel when allowed; open results | Queued, running, cancellation requested, cancelled, failed, completed, stale cache |
| Results | Allocations, equity, metrics beside baselines; open provenance/deviations | Finite/undefined metrics with reasons, missing artifacts, comparison errors |

Use specific labels such as Experiments and Results. Put advanced settings one level deeper. Keep synthetic/paper-inspired labels and the research-only notice visible. Do not expose a Transformer or dataset option before it works.

## Visual and interaction rules

- Use platform system fonts and consistent spacing/type scales. Show metric units and positive/negative signs. Support system light/dark appearance; distinguish chart series with labels and line styles as well as color.
- Reserve translucency for useful floating layers. Never stack translucent text surfaces. Use opaque surfaces when requested or when blur harms legibility/performance.
- Target at least 48 logical pixels for essential touch controls, without overlapping hit areas. Check small screens, 200% text scaling, safe areas, keyboard and rotation for clipping or hidden actions.
- Highlight on press-down; commit on release. Allow dragging away to cancel. Never submit an experiment on press-down.
- Drag from the original grab offset. Start interrupted transitions from the displayed position, preserve appropriate velocity and permit reversal without jumping or locking input. Keep entry/exit paths consistent; reserve bounce for momentum gestures.
- Provide visible accessible alternatives for gesture actions. Preserve Android Back and restore focus after modal dismissal.
- Reduced motion uses static changes or brief fades while retaining state feedback. Support reduced transparency/high contrast through platform capabilities and an in-app fallback when a preference is unavailable.
- Optional haptics confirm meaningful events, respect user/platform settings and never serve as the only feedback. Avoid gratuitous sounds and looping motion.

## Truthful experiment state

Immediate feedback is not optimistic success. Show Submitting until the server accepts a job. Reuse the same submission identity if the response is lost. Do not invent a completion percentage when no measurable denominator exists.

Cancellation requested stays pending until the authoritative terminal state arrives. Losing connectivity does not imply the worker stopped. Cached results show their fetched time. Offline submit/cancel/verify actions are disabled and never queued for later replay.

Baseline comparisons use identical recorded dates and costs. Preserve undefined metric reasons. Make dataset/model/configuration identity and deviations understandable, with detailed provenance available when wanted.

## Verification before client completion

| Check | Acceptance evidence | Current status |
|---|---|---|
| Components and state | All listed states; invalid fields; no duplicate actions; cancellation race; failed fetch; undefined metrics | Preview/live fake-client/report tests exist; series/date/retry/race coverage added. Real service races remain unverified. |
| API contract | Real response fixtures; unsupported versions rejected; one idempotency key retained across retry | Typed request/report/series readers and fake-client tests exist; saved A0 artifact regression added. No real HTTP integration. |
| Physical Android flow | Submit, monitor, cancel, reconnect and inspect report on the phone | Deferred until local service/client work |
| Web flow | Same core actions plus keyboard navigation and browser accessibility checks | Not run |
| Accessibility | TalkBack order/names/announcements; restored focus; gesture alternatives; large text; contrast; no color-only meaning | Not run |
| Motion | Reverse a sheet mid-motion without jumps; cancel a press; native scroll behavior; reduced-motion equivalents | Not run |
| Visual review | Inspect rendered light/dark, loading/empty/error/offline, small/tall, keyboard and large-text screenshots | Earlier offline preview dark web review only; current connected UI review not run. |
| Performance | Release-build trace on the phone with refresh rate, frame times and dropped frames during gestures/scrolling | Not run |
| Recovery | API unavailable; lost acceptance response; app restart; stale cache; worker restart; cancellation/completion race | Not run |

Run automated checks before manual device review. Inspect rendered screens, not only snapshots. Include long labels, long lists and missing data. Record device/OS, Expo/runtime versions and evidence for each result. No UI check is satisfied by Python tests.

The [A0 evidence](A0-EVIDENCE.md) records 59 research tests and exact local repeat/resume agreement. [SPEC](SPEC.md) separately requires bounded requests, durable jobs, lease fencing, artifact registration and service recovery. [DESIGN](../DESIGN.md) stages the small usable app before larger research studies.
