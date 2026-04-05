"""ClaudeCodeBenchmark -- synthetic benchmark for Claude Code orchestrator agents."""

from __future__ import annotations

from ...benchmarks.base import BenchmarkAdapter
from ...types import Feedback, Task, Trajectory
from .judge import judge_output
from .tasks import get_tasks_for_role


class ClaudeCodeBenchmark(BenchmarkAdapter):
    """Benchmark adapter for Claude Code /dev orchestrator agents.

    Uses synthetic tasks per role and LLM-as-judge evaluation.
    """

    def __init__(
        self,
        role: str,
        judge_model: str = "gpt-4o-mini",
        judge_base_url: str | None = None,
    ):
        self.role = role
        self.judge_model = judge_model
        self.judge_base_url = judge_base_url

    def get_tasks(self, split: str = "train", limit: int = 10) -> list[Task]:
        return get_tasks_for_role(self.role, split=split, limit=limit)

    def evaluate(self, task: Task, trajectory: Trajectory) -> Feedback:
        return judge_output(
            task=task,
            trajectory=trajectory,
            role=self.role,
            judge_model=self.judge_model,
            judge_base_url=self.judge_base_url,
        )
