# Agent workflow

This repository uses `lat.md/` as the project knowledge graph.

## Quick context

a-evolve is an agentic evolution framework. It runs AI agents on benchmarks and evolves their strategies.
The project depends on self-hosted LLM infrastructure — see `lat.md/environments.md` for deployed models and GPU setup.

## Mandatory workflow

Before making substantial changes:
- Read the relevant `lat.md/` files first.
- Use `lat locate`, `lat section`, `lat refs`, or `lat search` when helpful.
- Do not change architecture, delivery flow, environments, or test expectations without first reading the matching lat docs.

## What's deployed

Read `lat.md/environments.md` for current state. Key facts:
- GPU server with 8 GPUs accessible via `ssh jumper` → `ssh gpu`
- Llama 3.1 405B FP8 served via vLLM on all 8 GPUs (port 8000)
- Infrastructure managed by Ansible playbooks in `/home/det/x7/projects/Highrise/atlas`

## Routing rules

- Architecture / components / algorithms / LLM providers:
  → update `lat.md/architecture.md`

- Build / deploy models / run experiments / CI:
  → update `lat.md/delivery.md`

- GPU infrastructure / deployed models / SSH access / secrets:
  → update `lat.md/environments.md`

- Test strategy / required checks / invariants:
  → update `lat.md/tests.md`

## Completion criteria

A task is not complete until:
- Relevant `lat.md/` files updated for any substantial behavior/config/workflow change
- `lat check` passes
- Pre-commit hook passes (infra changes require lat.md update)

## Related repositories

- **Highrise Atlas** (`/home/det/x7/projects/Highrise/atlas`) — Ansible infrastructure: GPU provisioning, vLLM deployment, network management, security hardening
