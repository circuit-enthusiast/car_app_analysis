from pathlib import Path
from utils import application_permissions, trackers

BASE_PATH = Path(__file__).resolve().parents[1]
SUBSCRIPTS = (
    ("trackers", trackers.generate_tracker_report),
    ("application_permissions", application_permissions.generate_permissions_reports),
)

def run_subscripts(base_path: Path = BASE_PATH) -> None:
    for name, runner in SUBSCRIPTS:
        print(f"Running {name} analysis...")
        runner(base_path=base_path)

def main() -> int:
    run_subscripts()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
