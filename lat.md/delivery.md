# Delivery

How code and models move from development to running experiments.

## Build and release

Python package with optional extras, built and developed locally.

- **Package**: `pip install -e ".[all,dev]"` or `make install`
- **Dev shell**: `nix develop` (provides Python 3.11, uv, git, docker)
- **Versioning**: 0.1.0 (pyproject.toml), no formal release process yet
- **Lint**: `make lint` (ruff check)
- **Format**: `make fmt` (ruff format)

## Model deployment

Model serving managed via Ansible in the atlas repository.

1. Update defaults in `ansible/roles/vllm_serve/defaults/main.yml`
2. Run `ansible-playbook ansible/playbooks/vllm_serve.yml -i ansible/inventory/hosts.yml`
3. Verify: `curl http://<gpu-ip>:8000/v1/models`

Adding a new model requires either a new role or parameterizing `vllm_serve` for multi-model support.

## Running experiments

Config YAML drives all experiment parameters — model, algorithm, benchmark.

```bash
# Example: MCP-Atlas benchmark
python -m agent_evolve.run --config examples/configs/metaharness_mcp.yaml

# Example: SWE-bench
python -m agent_evolve.run --config examples/configs/swe.yaml
```

## Failure handling

Recovery procedures for common failure modes. See [[tests#Failure signals]].

- vLLM crash: container auto-restarts (`--restart unless-stopped`)
- Model OOM: reduce `--gpu-memory-utilization` or `--max-model-len`
- Experiment failure: check logs in `logs/`, workspace in `evolution_workdir/`
