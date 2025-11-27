from collections.abc import Mapping
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from apps import available_apps
from utils import scoring

PROJECT_ROOT = SRC_PATH.parent
GENERATED_ROOT = SRC_PATH / "generated"
CERTIFICATES_DIR = GENERATED_ROOT / "certificates"

CERTIFICATE_CSV = "certificate_analysis.csv"


def handle_score_certificate_analysis(dataframe: pd.DataFrame) -> dict[str, int]:
    if "SEVERITY" not in dataframe.columns and "severity" not in dataframe.columns:
        return {"unknown": len(dataframe)}

    if "SEVERITY" in dataframe.columns:
        sev_col = dataframe["SEVERITY"]
    else:
        sev_col = dataframe["severity"]

    sev_series = sev_col.fillna("unknown").astype(str).str.strip().str.lower()
    counts = sev_series.value_counts().to_dict()

    mapped_counts: dict[str, int] = {}
    for sev, count in counts.items():
        risk_level = scoring.map_to_risk(sev)
        mapped_counts[risk_level] = mapped_counts.get(risk_level, 0) + count

    return {str(k): int(v) for k, v in mapped_counts.items()}


def load_certificate_counts(base_path: Path = PROJECT_ROOT) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for app in available_apps(base_path):
        csv_path = base_path / app / CERTIFICATE_CSV
        if not csv_path.exists():
            continue
        dataframe = pd.read_csv(csv_path)
        counts[Path(app).name] = handle_score_certificate_analysis(dataframe)
    return counts


def save_certificate_bar_chart(
    counts: Mapping[str, Mapping[str, int]],
    output_path: Path,
) -> Path:
    if not counts:
        raise ValueError("No certificate counts provided")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    manufacturers = list(counts.keys())
    severity_set = set()
    for m in manufacturers:
        severity_set.update(counts[m].keys())
    severities = sorted(severity_set)

    values_by_sev = {sev: [counts[m].get(sev, 0) for m in manufacturers] for sev in severities}

    x_positions = list(range(len(manufacturers)))

    fig, ax = plt.subplots(figsize=(max(6, len(manufacturers) * 0.9), 5))

    color_map = {
        "high": "#d62728",
        "medium": "#ff7f0e",
        "normal": "#2b77ae",
    }
    fallback_palette = ["#abf301", "#9467bd", "#8c564b"]

    bottom = [0] * len(manufacturers)
    for idx, sev in enumerate(severities):
        vals = values_by_sev[sev]
        color = color_map.get(sev, fallback_palette[idx % len(fallback_palette)])
        ax.bar(x_positions, vals, bottom=bottom, color=color, label=sev)
        bottom = [b + v for b, v in zip(bottom, vals)]

    ax.set_ylabel("Findings count")
    ax.set_title("Certificate security findings per manufacturer (by severity)")
    ax.set_xticks(x_positions, manufacturers, rotation=45, ha="right")
    max_value = max(bottom) if bottom else 0
    ax.set_ylim(0, max_value + 1)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(title="Severity", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def save_certificate_summary_csv(counts: Mapping[str, Mapping[str, int]], output_path: Path) -> Path:
    if not counts:
        raise ValueError("No certificate counts provided")

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
    df = df[["manufacturer", "high", "medium", "normal", "total", "score"]]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def generate_certificate_report(base_path: Path = PROJECT_ROOT) -> Path | None:
    counts = load_certificate_counts(base_path)
    if not counts:
        return None
    output_path = CERTIFICATES_DIR / "certificate_security_counts.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    chart_path = save_certificate_bar_chart(counts, output_path)

    csv_path = CERTIFICATES_DIR / "certificate_security_summary.csv"
    if csv_path.exists():
        csv_path.unlink()
    save_certificate_summary_csv(counts, csv_path)

    return chart_path


if __name__ == "__main__":
    path = generate_certificate_report()
    if path:
        print(f"Saved certificate chart to {path}")
        print(f"Saved summary CSV to {CERTIFICATES_DIR / 'certificate_security_summary.csv'}")
        counts = load_certificate_counts()
        for m, sevmap in counts.items():
            print(f"{m}:")
            for sev, c in sorted(sevmap.items(), key=lambda x: (-x[1], x[0])):
                print(f"  {sev}: {c}")
    else:
        print("No certificate security data available to plot")
