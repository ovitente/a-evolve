"""LLM-as-judge evaluation for Claude Code orchestrator agents.

Scores agent output on 4 axes: format, completeness, quality, contract.
For reviewer/security roles, adds ground-truth scoring for injected bugs.
"""

from __future__ import annotations

import logging
from ...llm.base import LLMMessage
from ...types import Feedback, Task, Trajectory

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_TEMPLATE = """\
You are a STRICT technical evaluator. Score 0.9+ is RARE. Follow the checklist exactly.

Score 4 axes (0.0 to 1.0) using these MANDATORY rules:

## FORMAT (weight 0.10)
{format_checklist}

## COMPLETENESS (weight 0.25)
{completeness_checklist}

## QUALITY (weight 0.45)
{quality_rubric}

## CONTRACT (weight 0.20)
- Has [STATUS: ...] declaration: +0.3
- Stays within role boundaries (does not do other agents' jobs): +0.3
- Has actionable output (not just advice): +0.4

Respond ONLY in this exact format (use decimal numbers like 0.65, not letters):
FORMAT: 0.X
COMPLETENESS: 0.X
QUALITY: 0.X
CONTRACT: 0.X
VERDICT: PASS or PARTIAL or FAIL
DETAIL: name the single biggest weakness
"""

ROLE_JUDGE_CONFIG = {
    "architect": {
        "format_checklist": (
            "Count these required sections: Summary, Components, Technology Stack, Interfaces, "
            "Capacity Planning, Monitoring, Failure Modes, Non-functional requirements, Assumptions, "
            "Risks, Status declaration.\n"
            "- All 11 present with content: 0.9-1.0\n"
            "- 8-10 present: 0.7\n"
            "- 5-7 present: 0.5\n"
            "- Fewer than 5: 0.3"
        ),
        "completeness_checklist": (
            "Check these 5 items. Each missing item = subtract 0.15 from 1.0:\n"
            "- [ ] Capacity planning with NUMBERS (memory, CPU, storage, network)\n"
            "- [ ] Failure modes with SPECIFIC scenarios (not just \"handle failures\")\n"
            "- [ ] Interface specs with DATA TYPES or schemas\n"
            "- [ ] Technology choices with SPECIFIC product names (not \"use a database\")\n"
            "- [ ] Monitoring with SPECIFIC metrics or thresholds\n"
            "Score CANNOT exceed 0.5 if capacity planning has no numbers."
        ),
        "quality_rubric": (
            "- 0.8-1.0: Specific tech choices WITH versions, capacity WITH formulas, schemas WITH field types, failure modes WITH recovery steps\n"
            "- 0.6-0.7: Specific tech choices but missing formulas/schemas/recovery details\n"
            "- 0.4-0.5: Some specifics mixed with generic advice\n"
            "- 0.2-0.3: Mostly generic (\"use Redis\", \"add monitoring\") without details\n"
            "- 0.0-0.1: Pure boilerplate\n"
            "If output contains \"consider\", \"appropriate\", \"suitable\" without specifics, cap at 0.5."
        ),
    },
    "reviewer": {
        "format_checklist": (
            "Count these required sections: Summary, Issues Found (with severity), "
            "Code Quality, Security Concerns, Recommendations, Status declaration.\n"
            "- All 6 present: 0.9-1.0\n"
            "- 4-5 present: 0.7\n"
            "- 2-3 present: 0.5\n"
            "- Fewer than 2: 0.3"
        ),
        "completeness_checklist": (
            "Check these 5 items. Each missing item = subtract 0.15 from 1.0:\n"
            "- [ ] Identified specific bugs with line numbers or code references\n"
            "- [ ] Severity ratings for each issue (critical/high/medium/low)\n"
            "- [ ] Concrete fix suggestions (not just \"fix this\")\n"
            "- [ ] Security implications mentioned where relevant\n"
            "- [ ] Edge cases and error handling gaps identified"
        ),
        "quality_rubric": (
            "- 0.8-1.0: All real bugs found, precise fixes suggested, security implications explained\n"
            "- 0.6-0.7: Most bugs found but fixes are vague or security implications missed\n"
            "- 0.4-0.5: Some bugs found but many missed, generic advice\n"
            "- 0.2-0.3: Only obvious issues found, misses critical bugs\n"
            "- 0.0-0.1: No real bugs identified or all findings are false positives"
        ),
    },
    "developer": {
        "format_checklist": (
            "Count these required sections: Implementation code, Error handling, "
            "Tests or test strategy, Status declaration.\n"
            "- All 4 present with working code: 0.9-1.0\n"
            "- 3 present: 0.7\n"
            "- 2 present: 0.5\n"
            "- Fewer than 2: 0.3"
        ),
        "completeness_checklist": (
            "Check these 5 items. Each missing item = subtract 0.15 from 1.0:\n"
            "- [ ] All interfaces from architecture are implemented\n"
            "- [ ] Error handling for failure cases\n"
            "- [ ] Thread safety where required by architecture\n"
            "- [ ] Input validation at boundaries\n"
            "- [ ] Code follows specified constraints (language, deps)"
        ),
        "quality_rubric": (
            "- 0.8-1.0: Clean, working code; handles edge cases; follows architecture exactly\n"
            "- 0.6-0.7: Working code but missing some edge cases or not fully matching architecture\n"
            "- 0.4-0.5: Partial implementation, some functions stubbed\n"
            "- 0.2-0.3: Skeleton code, major parts missing\n"
            "- 0.0-0.1: Non-functional or wrong language/approach"
        ),
    },
    "security": {
        "format_checklist": (
            "Count these required sections: Vulnerability Summary, Findings (with CVSS/severity), "
            "Exploitation Scenarios, Remediation, Status declaration.\n"
            "- All 5 present: 0.9-1.0\n"
            "- 3-4 present: 0.7\n"
            "- 2 present: 0.5\n"
            "- Fewer than 2: 0.3"
        ),
        "completeness_checklist": (
            "Check these 5 items. Each missing item = subtract 0.15 from 1.0:\n"
            "- [ ] All OWASP-relevant vulnerabilities identified\n"
            "- [ ] Exploitation scenario for each critical finding\n"
            "- [ ] Concrete remediation code or pattern for each finding\n"
            "- [ ] Severity/CVSS rating per finding\n"
            "- [ ] Defense-in-depth recommendations beyond just fixing the bug"
        ),
        "quality_rubric": (
            "- 0.8-1.0: All vulnerabilities found with exploitation paths and concrete fixes\n"
            "- 0.6-0.7: Most vulnerabilities found but exploitation or fixes incomplete\n"
            "- 0.4-0.5: Some vulnerabilities found, generic remediation advice\n"
            "- 0.2-0.3: Only obvious issues, misses critical vulnerabilities\n"
            "- 0.0-0.1: No real findings or all false positives"
        ),
    },
    "clarifier": {
        "format_checklist": (
            "Count these required sections: Ambiguities Found (with interpretations), "
            "Critical Missing Information, Status declaration.\n"
            "- All 3 present with multiple ambiguities: 0.9-1.0\n"
            "- 2 present: 0.7\n"
            "- 1 present: 0.5\n"
            "- None: 0.3"
        ),
        "completeness_checklist": (
            "Check these 5 items. Each missing item = subtract 0.15 from 1.0:\n"
            "- [ ] Multiple valid interpretations listed for each ambiguity\n"
            "- [ ] Each interpretation shows different implementation outcomes\n"
            "- [ ] Recommended question to resolve each ambiguity\n"
            "- [ ] Critical missing information identified\n"
            "- [ ] Does NOT design or solve — only identifies what is unclear"
        ),
        "quality_rubric": (
            "- 0.8-1.0: All major ambiguities found, interpretations lead to genuinely different designs\n"
            "- 0.6-0.7: Most ambiguities found but some interpretations are trivial\n"
            "- 0.4-0.5: Some ambiguities found but misses obvious ones\n"
            "- 0.2-0.3: Few ambiguities, or starts designing instead of clarifying\n"
            "- 0.0-0.1: Declares CLEAR when obvious ambiguities exist, or does architecture work"
        ),
    },
    "tester": {
        "format_checklist": (
            "Count these required sections: Summary, Test Coverage Analysis, Issues, "
            "Recommended Test Additions, Status declaration.\n"
            "- All 5 present: 0.9-1.0\n"
            "- 3-4 present: 0.7\n"
            "- 2 present: 0.5\n"
            "- Fewer than 2: 0.3"
        ),
        "completeness_checklist": (
            "Check these 5 items. Each missing item = subtract 0.15 from 1.0:\n"
            "- [ ] Unit/integration/E2E coverage assessed separately\n"
            "- [ ] Specific missing test scenarios with concrete descriptions\n"
            "- [ ] Priority ratings for each gap\n"
            "- [ ] Edge cases and error paths identified\n"
            "- [ ] Concrete test code or pseudocode for critical gaps"
        ),
        "quality_rubric": (
            "- 0.8-1.0: All coverage gaps found, concrete test cases suggested, priorities justified\n"
            "- 0.6-0.7: Most gaps found but test suggestions are vague\n"
            "- 0.4-0.5: Some gaps found, generic testing advice\n"
            "- 0.2-0.3: Obvious gaps missed, no concrete test suggestions\n"
            "- 0.0-0.1: No useful analysis"
        ),
    },
    "documenter": {
        "format_checklist": (
            "Count these required sections: Summary, README, Setup/Config docs, "
            "API docs (if applicable), User Guide, Troubleshooting, Status declaration.\n"
            "- 6+ present: 0.9-1.0\n"
            "- 4-5 present: 0.7\n"
            "- 2-3 present: 0.5\n"
            "- Fewer than 2: 0.3"
        ),
        "completeness_checklist": (
            "Check these 5 items. Each missing item = subtract 0.15 from 1.0:\n"
            "- [ ] Working code examples (not just descriptions)\n"
            "- [ ] Installation and setup steps that could be followed literally\n"
            "- [ ] All configuration options documented with defaults\n"
            "- [ ] Error scenarios and troubleshooting covered\n"
            "- [ ] Both quick-start and detailed reference provided"
        ),
        "quality_rubric": (
            "- 0.8-1.0: Could deploy and use the system following only this documentation\n"
            "- 0.6-0.7: Good coverage but some steps require guessing\n"
            "- 0.4-0.5: Partial documentation, some sections are stubs\n"
            "- 0.2-0.3: High-level overview only, not actionable\n"
            "- 0.0-0.1: Generic template with no project-specific content"
        ),
    },
    "devops": {
        "format_checklist": (
            "Count these required sections: CI/CD Pipeline, Deployment Steps, "
            "Operational Checks, Runbook, Environment Placeholders, Status declaration.\n"
            "- All 6 present: 0.9-1.0\n"
            "- 4-5 present: 0.7\n"
            "- 2-3 present: 0.5\n"
            "- Fewer than 2: 0.3"
        ),
        "completeness_checklist": (
            "Check these 5 items. Each missing item = subtract 0.15 from 1.0:\n"
            "- [ ] Idempotent deployment steps (can re-run safely)\n"
            "- [ ] Rollback procedures with specific steps\n"
            "- [ ] Monitoring metrics with thresholds\n"
            "- [ ] Incident response procedures with triage steps\n"
            "- [ ] Health checks and validation gates"
        ),
        "quality_rubric": (
            "- 0.8-1.0: Complete runbook that an on-call engineer could follow at 3am\n"
            "- 0.6-0.7: Good procedures but some steps need interpretation\n"
            "- 0.4-0.5: Partial procedures, missing rollback or monitoring\n"
            "- 0.2-0.3: High-level steps only, not executable\n"
            "- 0.0-0.1: Generic advice with no specific procedures"
        ),
    },
}


