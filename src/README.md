# src/

Independently authored reconstruction code for SLOP Source.

This directory holds code that reimplements SLOPCASH features from
scratch, based on the research in `research/`. Code here is written
independently — it is not copied from the original project.

## Layout

- `src/<area>/` — reconstruction code for one research area
  (for example `src/token/`, `src/projects/`).
- Each area keeps its own README describing what it reimplements and
  what it does not cover yet.

## Rules

- Every file must be independently authored. Do not paste source code
  from the original project.
- Every implementation links to the research packet that verified the
  behavior it reproduces.
- Unverified work is not presented as a finished feature.
