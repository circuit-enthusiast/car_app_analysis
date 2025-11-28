from pathlib import Path
from utils import application_permissions, trackers, certificate_analysis, network_analysis, pni_scoring, code_analysis, manifest_analysis

BASE_PATH = Path(__file__).resolve().parents[1]
SUBSCRIPTS = (
    ("trackers", trackers.generate_tracker_report),
    ("application_permissions", application_permissions.generate_permissions_reports),
    ("certificate_analysis", certificate_analysis.generate_certificate_report),
    ("network_analysis", network_analysis.generate_network_report),
    ("pni_scoring", pni_scoring.generate_pni_report),
    ("code_analysis", code_analysis.generate_code_report),
    ("manifest_analysis", manifest_analysis.generate_manifest_report)
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
