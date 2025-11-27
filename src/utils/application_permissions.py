from pathlib import Path
from typing import Iterable
import sys
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator
from apps import available_apps
from utils import scoring

SRC_PATH = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SRC_PATH.parent
GENERATED_ROOT = SRC_PATH / "generated"
PERMISSIONS_DIR = GENERATED_ROOT / "permissions"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

CSV_NAME = "application_permissions.csv"
DEFAULT_BASE_PATH = PROJECT_ROOT
COLUMN_CANDIDATES: tuple[str, ...] = (
    "STATUS",
    "status",
    "Status",
    "SEVERITY",
    "severity",
    "Severity",
)
COLOR_NORMAL = "#c7c9d3"
COLOR_MEDIUM = "#ffb347"
COLOR_HIGH = "#ff5c5c"


def prepare_output_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    return path

def find_status_column(frame: pd.DataFrame) -> str | None:
    for candidate in COLUMN_CANDIDATES:
        if candidate in frame.columns:
            return candidate
    return None

def summarize_manufacturer(csv_path: Path) -> dict[str, int | str] | None:
    dataframe = pd.read_csv(csv_path)
    column = find_status_column(dataframe)
    if column is None:
        return None
    summary = scoring.summarize_risks(dataframe[column])
    manufacturer = csv_path.parent.name
    return {
        "manufacturer": manufacturer,
        "high": int(summary.get("high", 0)),
        "medium": int(summary.get("medium", 0)),
        "normal": int(summary.get("normal", 0)),
        "total_permissions": int(summary.get("total", 0)),
        "score": int(summary.get("score", 0)),
    }

def collect_permission_summaries(
    base_path: Path = DEFAULT_BASE_PATH,
) -> list[dict[str, int | str]]:
    summaries: list[dict[str, int | str]] = []
    for app in available_apps(base_path):
        csv_path = base_path / app / CSV_NAME
        if not csv_path.exists():
            continue
        summary = summarize_manufacturer(csv_path)
        if summary is None:
            continue
        summaries.append(summary)
    return summaries

def summaries_to_frame(summaries: Iterable[dict[str, int | str]]) -> pd.DataFrame:
    frame = pd.DataFrame(list(summaries))
    if frame.empty:
        return frame
    return frame.sort_values("manufacturer").reset_index(drop=True)

def plot_stacked_bar(frame: pd.DataFrame, output_path: Path) -> Path:
    prepare_output_path(output_path)
    manufacturers = frame["manufacturer"].tolist()
    normal = frame["normal"].tolist()
    medium = frame["medium"].tolist()
    high = frame["high"].tolist()
    x_positions = list(range(len(manufacturers)))

    fig, ax = plt.subplots(figsize=(max(8, len(manufacturers) * 0.9), 5.5))
    ax.bar(x_positions, normal, label="Normal", color=COLOR_NORMAL)
    ax.bar(x_positions, medium, bottom=normal, label="Medium", color=COLOR_MEDIUM)
    ax.bar(
        x_positions,
        high,
        bottom=(frame["normal"] + frame["medium"]).tolist(),
        label="High",
        color=COLOR_HIGH,
    )
    ax.set_xticks(x_positions, manufacturers, rotation=45, ha="right")
    ax.set_ylabel("Permissions count")
    ax.set_title("Application permission risk mix by manufacturer")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path

def plot_score_bars(frame: pd.DataFrame, output_path: Path) -> Path:
    ordered = frame.sort_values("score", ascending=False)
    prepare_output_path(output_path)
    fig, ax = plt.subplots(figsize=(8, max(4, len(ordered) * 0.5)))
    bars = ax.barh(ordered["manufacturer"], ordered["score"], color="#4c72b0")
    ax.set_xlabel("Risk score (High=2, Medium=1)")
    ax.set_ylabel("Manufacturer")
    ax.set_title("Total application permission risk score")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.invert_yaxis()
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.1,
            bar.get_y() + (bar.get_height() / 2),
            f"{int(width)}",
            va="center",
            fontsize=8,
        )
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path

def plot_risk_pie(frame: pd.DataFrame, output_path: Path) -> Path:
    total_high = int(frame["high"].sum())
    total_medium = int(frame["medium"].sum())
    total_normal = int(frame["normal"].sum())
    totals = [total_high, total_medium, total_normal]
    labels = ["High", "Medium", "Normal"]
    colors = [COLOR_HIGH, COLOR_MEDIUM, COLOR_NORMAL]
    if sum(totals) == 0:
        raise ValueError("No permission data available for pie chart")

    prepare_output_path(output_path)
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.pie(
        totals,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
    )
    ax.set_title("Risk distribution across all permissions")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path

def save_summary_csv(frame: pd.DataFrame, output_path: Path) -> Path:
    prepare_output_path(output_path)
    frame.to_csv(output_path, index=False)
    return output_path

def generate_permissions_reports(
    base_path: Path = DEFAULT_BASE_PATH,
) -> dict[str, Path]:
    summaries = collect_permission_summaries(base_path)
    if not summaries:
        return {}

    frame = summaries_to_frame(summaries)
    permissions_dir = PERMISSIONS_DIR
    outputs = {
        "summary_csv": save_summary_csv(frame, permissions_dir / "permissions_summary.csv"),
        "stacked_bar": plot_stacked_bar(frame, permissions_dir / "permissions_stacked.png"),
        "score_bar": plot_score_bars(frame, permissions_dir / "permissions_scores.png"),
        "risk_pie": plot_risk_pie(frame, permissions_dir / "permissions_risk_split.png"),
    }
    return outputs

if __name__ == "__main__":
    results = generate_permissions_reports()
    if results:
        for name, path in results.items():
            print(f"Created {name}: {path}")
    else:
        print("No application permission data available")
