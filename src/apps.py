from pathlib import Path

MANUFACTURER_DIRS = (
    "Acura",
    "Audi",
    "BMW",
    "Chevrolet",
    "Jeep",
    "Kia",
    "Mercedes",
    "Tesla",
    "Honda",
    "Subaru",
)

def available_apps(base_path: Path = Path(__file__).resolve().parents[1]) -> list[str]:
    return [name for name in MANUFACTURER_DIRS if (base_path / name).exists()]
