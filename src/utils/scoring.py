from collections import Counter
from collections.abc import Iterable, Mapping

RISK_LEVELS: tuple[str, ...] = ("high", "medium", "normal")
RISK_WEIGHTS: Mapping[str, int] = {"high": 2, "medium": 1, "normal": 0}
DEFAULT_STATUS_MAPPING: Mapping[str, str] = {
    "dangerous": "high",
    "high": "high",
    "unknown": "medium",
    "medium": "medium",
    "normal": "normal",
    "secure": "normal",
    "info": "normal",
    "warning": "medium",
}

def normalize_token(value: object) -> str:
    if isinstance(value, str):
        return value.strip().lower()
    return str(value).strip().lower()

def map_to_risk(
    value: object,
    mapping: Mapping[str, str] = DEFAULT_STATUS_MAPPING,
    default: str = "normal",
) -> str:
    token = normalize_token(value)
    return mapping.get(token, default)

def tally_risks(
    values: Iterable[object],
    mapping: Mapping[str, str] = DEFAULT_STATUS_MAPPING,
    levels: Iterable[str] = RISK_LEVELS,
    default: str = "normal",
) -> dict[str, int]:
    counts = Counter({level: 0 for level in levels})
    for value in values:
        if value is None:
            continue
        level = map_to_risk(value, mapping=mapping, default=default)
        counts[level] += 1
    return dict(counts)

def weighted_score(
    counts: Mapping[str, int],
    weights: Mapping[str, int] = RISK_WEIGHTS,
) -> int:
    return sum(counts.get(level, 0) * weights.get(level, 0) for level in set(counts) | set(weights))

def summarize_risks(
    values: Iterable[object],
    mapping: Mapping[str, str] = DEFAULT_STATUS_MAPPING,
    weights: Mapping[str, int] = RISK_WEIGHTS,
) -> dict[str, int | float]:
    counts = tally_risks(values, mapping=mapping)
    score = weighted_score(counts, weights=weights)
    return {
        **counts,
        "score": score,
        "total": sum(counts.values()),
    }
