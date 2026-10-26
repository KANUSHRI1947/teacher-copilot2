"""Tokenomics for Teacher Copilot: turn token counts into dollars.

Prices: OpenAI Standard short-context rates for gpt-6-luna, USD per 1M tokens
(course Lecture 11, source https://developers.openai.com/api/docs/pricing).
input_tokens includes cache reads and cache writes, so the uncached part is
input - cache_read - cache_write, billed at the normal input rate.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

MODEL_PRICES = {
    "gpt-6-luna": {"input": 0.10, "cached": 0.01, "cache_write": 0.125, "output": 0.50},
}
PRICE_SOURCE = "https://developers.openai.com/api/docs/pricing"

# Spending guardrails
DEFAULT_RUN_BUDGET_USD = 0.01   # one question may not cost more than 1 cent
DAILY_BUDGET_USD = 1.00         # whole app stops for the day after $1


def usage_to_dict(usage) -> dict:
    """Read the token fields from a pydantic-ai RunUsage (or a dict)."""
    get = (lambda k: usage.get(k, 0)) if isinstance(usage, dict) else (lambda k: getattr(usage, k, 0) or 0)
    return {
        "input_tokens": int(get("input_tokens") or 0),
        "cache_read_tokens": int(get("cache_read_tokens") or 0),
        "cache_write_tokens": int(get("cache_write_tokens") or 0),
        "output_tokens": int(get("output_tokens") or 0),
        "requests": int(get("requests") or 0),
        "tool_calls": int(get("tool_calls") or 0),
    }


def subtract(a: dict, b: dict) -> dict:
    return {k: a.get(k, 0) - b.get(k, 0) for k in a}


def cost_usd(usage: dict, model: str = "gpt-6-luna") -> float:
    p = MODEL_PRICES[model]
    cr, cw = usage.get("cache_read_tokens", 0), usage.get("cache_write_tokens", 0)
    uncached = max(0, usage.get("input_tokens", 0) - cr - cw)
    dollars = (
        uncached * p["input"]
        + cr * p["cached"]
        + cw * p["cache_write"]
        + usage.get("output_tokens", 0) * p["output"]
    ) / 1_000_000
    return round(dollars, 8)


def budget_to_token_cap(budget_usd: float, model: str = "gpt-6-luna") -> int:
    """Convert a dollar budget into a hard token cap for pydantic-ai UsageLimits.

    Conservative: assumes every token is billed at the (most expensive) output
    rate, so the real spend can never pass the budget.
    """
    return max(1000, int(budget_usd / (MODEL_PRICES[model]["output"] / 1_000_000)))


def spent_today(log_path: Path) -> float:
    """Sum today's spend from the audit log (survives app restarts)."""
    if not log_path.exists():
        return 0.0
    today = date.today().isoformat()
    total = 0.0
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("timestamp", "").startswith(today):
                total += float(rec.get("cost_usd", 0) or 0)
    return total


def monthly_projection(cost_per_run: float, runs_per_day: int = 8, school_days: int = 21) -> float:
    return cost_per_run * runs_per_day * school_days
