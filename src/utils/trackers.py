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

PROJECT_ROOT = SRC_PATH.parent
GENERATED_ROOT = SRC_PATH / "generated"
TRACKERS_DIR = GENERATED_ROOT / "trackers"

TRACKERS_CSV = "trackers.csv"

def handle_score_trackers(dataframe: pd.DataFrame) -> int:
    return len(dataframe)

def load_tracker_counts(base_path: Path = PROJECT_ROOT) -> dict[str, int]:
    counts: dict[str, int] = {}
    for app in available_apps(base_path):
        csv_path = base_path / app / TRACKERS_CSV
        if not csv_path.exists():
            continue
        dataframe = pd.read_csv(csv_path)
        counts[Path(app).name] = handle_score_trackers(dataframe)
    return counts

def save_tracker_bar_chart(
    counts: Mapping[str, int],
    output_path: Path,
) -> Path:
    if not counts:
        raise ValueError("No tracker counts provided")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    manufacturers = list(counts.keys())
    values = [counts[name] for name in manufacturers]
    x_positions = list(range(len(manufacturers)))

    fig, ax = plt.subplots(figsize=(max(6, len(manufacturers) * 0.8), 4.5))
    ax.bar(x_positions, values, color="#1f77b4")
    ax.set_ylabel("Tracker count")
    ax.set_title("Trackers detected per manufacturer")
    ax.set_xticks(x_positions, manufacturers, rotation=45, ha="right")
    max_value = max(values)
    ax.set_ylim(0, max_value + 1)
    ax.set_yticks(range(0, max_value + 1, 1))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path

def generate_tracker_report(base_path: Path = PROJECT_ROOT) -> Path | None:
    counts = load_tracker_counts(base_path)
    if not counts:
        return None
    output_path = TRACKERS_DIR / "tracker_counts.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    return save_tracker_bar_chart(counts, output_path)

if __name__ == "__main__":
    path = generate_tracker_report()
    if path:
        print(f"Saved tracker chart to {path}")
    else:
        print("No tracker data available to plot")
