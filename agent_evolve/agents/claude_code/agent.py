"""ClaudeCodeAgent -- wraps Claude Code orchestrator agent prompts for evolution.

Each agent role (architect, developer, reviewer, etc.) is a prompt-only agent:
it receives a task input, builds a system prompt from workspace files (including
evolved skills), calls the LLM, and returns structured text output.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ...llm.base import LLMMessage, LLMProvider
from ...protocol.base_agent import BaseAgent
from ...types import Task, Trajectory

logger = logging.getLogger(__name__)

# Token budgets per role (from the original agent definitions)
ROLE_MAX_TOKENS: dict[str, int] = {
    "clarifier": 800,
    "architect": 2000,
    "developer": 4000,
    "reviewer": 1500,
    "security": 1500,
    "tester": 1500,
    "documenter": 3000,
    "devops": 2000,
}


def _create_llm(model: str, base_url: str | None = None) -> LLMProvider:
    """Create the appropriate LLM provider based on model name."""
    if model.startswith("claude"):
        from ...llm.anthropic import AnthropicProvider
        return AnthropicProvider(model=model)
    else:
        from ...llm.openai import OpenAIProvider
        return OpenAIProvider(model=model, base_url=base_url)


class ClaudeCodeAgent(BaseAgent):
    """Evolvable wrapper for Claude Code /dev orchestrator agents.

    Auto-detects provider from model name (claude-* → Anthropic, gpt-* → OpenAI).
    The workspace prompt and skills are assembled into a single system prompt,
    mirroring how the real orchestrator injects skills at spawn time.
    """

    def __init__(
        self,
        workspace_dir: str | Path,
        model: str = "gpt-4o",
        max_tokens: int | None = None,
        role: str | None = None,
        base_url: str | None = None,
    ):
        self._model = model
        self._role = role
        self._max_tokens_override = max_tokens
        self._base_url = base_url
        self._llm: LLMProvider | None = None
        super().__init__(workspace_dir)

    @property
    def llm(self) -> LLMProvider:
        if self._llm is None:
            self._llm = _create_llm(self._model, base_url=self._base_url)
        return self._llm

    @property
    def role(self) -> str:
        if self._role:
            return self._role
        # Infer from workspace directory name
        return self.workspace.root.name

    @property
    def max_output_tokens(self) -> int:
        if self._max_tokens_override:
            return self._max_tokens_override
        return ROLE_MAX_TOKENS.get(self.role, 2000)

    def _build_full_prompt(self) -> str:
        """Assemble system prompt from workspace prompt + evolved skills."""
        parts = [self.system_prompt]

        if self.skills:
            parts.append("\n## Loaded Skills\n")
            for skill in self.skills:
                content = self.get_skill_content(skill.name)
                parts.append(f"### {skill.name}\n{skill.description}\n\n{content}\n")

        if self.memories:
            lessons = []
            for m in self.memories[-10:]:
                if isinstance(m.get("content"), str):
                    lessons.append(m["content"])
            if lessons:
                parts.append("\n## Lessons from past tasks\n")
                for lesson in lessons[-5:]:
                    parts.append(f"- {lesson}")

        return "\n".join(parts)

    def solve(self, task: Task) -> Trajectory:
        """Call the LLM with the workspace prompt and task input."""
        system = self._build_full_prompt()

        messages = [
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content=task.input),
        ]

        logger.info(
            "Solving task %s with role=%s, model=%s, prompt=%d chars",
            task.id, self.role, self._model, len(system),
        )

        response = self.llm.complete(messages, max_tokens=self.max_output_tokens)

        return Trajectory(
            task_id=task.id,
            output=response.content,
            steps=[{
                "type": "llm_call",
                "model": self._model,
                "role": self.role,
                "prompt_chars": len(system),
                "input_tokens": response.usage.get("input_tokens", 0),
                "output_tokens": response.usage.get("output_tokens", 0),
            }],
            conversation=[
                {"role": "system", "content": system},
                {"role": "user", "content": task.input},
                {"role": "assistant", "content": response.content},
            ],
        )
