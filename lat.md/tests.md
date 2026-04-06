# Tests

Test strategy and critical invariants.

## Required checks

Three automated checks gate every commit and merge.

- `make test` — pytest suite (`tests/`)
- `make lint` — ruff check (`agent_evolve/`)
- `lat check` — knowledge graph validation (pre-commit)

## Smoke expectations

Health checks to verify deployment and code changes are working.

After model deployment:
- `curl http://<gpu-ip>:8000/v1/models` returns model list
- `curl http://<gpu-ip>:8000/health` returns OK

After code changes:
- `pytest tests/ -v` passes
- Example configs in `examples/configs/` remain valid YAML

## Critical invariants

Properties that must always hold true across the codebase.

- Workspace filesystem contract must be respected — engine never calls agent methods directly
- LLM provider auto-detection logic must match documented prefixes
- Seed workspaces must be self-contained (no references to absolute paths)

## Failure signals

Conditions that block a commit, PR, or deploy.

- Pre-commit blocks if infrastructure files changed without `lat.md/` update
- `lat check` failure blocks commit
- pytest failure blocks merge
