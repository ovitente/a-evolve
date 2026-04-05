"""AdaptiveSkillEngine -- the core A-Evolve algorithm.

Uses an LLM with bash tool access to analyze observation logs and mutate
the agent workspace (prompts, skills, memory). This is the first and
default EvolutionEngine implementation.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from ...config import EvolveConfig
from ...contract.workspace import AgentWorkspace
from ...engine.base import EvolutionEngine
from ...engine.versioning import VersionControl
from ...llm.base import LLMMessage, LLMProvider
from ...types import Observation, StepResult
from .prompts import DEFAULT_EVOLVER_SYSTEM_PROMPT, STRUCTURED_EVOLVER_SYSTEM_PROMPT, build_evolution_prompt
from .tools import BASH_TOOL_SPEC, create_default_llm, make_workspace_bash

logger = logging.getLogger(__name__)


class AdaptiveSkillEngine(EvolutionEngine):
    """LLM-driven workspace mutation engine."""

    def __init__(self, config: EvolveConfig, llm: LLMProvider | None = None):
        self.config = config
        self._llm = llm

    @property
    def llm(self) -> LLMProvider:
        if self._llm is None:
            self._llm = create_default_llm(self.config)
        return self._llm

    def step(
        self,
        workspace: AgentWorkspace,
        observations: list[Observation],
        history: Any,
        trial: Any,
    ) -> StepResult:
        """Analyze observations and mutate the workspace via LLM."""
        recent_logs = history.get_observations(last_n_cycles=2)
        cycle_num = history.latest_cycle + 1

        skills_before = [s.name for s in workspace.list_skills()]
        drafts = workspace.list_drafts()

        prompt = build_evolution_prompt(
            workspace,
            recent_logs,
            drafts,
            cycle_num,
            evolve_prompts=self.config.evolve_prompts,
            evolve_skills=self.config.evolve_skills,
            evolve_memory=self.config.evolve_memory,
            evolve_tools=self.config.evolve_tools,
            trajectory_only=self.config.trajectory_only,
            max_skills=self.config.extra.get("max_skills", 5),
            solver_proposed=self.config.extra.get("solver_proposed", False),
            prompt_only=self.config.extra.get("prompt_only", False),
            protect_skills=self.config.extra.get("protect_skills", False),
        )
        response = self._run_llm(prompt, workspace.root)

        skills_after = [s.name for s in workspace.list_skills()]
        new_skills = len(set(skills_after) - set(skills_before))

        workspace.clear_drafts()

        mutated = set(skills_after) != set(skills_before) or new_skills > 0

        return StepResult(
            mutated=mutated,
            summary=f"A-Evolve: {new_skills} new skills, {len(drafts)} drafts reviewed",
            metadata={
                "evo_number": cycle_num,
                "tasks_analyzed": len(recent_logs),
                "drafts_reviewed": len(drafts),
                "skills_before": len(skills_before),
                "skills_after": len(skills_after),
                "new_skills": new_skills,
                "usage": response.get("usage", {}),
            },
        )

    def evolve(
        self,
        workspace: AgentWorkspace,
        observation_logs: list[dict[str, Any]],
        evo_number: int = 0,
    ) -> dict[str, Any]:
        """Run one evolution pass outside the loop (for scripts/examples)."""
        vc = VersionControl(workspace.root)
        vc.init()

        skills_before = [s.name for s in workspace.list_skills()]
        drafts = workspace.list_drafts()

        vc.commit(
            message=f"pre-evo-{evo_number}: snapshot before evolution",
            tag=f"pre-evo-{evo_number}",
        )

        prompt = build_evolution_prompt(
            workspace,
            observation_logs,
            drafts,
            evo_number,
            evolve_prompts=self.config.evolve_prompts,
            evolve_skills=self.config.evolve_skills,
            evolve_memory=self.config.evolve_memory,
            evolve_tools=self.config.evolve_tools,
            trajectory_only=self.config.trajectory_only,
            max_skills=self.config.extra.get("max_skills", 5),
            solver_proposed=self.config.extra.get("solver_proposed", False),
            prompt_only=self.config.extra.get("prompt_only", False),
            protect_skills=self.config.extra.get("protect_skills", False),
        )
        response = self._run_llm(prompt, workspace.root)

        skills_after = [s.name for s in workspace.list_skills()]
        new_skills = len(set(skills_after) - set(skills_before))

        workspace.clear_drafts()

        mutated = set(skills_after) != set(skills_before) or new_skills > 0
        if mutated:
            vc.commit(
                message=f"evo-{evo_number}: {new_skills} new skills",
                tag=f"evo-{evo_number}",
            )
        else:
            vc.commit(
                message=f"evo-{evo_number}: no mutation",
                tag=f"evo-{evo_number}",
            )

        return {
            "evo_number": evo_number,
            "tasks_analyzed": len(observation_logs),
            "drafts_reviewed": len(drafts),
            "skills_before": len(skills_before),
            "skills_after": len(skills_after),
            "new_skills": new_skills,
            "usage": response.get("usage", {}),
        }

    def _run_llm(self, prompt: str, workspace_root: Path) -> dict[str, Any]:
        """Run the evolver LLM with bash access to the workspace."""
        self._workspace_root = workspace_root
        bash_fn = make_workspace_bash(workspace_root)

        try:
            from ...llm.bedrock import BedrockProvider

            if isinstance(self.llm, BedrockProvider):
                response = self.llm.converse_loop(
                    system_prompt=DEFAULT_EVOLVER_SYSTEM_PROMPT,
                    user_message=prompt,
                    tools=[BASH_TOOL_SPEC],
                    tool_executor={"workspace_bash": lambda command: bash_fn(command)},
                    max_tokens=self.config.evolver_max_tokens,
                )
                return {
                    "content": response.content,
                    "usage": response.usage,
                }
        except ImportError:
            pass

        # For Anthropic and OpenAI: tool-use loop with workspace_bash
        return self._tool_use_loop(prompt, bash_fn)

    def _tool_use_loop(
        self, prompt: str, bash_fn, max_turns: int = 20
    ) -> dict[str, Any]:
        """Run a multi-turn tool-use loop for non-Bedrock providers."""
        from ...llm.anthropic import AnthropicProvider

        total_usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
        final_text = ""

        if isinstance(self.llm, AnthropicProvider):
            return self._anthropic_tool_loop(prompt, bash_fn, max_turns, total_usage)

        # Non-tool-use models: structured output with <file> blocks
        return self._structured_output_loop(prompt)

    def _anthropic_tool_loop(
        self, prompt: str, bash_fn, max_turns: int, total_usage: dict
    ) -> dict[str, Any]:
        """Anthropic-native tool-use loop."""
        import anthropic

        client = self.llm.client
        model = self.llm.model

        anthropic_tool = {
            "name": "workspace_bash",
            "description": BASH_TOOL_SPEC["description"],
            "input_schema": BASH_TOOL_SPEC["input_schema"],
        }

        messages = [{"role": "user", "content": prompt}]
        final_text_parts = []

        for turn in range(max_turns):
            response = client.messages.create(
                model=model,
                system=DEFAULT_EVOLVER_SYSTEM_PROMPT,
                messages=messages,
                tools=[anthropic_tool],
                max_tokens=self.config.evolver_max_tokens,
            )

            total_usage["input_tokens"] += response.usage.input_tokens
            total_usage["output_tokens"] += response.usage.output_tokens

            # Collect text blocks
            for block in response.content:
                if hasattr(block, "text"):
                    final_text_parts.append(block.text)

            # Check if model wants to use a tool
            if response.stop_reason != "tool_use":
                break

            # Execute tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    command = block.input.get("command", "")
                    logger.info("Evolver bash: %s", command[:200])
                    result = bash_fn(command)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result[:4000],
                    })

            # Append assistant response and tool results for next turn
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        return {
            "content": "\n".join(final_text_parts),
            "usage": total_usage,
        }

    def _structured_output_loop(self, prompt: str) -> dict[str, Any]:
        """For models without tool use: get structured output and apply file changes."""
        workspace_root = getattr(self, '_workspace_root', None)

        # Build context: show current files to the model
        context_parts = []
        if workspace_root:
            for rel in ("prompts/system.md",):
                p = workspace_root / rel
                if p.exists():
                    context_parts.append(f"### Current {rel}\n```\n{p.read_text()[:3000]}\n```")
            skills_dir = workspace_root / "skills"
            if skills_dir.exists():
                for f in sorted(skills_dir.iterdir()):
                    if f.is_file() and f.suffix == ".md" and not f.name.startswith("_"):
                        context_parts.append(f"### Current skills/{f.name}\n```\n{f.read_text()[:2000]}\n```")
                    elif f.is_dir() and not f.name.startswith("_"):
                        sf = f / "SKILL.md"
                        if sf.exists():
                            context_parts.append(f"### Current skills/{f.name}/SKILL.md\n```\n{sf.read_text()[:2000]}\n```")
            mem_dir = workspace_root / "memory"
            if mem_dir.exists():
                for f in sorted(mem_dir.iterdir()):
                    if f.is_file() and f.suffix == ".jsonl":
                        content = f.read_text()[-1000:]  # last entries
                        context_parts.append(f"### Current memory/{f.name} (tail)\n```\n{content}\n```")

        current_files = "\n\n".join(context_parts) if context_parts else "No existing files."

        full_prompt = f"""{prompt}

