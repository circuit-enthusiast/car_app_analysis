from collections.abc import Mapping
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

import matplotlib.pyplot as plt
import pandas as pd

from apps import available_apps
from utils import scoring

PROJECT_ROOT = SRC_PATH.parent
GENERATED_ROOT = SRC_PATH / "generated"
NETWORK_DIR = GENERATED_ROOT / "network"

NETWORK_CSV = "network_security.csv"


def handle_score_network_security(dataframe: pd.DataFrame) -> dict[str, int]:
    if "SEVERITY" not in dataframe.columns and "severity" not in dataframe.columns:
        return {"unknown": len(dataframe)}

    # accept either uppercase or lowercase column
    if "SEVERITY" in dataframe.columns:
        sev_col = dataframe["SEVERITY"]
    else:
        sev_col = dataframe["severity"]

    # normalize severity values
    sev_series = sev_col.fillna("unknown").astype(str).str.strip().str.lower()
    counts = sev_series.value_counts().to_dict()

    # Map severity to the scoring module's risk levels
    mapped_counts: dict[str, int] = {}
    for sev, count in counts.items():
        risk_level = scoring.map_to_risk(sev)
        mapped_counts[risk_level] = mapped_counts.get(risk_level, 0) + count

    # ensure keys are str
    return {str(k): int(v) for k, v in mapped_counts.items()}


def load_network_counts(base_path: Path = PROJECT_ROOT) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for app in available_apps(base_path):
        csv_path = base_path / app / NETWORK_CSV
        if not csv_path.exists():
            continue
        dataframe = pd.read_csv(csv_path)
        counts[Path(app).name] = handle_score_network_security(dataframe)
    return counts


def save_network_bar_chart(
    counts: Mapping[str, Mapping[str, int]],
    output_path: Path,
) -> Path:
    if not counts:
        raise ValueError("No network counts provided")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    manufacturers = list(counts.keys())
    # determine the full set of severities across all manufacturers
    severity_set = set()
    for m in manufacturers:
        severity_set.update(counts[m].keys())
    severities = sorted(severity_set)

    # build stacked values per severity
    values_by_sev = {sev: [counts[m].get(sev, 0) for m in manufacturers] for sev in severities}

    x_positions = list(range(len(manufacturers)))

    fig, ax = plt.subplots(figsize=(max(6, len(manufacturers) * 0.9), 5))

    # choose a color palette (extendable)
    palette = ["#d62728", "#ff7f0e", "#2b77ae", "#abf301", "#9467bd", "#8c564b"]
    # map severities to colors deterministically
    colors = {sev: palette[i % len(palette)] for i, sev in enumerate(severities)}

    bottom = [0] * len(manufacturers)
    for sev in severities:
        vals = values_by_sev[sev]
        ax.bar(x_positions, vals, bottom=bottom, color=colors.get(sev), label=sev)
        bottom = [b + v for b, v in zip(bottom, vals)]

    ax.set_ylabel("Findings count")
    ax.set_title("Network security findings per manufacturer (by severity)")
    ax.set_xticks(x_positions, manufacturers, rotation=45, ha="right")
    max_value = max(bottom) if bottom else 0
    ax.set_ylim(0, max_value + 1)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(title="Severity", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def save_network_summary_csv(counts: Mapping[str, Mapping[str, int]], output_path: Path) -> Path:
    if not counts:
        raise ValueError("No network counts provided")

    rows = []
    for m, sevmap in counts.items():
        high = int(sevmap.get("high", 0))
        medium = int(sevmap.get("medium", 0))
        normal = int(sevmap.get("normal", 0))
        total = high + medium + normal
        score = int(scoring.weighted_score({"high": high, "medium": medium, "normal": normal}))
        rows.append(
            {
                "manufacturer": m,
                "high": high,
                "medium": medium,
                "normal": normal,
                "total": total,
                "score": score,
            }
        )

    df = pd.DataFrame(rows)
    # ensure consistent column order
    df = df[["manufacturer", "high", "medium", "normal", "total", "score"]]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def generate_network_report(base_path: Path = PROJECT_ROOT) -> Path | None:
    counts = load_network_counts(base_path)
    if not counts:
        return None
    output_path = NETWORK_DIR / "network_security_counts.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    # save chart
    chart_path = save_network_bar_chart(counts, output_path)

    # save summary CSV alongside the chart
    csv_path = NETWORK_DIR / "network_security_summary.csv"
    if csv_path.exists():
        csv_path.unlink()
    save_network_summary_csv(counts, csv_path)

    return chart_path


if __name__ == "__main__":
    path = generate_network_report()
    if path:
        print(f"Saved network chart to {path}")
        print(f"Saved summary CSV to {NETWORK_DIR / 'network_security_summary.csv'}")
        # also print a brief severity table for CLI users
        counts = load_network_counts()
        for m, sevmap in counts.items():
            print(f"{m}:")
            for sev, c in sorted(sevmap.items(), key=lambda x: (-x[1], x[0])):
                print(f"  {sev}: {c}")
    else:
        print("No network security data available to plot")