def _get_judge_system(role: str) -> str:
    """Build role-specific judge system prompt."""
    config = ROLE_JUDGE_CONFIG.get(role, ROLE_JUDGE_CONFIG["architect"])
    return JUDGE_SYSTEM_TEMPLATE.format(**config)


def _parse_judge_response(text: str) -> dict[str, float | str]:
    """Parse structured judge response into scores."""
    scores: dict[str, float | str] = {}
    for line in text.strip().splitlines():
        line = line.strip()
        for key in ("FORMAT", "COMPLETENESS", "QUALITY", "CONTRACT"):
            if line.upper().startswith(key + ":"):
                try:
                    val = float(line.split(":", 1)[1].strip())
                    scores[key.lower()] = min(1.0, max(0.0, val))
                except ValueError:
                    scores[key.lower()] = 0.5
        if line.upper().startswith("VERDICT:"):
            scores["verdict"] = line.split(":", 1)[1].strip().upper()
        if line.upper().startswith("DETAIL:"):
            scores["detail"] = line.split(":", 1)[1].strip()
    return scores


def _compute_weighted_score(scores: dict[str, float | str]) -> float:
    """Compute weighted score from judge axes."""
    weights = {"format": 0.10, "completeness": 0.25, "quality": 0.45, "contract": 0.20}
    total = 0.0
    for axis, weight in weights.items():
        total += float(scores.get(axis, 0.5)) * weight
    return total


