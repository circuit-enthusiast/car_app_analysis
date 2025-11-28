# car_app_analysis

## Overview
This repository aggregates static analysis data for a corpus of North American automotive companion applications drawn from the Mozilla Foundation's *Privacy Not Included* study. Each application directory stores CSV exports from Mobile Security Framework (MobSF) runs, while the Python utilities now live in the `src/` directory to normalize the data, score risk, and generate comparative charts. 

## Repository layout
- `*/application_permissions.csv`, `*/manifest_analysis.csv`, `*/network_security.csv`, etc.: Raw MobSF CSV exports for each application (e.g., `Audi/`, `Kia/`, `Jeep/`, `Tesla/`).
- `src/main.py`: Batch runner that iterates through every analytics module (trackers, application permissions, certificate security, network security, and the Mozilla PNI scraper) and kicks off report generation.
- `src/apps.py`: Defines the canonical list of manufacturer directories and exposes `available_apps()` so every analysis only touches folders that actually exist in the checkout.
- `src/utils/`: Purpose-built analyzers, each with a `generate_*` entry point. Highlights:
  - `application_permissions.py`: Loads each `application_permissions.csv`, summarizes MobSF risk classifications with `pandas`, and writes both `permissions_summary.csv` plus the stacked/risk mix/score PNG charts under `src/generated/permissions/`.
  - `trackers.py`: Counts rows in every `trackers.csv` file and produces `tracker_counts.png` so we can quickly compare embedded SDK usage per manufacturer.
  - `certificate_analysis.py` & `network_analysis.py`: Collapse MobSF severity columns from `certificate_analysis.csv` and `network_security.csv`, convert them into weighted scores via `scoring.py`, and emit both summary CSVs and stacked bar charts (`src/generated/certificates/` and `src/generated/network/`).
  - `pni_scoring.py`: Scrapes the Mozilla *Privacy Not Included* site with `BeautifulSoup`, calculates privacy grades, and exports the bar chart (`pni_scores.png`), CSV summary, and full JSON dataset in `src/generated/pni/`.
  - `scoring.py`: Shared helpers that normalize severity labels, tally risk buckets, and compute weighted scores that the other modules reuse.
- `src/generated/`: Output tree created by the analyzers (e.g., `permissions/`, `trackers/`, `certificates/`, `network/`, `pni/`), containing the derived CSVs, PNG charts, and JSON artifacts described above.

## App corpus selection

| Manufacturer | App Name | Package Name | Version Analyzed |
|--------------|-----|---------|---------|
| Audi | myAudi | `de.myaudi.mobile.assistant` | 4.18.0 |
| Kia | MyKia | `com.kia.eu.mykia` | 3.0.0 |
| Jeep | Jeep | `com.fca.myconnect.nafta` | 1.98.9 |
| Tesla | Tesla | `com.teslamotors.tesla` | 4.50.1 |
| Chevrolet | myChevrolet | `com.gm.chevrolet.nomad.ownership` | 6.25.0 |
| Acura | AcuraLink | `com.acura.acuralink.connect` | 5.0.46 |
| Mercedes | Mercedes-Benz Connect | `com.daimler.ris.mercedesme.ece.android` | 1.62.0 |
| BMW | My BMW | `de.bmw.connected.mobile20.na` | 5.9.4 |
| Buick | myBuick | `com.gm.buick.nomad.ownership` | 6.25.0 |
| Ford | FordPass | `https://fordpass.en.uptodown.com` | 6.9.4 |
| Honda | HondaLink | `com.honda.hondalink.connect` | 5.0.46 |
| Nissan | NissanConnect® EV & Services | `com.aqsmartphone.android.nissan` | 8.0.4 |
| Subaru | MySubaru |`com.subaru.telematics.app.remote` | 3.2.1 |
| Toyota | myToyota | `com.toyota.oneapp.eu` | 2.8.1 |
