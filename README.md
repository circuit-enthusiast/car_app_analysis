# car_app_analysis

## Overview
This repository aggregates static analysis data for a corpus of North American automotive companion applications drawn from the Mozilla Foundation's *Privacy Not Included* study. Each application directory stores CSV exports from Mobile Security Framework (MobSF) runs, while the `scripts/` directory will host Python utilities to normalize the data, score risk, and generate comparative charts. 

## Repository layout
- `*/application_permissions.csv`, `*/manifest_analysis.csv`, `*/network_security.csv`, etc.: Raw MobSF CSV exports for each application (e.g., `Audi/`, `Kia/`, `Jeep/`, `Tesla/`).
- `scripts/`: Python scripts for data parsing

## App corpus selection

| Manufacturer | App Name | Package Name | Version Analyzed |
|--------------|-----|---------|---------|
| Audi | myAudi | `de.myaudi.mobile.assistant` | 4.18.0 |
| Kia | MyKia | `com.kia.eu.mykia` | 3.0.0 |
| Jeep | Jeep | `com.fca.myconnect.nafta` | 1.98.9 |
| Tesla | Tesla | `com.teslamotors.tesla` | 4.50.1 |
| Chevrolet | myChevrolet | `com.gm.chevrolet.nomad.ownership` | 6.25.0 |
| Acura | AcuraLink | `com.acura.acuralink.connect` | 5.0.46 |

