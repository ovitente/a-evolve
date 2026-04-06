# Environments

Infrastructure for model serving and agent evolution experiments.

## GPU server

Bare-metal GPU node accessible via SSH jump host.

| Property | Value |
|----------|-------|
| Access | `ssh jumper` → `ssh gpu` |
| Public IP | 176.9.117.233:77 (gpu-1) |
| Internal IP | 10.240.129.106 (r27n02) |
| GPUs | 8x (type/VRAM TBD — run `nvidia-smi`) |
| Network | Bond0 (2x Ethernet), Bond1 (8x InfiniBand) |
| SSH keys | `~/.ssh/hr/control`, `~/.ssh/personal` |
| Ansible proxy | `ProxyJump=jumper` |

## Deployed models

Self-hosted LLM inference via vLLM on the GPU server.

### Llama 3.1 405B (FP8)

Primary model for agent evolution experiments.

| Property | Value |
|----------|-------|
| Model ID | `neuralmagic/Meta-Llama-3.1-405B-Instruct-FP8` |
| Served name | `Llama-3.1-405B` |
| Framework | vLLM v0.17.0 (`vllm/vllm-openai:v0.17.0`) |
| Tensor parallel | 8 GPUs (all GPUs) |
| GPU memory util | 90% |
| Max context | 8192 tokens |
| API | OpenAI-compatible on port 8000 |
| Deploy path | `/data/model/Meta-Llama-3.1-405B-Instruct-FP8` |

To use from a-evolve: set OpenAI provider with `base_url` pointing to `http://<gpu-ip>:8000/v1`.

### Gemma 4 (planned)

Not yet deployed. Candidate models under evaluation:
- `google/gemma-4-E4B-it` (8B, ~5 GB INT4) — fits alongside Llama if `gpu-memory-utilization` reduced to ~0.82
- `google/gemma-4-E2B-it` (5B, ~3 GB INT4) — smallest, easiest to co-locate
- `google/gemma-4-26B-A4B-it` (27B MoE, 4B active, ~14 GB INT4) — best quality/size but needs GPU headroom

## Infrastructure management

Ansible playbooks in a separate repo manage GPU provisioning and model deployment.

- **Repo**: `/home/det/x7/projects/Highrise/atlas`
- **Playbook**: `ansible/playbooks/vllm_serve.yml`
- **Role**: `ansible/roles/vllm_serve/`
- **Defaults**: `ansible/roles/vllm_serve/defaults/main.yml`
- **Inventory**: `ansible/inventory/hosts.yml`

To deploy/redeploy vLLM:
```bash
cd /home/det/x7/projects/Highrise/atlas
ansible-playbook ansible/playbooks/vllm_serve.yml -i ansible/inventory/hosts.yml
```

## Config and secrets

API keys and credentials stored outside the repo, managed per-environment.

- Model API keys: `.env` / `.env.highrise` (gitignored)
- AWS credentials for Bedrock: environment variables or `~/.aws/credentials`
- Highrise API: `HIGHRISE_BASE_URL`, `HIGHRISE_API_KEY`, `HIGHRISE_MODEL`
- SSH keys for GPU access: `~/.ssh/hr/` directory

## Runtime assumptions

External services and connectivity required for the system to function.

- GPU server must be reachable via SSH jump host
- vLLM container must be running and healthy on port 8000
- Docker with NVIDIA Container Toolkit installed on GPU server
- Model weights downloaded to `/data/model/` on GPU server
