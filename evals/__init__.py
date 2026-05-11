"""
AgentOS Evaluations
===================

Eval framework built on Agno evals for testing all agents, teams, and workflows.

Three layers:
    - Smoke tests: fast pattern-matching assertions, no LLM cost
    - Reliability: tool call validation, no LLM cost
    - Agno evals: LLM-judged using AgentAsJudgeEval and AccuracyEval

Usage:
    python -m evals smoke                    # Fast smoke tests
    python -m evals reliability              # Tool call validation
    python -m evals                          # Agno eval suite
    python -m evals --category security      # Single category
    python -m evals perf                     # Performance baselines
    python -m evals improve --entity dash    # Auto-improvement data
"""

from agno.models.openai import OpenAIResponses

JUDGE_MODEL = OpenAIResponses(id="gpt-5.4")

CATEGORIES = {
    "security": {
        "type": "judge_binary",
        "module": "evals.cases.security",
    },
    "accuracy": {
        "type": "accuracy",
        "module": "evals.cases.accuracy",
    },
    "quality": {
        "type": "judge_numeric",
        "module": "evals.cases.judge.quality",
    },
}
