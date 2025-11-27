from pathlib import Path

MANUFACTURER_DIRS = (
    "Acura",
    "Audi",
    "BMW",
    "Buick",
    "Chevrolet",
    "Ford",
    "Honda",
    "Jeep",
    "Kia",
    "Mercedes",
    "Nissan",
    "Subaru",
    "Tesla",
    "Toyota",
)

def available_apps(base_path: Path = Path(__file__).resolve().parents[1]) -> list[str]:
    return [name for name in MANUFACTURER_DIRS if (base_path / name).exists()]
