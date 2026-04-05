#!/usr/bin/env python3
"""Evolve a single Claude Code orchestrator agent role.

Usage:
    python examples/claude_code_examples/evolve_agent.py --role architect --cycles 5
    python examples/claude_code_examples/evolve_agent.py --role reviewer --cycles 5 --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_evolve.agents.claude_code.agent import ClaudeCodeAgent, _create_llm
from agent_evolve.agents.claude_code.benchmark import ClaudeCodeBenchmark
from agent_evolve.algorithms.adaptive_skill.engine import AdaptiveSkillEngine
from agent_evolve.config import EvolveConfig
from agent_evolve.engine.loop import EvolutionLoop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Evolve a Claude Code agent role")
    parser.add_argument(
        "--role", required=True,
        choices=["architect", "developer", "reviewer", "security",
                 "clarifier", "tester", "documenter", "devops"],
        help="Agent role to evolve",
    )
    parser.add_argument("--cycles", type=int, default=5, help="Evolution cycles")
    parser.add_argument("--batch-size", type=int, default=5, help="Tasks per batch")
    parser.add_argument("--model", default="gpt-4o", help="Solver model")
    parser.add_argument("--judge-model", default="gpt-4o-mini", help="Judge model")
    parser.add_argument("--evolver-model", default="gpt-4o", help="Evolver model")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL for solver/judge")
    parser.add_argument("--evolver-max-tokens", type=int, default=None, help="Max tokens for evolver output")
    parser.add_argument(
        "--config", default="examples/configs/claude_code.yaml",
        help="Config YAML path",
    )
    parser.add_argument(
        "--work-dir", default="./evolution_workdir",
        help="Working directory for evolved workspaces",
    )
    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    if config_path.exists():
        config = EvolveConfig.from_yaml(config_path)
    else:
        config = EvolveConfig()

    # Override from CLI
    config.max_cycles = args.cycles
    config.batch_size = args.batch_size
    config.evolver_model = args.evolver_model
    if args.evolver_max_tokens:
        config.evolver_max_tokens = args.evolver_max_tokens

    # Copy seed workspace to working directory
    seed = Path(f"seed_workspaces/claude_code/{args.role}")
    if not seed.exists():
        logger.error("Seed workspace not found: %s", seed)
        sys.exit(1)

    work = Path(args.work_dir) / args.role
    if not work.exists():
        logger.info("Copying seed workspace %s -> %s", seed, work)
        shutil.copytree(seed, work)
    else:
        logger.info("Using existing workspace: %s", work)

    # Create components
    agent = ClaudeCodeAgent(work, model=args.model, role=args.role, base_url=args.base_url)
    benchmark = ClaudeCodeBenchmark(role=args.role, judge_model=args.judge_model, judge_base_url=args.base_url)
    evolver_llm = _create_llm(args.evolver_model, base_url=args.base_url)
    engine = AdaptiveSkillEngine(config, llm=evolver_llm)

    logger.info("=" * 60)
    logger.info("Evolving role: %s", args.role)
    logger.info("Model: %s | Judge: %s | Evolver: %s", args.model, args.judge_model, args.evolver_model)
    logger.info("Cycles: %d | Batch size: %d", args.cycles, args.batch_size)
    logger.info("Workspace: %s", work)
    logger.info("=" * 60)

    # Run evolution
    result = EvolutionLoop(agent, benchmark, engine, config).run(cycles=args.cycles)

    # Report
    print("\n" + "=" * 60)
    print(f"Evolution complete: {args.role}")
    print(f"  Cycles: {result.cycles_completed}")
    print(f"  Final score: {result.final_score:.3f}")
    print(f"  Score history: {[f'{s:.3f}' for s in result.score_history]}")
    print(f"  Converged: {result.converged}")
    print(f"  Workspace: {work}")
    print("=" * 60)

    # Show what changed
    prompt_path = work / "prompts" / "system.md"
    skills_dir = work / "skills"
    skills = [d.name for d in skills_dir.iterdir() if d.is_dir()] if skills_dir.exists() else []

    print(f"\nEvolved prompt: {prompt_path}")
    print(f"Generated skills: {skills if skills else 'none'}")
    print(f"\nTo apply results:")
    print(f"  python examples/claude_code_examples/sync_back.py \\")
    print(f"    --workspace {work} --role {args.role} --target ~/.claude/agents/")


if __name__ == "__main__":
    main()
