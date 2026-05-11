"""Accuracy eval cases — LLM-judged output comparison."""

from evals.cases.accuracy.agents import CASES as AGENT_CASES
from evals.cases.accuracy.teams import CASES as TEAM_CASES

CASES = AGENT_CASES + TEAM_CASES
