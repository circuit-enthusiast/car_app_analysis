
from pathlib import Path
import sys
from typing import Optional

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
	sys.path.append(str(SRC_PATH))

import pandas as pd

from apps import available_apps

PROJECT_ROOT = SRC_PATH.parent
GENERATED_ROOT = SRC_PATH / "generated"
MERGED_DIR = GENERATED_ROOT / "merged"


def load_all_csvs(target_filename: str | None, base_path: Path = PROJECT_ROOT) -> pd.DataFrame:
	frames = []
	for app in available_apps(base_path):
		app_path = base_path / app
		if target_filename:
			candidates = [app_path / target_filename]
		else:
			candidates = list(app_path.glob("*.csv"))

		for csv_path in candidates:
			if not csv_path or not Path(csv_path).exists():
				continue
			try:
				df = pd.read_csv(csv_path)
			except Exception:
				# skip unreadable files
				continue
			df = df.copy()
			df["app"] = Path(app).name
			df["source_path"] = str(csv_path)
			frames.append(df)

	if not frames:
		return pd.DataFrame()

	# Concatenate using union of columns
	result = pd.concat(frames, ignore_index=True, sort=False)
	return result


def find_all_csv_filenames(base_path: Path = PROJECT_ROOT) -> set[str]:
	names = set()
	for app in available_apps(base_path):
		app_path = base_path / app
		for p in app_path.glob("*.csv"):
			if p.is_file():
				names.add(p.name)
	return names


def load_all_grouped_by_filename(base_path: Path = PROJECT_ROOT) -> dict[str, pd.DataFrame]:
	result: dict[str, pd.DataFrame] = {}
	names = find_all_csv_filenames(base_path)
	for name in sorted(names):
		df = load_all_csvs(name, base_path)
		if not df.empty:
			result[name] = df
	return result


def save_merged(df: pd.DataFrame, output_path: Path) -> Path:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	if output_path.exists():
		output_path.unlink()
	df.to_csv(output_path, index=False)
	return output_path


def generate_summary_for(target_filename: str | None, base_path: Path = PROJECT_ROOT, output_name: str | None = None, outdir: Path | None = None) -> Optional[Path]:
	df = load_all_csvs(target_filename, base_path)
	if df.empty:
		return None
	if output_name:
		out_name = output_name
	else:
		if target_filename:
			out_name = f"summary_{Path(target_filename).name}"
		else:
			out_name = "summary_all.csv"
	if outdir:
		output_path = outdir / out_name
	else:
		output_path = MERGED_DIR / out_name
	return save_merged(df, output_path)


def generate_summaries_for_all(base_path: Path = PROJECT_ROOT, outdir: Path | None = None) -> list[Path]:
	grouped = load_all_grouped_by_filename(base_path)
	saved: list[Path] = []
	for name, df in grouped.items():
		if outdir:
			out_path = outdir / f"summary_{name}"
		else:
			out_path = MERGED_DIR / f"summary_{name}"
		save_merged(df, out_path)
		saved.append(out_path)
	return saved


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Merge CSVs named the same across app folders into one summary CSV")
	parser.add_argument("filename", nargs="?", help="Target CSV filename to look for in each app folder (e.g. certificate_analysis.csv). Omit or pass 'all' to merge all CSVs.")
	parser.add_argument("--all", action="store_true", help="Merge all CSV files found across apps")
	parser.add_argument("--output", help="Output filename (optional). Example: summary_combined.csv")
	parser.add_argument("--outdir", help="Output directory for generated summaries (optional)")
	parser.add_argument("--base", help="Project base path (optional)", default=str(PROJECT_ROOT))
	args = parser.parse_args()

	base = Path(args.base)
	outdir = Path(args.outdir) if args.outdir else None

	if args.all or (args.filename and args.filename.lower() == "all") or not args.filename and args.all:
		saved = generate_summaries_for_all(base, outdir)
		if saved:
			print("Saved merged CSVs:")
			for p in saved:
				print(f"  {p}")
		else:
			print("No CSV files found to merge")
	else:
		if args.filename:
			target = args.filename
		else:
			target = None
		result = generate_summary_for(target, base, args.output, outdir)
		if result:
			print(f"Saved merged CSV to {result}")
		else:
			print("No matching CSV files found to merge")