def _score_injected_bugs(output: str, metadata: dict) -> float | None:
    """For reviewer/security: check if injected bugs were found.

    Uses multi-keyword matching: ALL words in a finding phrase must appear
    in the output (within a 500-char window) to count as a match.
    This prevents false positives from incidental keyword mentions.
    """
    expected = metadata.get("expected_findings", [])
    if not expected:
        return None

    output_lower = output.lower()
    found = 0
    for finding in expected:
        keywords = finding.lower().split()
        if len(keywords) == 1:
            # Single keyword: require it appears in a diagnostic context
            # (near words like "issue", "bug", "vulnerability", "problem", "risk", "fix")
            kw = keywords[0]
            pos = output_lower.find(kw)
            if pos >= 0:
                # Check surrounding 200 chars for diagnostic context
                window = output_lower[max(0, pos - 100):pos + len(kw) + 100]
                diagnostic_words = ["issue", "bug", "vulnerab", "problem", "risk",
                                    "fix", "flaw", "danger", "critical", "block",
                                    "missing", "incorrect", "unsafe", "attack"]
                if any(dw in window for dw in diagnostic_words):
                    found += 1
        else:
            # Multi-keyword: all must appear within a 500-char window
            positions = []
            for kw in keywords:
                pos = output_lower.find(kw)
                if pos < 0:
                    break
                positions.append(pos)
            else:
                # All keywords found — check they're within 500 chars of each other
                if max(positions) - min(positions) < 500:
                    found += 1

    return found / len(expected) if expected else 1.0


