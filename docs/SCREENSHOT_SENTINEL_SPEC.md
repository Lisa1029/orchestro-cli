# Screenshot Trigger & Sentinel Specification

## Purpose & Scope
- Deliver deterministic screenshot capture for terminal UI (TUI) scenarios executed via Orchestro CLI.
- Coordinate screenshot triggers with sentinel monitoring so asynchronous UI events can be validated without flaky sleeps.
- Applies to scenario runner, sentinel monitor, and plugin interfaces exposed to users writing YAML scenarios.

## Personas & Value Statements
- **Scenario Author**: wants YAML-only descriptions to capture UI states without modifying tests every time the app changes layout.
- **TUI App Developer**: needs a minimal integration surface to honor trigger files and export `.svg` screenshots cross-platform.
- **CI Maintainer**: requires machine-verifiable evidence (screenshots + sentinel matches) to trust automated pipelines.

## Success Metrics
- **Primary**: Scenario success rate remains ≥ baseline 100% (93/93 tests passing per `runlog.jsonl:1`).
- **Secondary**: Screenshot fulfillment latency ≤ 2 seconds (from trigger creation to `.svg` artifact). Measurement via new telemetry hook around trigger injection + artifact detection.
- **Observability**: Each scenario run emits runlog records with screenshot + sentinel timestamps and validation outcomes (append to `runlog.jsonl`).

## Functional Requirements
1. **Scenario Schema Support**
   - Steps may declare `screenshot: <name>` with optional `timeout` and `note`. Missing extension auto-defaults to `.svg`.
   - Validation rules must support both `path_exists` and `file_contains` for screenshot outputs.
2. **Trigger Coordination**
   - Orchestro creates trigger files under `${TMPDIR}/.vyb_orchestro/screenshot_triggers/` (Linux/macOS) or `%TEMP%\.vyb_orchestro\screenshot_triggers\` (Windows).
   - Trigger naming matches `steps[n].screenshot`; duplicates overwrite and are idempotent.
   - CLI sets `VYB_AUTO_SCREENSHOT=1` for spawned apps to opt into monitoring.
3. **App Responsibilities (external contract)**
   - The app polls the trigger directory at ≤0.5s intervals and writes `.svg` files into `artifacts/screenshots/` relative to the scenario workspace.
   - After fulfilling a trigger the app removes the `.trigger` file.
4. **Sentinel Monitoring**
   - Sentinel monitor observes `/tmp/.vyb_orchestro_sentinels` (configurable) for regex patterns defined under `steps[].expect` or sentinel-specific directives.
   - Monitor must expose `wait_for` (single pattern) and `wait_for_any` (list) with default timeouts and poll intervals ≤100ms.
   - When both sentinel and screenshot steps exist, sentinel waits precede screenshot triggers unless explicitly ordered by the scenario author.
5. **Telemetry Hooks**
   - Each screenshot step logs `trigger_created_at`, `artifact_detected_at`, and derived latency.
   - Sentinel waits log `pattern`, `timeout_s`, and result (found | timeout) with timestamps.
   - Logs must be structured JSON appended to `runlog.jsonl` for each scenario execution.

## Non-Functional Requirements
- **Reliability**: Screenshot + sentinel features operate under strict mode (asyncio `Mode.STRICT` from pytest) without warnings.
- **Portability**: Works on Linux, macOS, and Windows by honoring OS-specific temp directories without hard-coded paths elsewhere.
- **Security**: Trigger and sentinel directories remain inside OS temp; no arbitrary path traversal or writes outside repo workspace.
- **Performance**: Added telemetry should not increase total scenario runtime by more than 5% (target ≤0.2s overhead per screenshot step).

## Guardrails & Tests
- Guardrails from `AGENTS.md` apply: zero regressions (tests, security, perf, PII, toxicity, correctness).
- Required automated checks before shipping:
  1. `pytest` (existing suite) ensuring scenario + sentinel tests remain green.
  2. Targeted integration test that simulates screenshot trigger satisfaction within ≤2s.
  3. Optional `bandit -r orchestro_cli` security scan.
- Manual verification checklist:
  - Confirm screenshot artifacts appear under `artifacts/screenshots/` after running `examples/screenshot_test.yaml`.
  - Validate runlog entry captures latency + sentinel info.

## Acceptance Criteria
1. Scenario authors can define screenshot steps plus validations without referencing implementation internals.
2. Orchestro automatically sets up trigger directories and environment variables so Textual apps respond without extra configuration.
3. Sentinel monitor waits can be combined with screenshot steps to gate capturing until UI reaches a known state.
4. Telemetry for each screenshot + sentinel action appears in `runlog.jsonl` with timestamps and pass/fail states.
5. Documentation (README + QUICKSTART) references this workflow and links to this specification.

## Risks & Open Questions
- Screenshot latency >2s on slower CI runners → consider adaptive timeout telemetry before enforcing gates.
- Sentinel file path collisions when multiple scenarios run concurrently → may require per-run namespace.
- Need to determine whether legacy `runner_legacy.py` must implement the same telemetry (pending stakeholder decision).
- Coverage gaps: modules like `orchestro_cli/execution/*` currently 0% coverage; future tasks must add tests before refactors.

## Next Steps
1. Implement telemetry hook & measurement instrumentation (NANO task T4) referencing this spec.
2. Update README/Quickstart to link to spec and explain telemetry fields.
3. Explore automated sentinel-screenshot integration tests in `tests/test_screenshot_workflow.py` to increase coverage.