### Current Workspace Files
{current_files}

Remember: output changed files using <file path="...">content</file> blocks."""

        messages = [
            LLMMessage(role="system", content=STRUCTURED_EVOLVER_SYSTEM_PROMPT),
            LLMMessage(role="user", content=full_prompt),
        ]
        response = self.llm.complete(
            messages, max_tokens=self.config.evolver_max_tokens
        )

        # Parse and apply file blocks
        files_written = self._apply_file_blocks(response.content, workspace_root)
        if files_written:
            logger.info("Structured evolver wrote %d files: %s", len(files_written), files_written)
        else:
            logger.warning("Structured evolver returned no file blocks. Response length: %d chars. First 500: %s",
                          len(response.content), response.content[:500])

        return {"content": response.content, "usage": response.usage}

    @staticmethod
    def _apply_file_blocks(text: str, workspace_root: Path | None) -> list[str]:
        """Parse <file path="...">content</file> blocks and write them."""
        if not workspace_root:
            return []
        pattern = re.compile(
            r'<file\s+path="([^"]+)">\s*\n(.*?)\n\s*</file>',
            re.DOTALL,
        )
        written = []
        for match in pattern.finditer(text):
            rel_path = match.group(1).strip()
            content = match.group(2)
            # Security: prevent path traversal
            if ".." in rel_path or rel_path.startswith("/"):
                logger.warning("Skipping suspicious path: %s", rel_path)
                continue
            target = workspace_root / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            written.append(rel_path)
            logger.info("Structured evolver wrote: %s (%d chars)", rel_path, len(content))
        return written