def judge_output(
    task: Task,
    trajectory: Trajectory,
    role: str,
    judge_model: str = "gpt-4o-mini",
    judge_base_url: str | None = None,
) -> Feedback:
    """Evaluate agent output using LLM-as-judge + optional ground-truth."""
    from .agent import _create_llm
    llm = _create_llm(judge_model, base_url=judge_base_url)

    user_prompt = (
        f"## Agent Role: {role.upper()}\n\n"
        f"## Task Given\n{task.input}\n\n"
        f"## Agent Output\n{trajectory.output}\n"
    )

    messages = [
        LLMMessage(role="system", content=_get_judge_system(role)),
        LLMMessage(role="user", content=user_prompt),
    ]

    response = llm.complete(messages, max_tokens=500, temperature=0.0)
    scores = _parse_judge_response(response.content)
    weighted = _compute_weighted_score(scores)

    # Blend with ground-truth for reviewer/security
    bug_score = _score_injected_bugs(trajectory.output, task.metadata)
    if bug_score is not None:
        # 60% judge + 40% ground-truth
        final_score = 0.6 * weighted + 0.4 * bug_score
        detail_suffix = f" Bug detection: {bug_score:.0%}."
    else:
        final_score = weighted
        detail_suffix = ""

    detail = scores.get("detail", "No detail provided")
    verdict = scores.get("verdict", "PARTIAL")
    success = verdict == "PASS" or final_score >= 0.7

    return Feedback(
        success=success,
        score=final_score,
        detail=f"[{verdict}] {detail}{detail_suffix}",
        raw={
            "axes": {k: v for k, v in scores.items() if k not in ("verdict", "detail")},
            "weighted_score": weighted,
            "bug_score": bug_score,
            "final_score": final_score,
            "judge_model": judge_model,
        },
    )
