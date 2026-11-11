# tests/

Tests for the reconstruction code in `src/`.

## Layout

- `tests/<area>/` — tests for one research area's reconstruction
  (for example `tests/token/`).
- Tests must be reproducible: they run against the code in `src/`,
  not against the original project's live systems.

## Rules

- A test must state what behavior it checks and where that behavior
  was verified (the research packet in `research/`).
- A test that needs a live system, an API key, or confidential data
  does not belong here.
- The PR checks workflow runs the tests when a test runner is
  configured. Until then, tests are documentation of what should be
  checked.
