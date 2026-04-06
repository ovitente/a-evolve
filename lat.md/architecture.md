# Architecture

Agentic evolution framework — "The PyTorch for Agentic AI". Full design details in `DESIGN.md`.

## System shape

Six core subsystems compose the framework.

- **Evolution Engine** (`agent_evolve/engine/`) — orchestrates SOLVE → EVALUATE → OBSERVE → EVOLVE → RELOAD cycle
- **Algorithms** (`agent_evolve/algorithms/`) — adaptive_evolve, adaptive_skill, guided_synth, skillforge
- **LLM Providers** (`agent_evolve/llm/`) — abstract `LLMProvider` with Anthropic, OpenAI, Bedrock implementations
- **Agents** (`agent_evolve/agents/`) — concrete agent implementations (SWE, MCP, etc.)
- **Benchmarks** (`agent_evolve/benchmarks/`) — adapters for SWE-bench, MCP-Atlas, Terminal-Bench, SkillBench
- **Seed Workspaces** (`seed_workspaces/`) — pre-configured agent workspaces with filesystem contract

## Key flows

Config-driven evolution cycle from workspace load to agent improvement.

1. Config YAML selects algorithm, model, and benchmark
2. Engine loads seed workspace, creates evolution working directory
3. Each generation: agent solves tasks → benchmark evaluates → engine observes results → algorithm evolves agent
4. Workspace IS the interface — filesystem contract (`skills/`, `memory/`, `config.yaml`) mediates all communication

## Important constraints

Hard rules protecting system integrity and reproducibility.

- Workspace filesystem contract is the only interface between engine and agent — no direct API calls
- LLM provider selection is automatic based on model name prefix (claude→Anthropic, gpt→OpenAI, dotted→Bedrock)
- Self-hosted models (vLLM) connect via OpenAI-compatible provider with custom `base_url`
- Evolution artifacts are gitignored — only seed workspaces are tracked

## Ownership boundaries

Which lat.md files are authoritative for which concerns.

- Architecture decisions: this file
- Build/deploy/experiments: [[delivery]]
- Infrastructure and models: [[environments]]
- Test strategy: [[tests]]
