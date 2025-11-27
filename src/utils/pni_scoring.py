"""
Privacy scoring module that scrapes Mozilla Privacy Not Included pages
for car manufacturer apps and generates privacy reports.
"""
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
import sys
import re
import json

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup

from apps import available_apps

PROJECT_ROOT = SRC_PATH.parent
GENERATED_ROOT = SRC_PATH / "generated"
PNI_DIR = GENERATED_ROOT / "pni"

# Map manufacturer folder names to Mozilla PNI URL slugs
MANUFACTURER_PNI_URLS: dict[str, str] = {
    "Acura": "https://foundation.mozilla.org/en/privacynotincluded/acura/",
    "Audi": "https://foundation.mozilla.org/en/privacynotincluded/audi/",
    "BMW": "https://foundation.mozilla.org/en/privacynotincluded/bmw/",
    "Buick": "https://foundation.mozilla.org/en/privacynotincluded/buick/",
    "Chevrolet": "https://foundation.mozilla.org/en/privacynotincluded/chevrolet/",
    "Ford": "https://foundation.mozilla.org/en/privacynotincluded/ford/",
    "Honda": "https://foundation.mozilla.org/en/privacynotincluded/honda/",
    "Jeep": "https://foundation.mozilla.org/en/privacynotincluded/jeep/",
    "Kia": "https://foundation.mozilla.org/en/privacynotincluded/kia/",
    "Mercedes": "https://foundation.mozilla.org/en/privacynotincluded/mercedes-benz/",
    "Nissan": "https://foundation.mozilla.org/en/privacynotincluded/nissan/",
    "Subaru": "https://foundation.mozilla.org/en/privacynotincluded/subaru/",
    "Tesla": "https://foundation.mozilla.org/en/privacynotincluded/tesla/",
    "Toyota": "https://foundation.mozilla.org/en/privacynotincluded/toyota/",
}


def fetch_pni_page(url: str) -> str | None:
    """Fetch HTML content from a Mozilla PNI URL."""
    try:
        resp = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; PrivacyScorer/1.0)'
        })
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  Warning: Failed to fetch {url}: {e}")
        return None


def extract_privacy_data(html: str, source_url: str = "") -> dict:
    """Extract privacy data from PNI HTML page."""
    soup = BeautifulSoup(html, 'html.parser')
    data = {
        "url": source_url,
        "product_name": "",
        "company": "",
        "camera_device": None,
        "camera_app": None,
        "microphone_device": None,
        "microphone_app": None,
        "tracks_location_device": None,
        "tracks_location_app": None,
        "collects_biometrics": False,
        "sells_data": False,
        "shares_for_marketing": False,
        "targeted_advertising": False,
        "data_deletion_available": "unclear",
        "opt_out_available": False,
        "user_friendly_privacy_info": None,
        "security_status": "unknown",
        "known_breaches": False,
        "breach_severity": "none",
        "can_use_offline": None,
        "privacy_warning": False,
    }

    # Extract product name from URL
    if source_url and 'privacynotincluded' in source_url:
        match = re.search(r'/privacynotincluded/([^/]+)/?$', source_url)
        if match:
            data["product_name"] = match.group(1).replace('-', ' ').title()

    # Company from specific element
    company_link = soup.find('a', id='product-company-url')
    if company_link:
        data["company"] = company_link.get_text(strip=True)

    text_lower = soup.get_text().lower()

    # Snooping capabilities from "it-uses" divs
    for div in soup.find_all('div', class_='it-uses'):
        h4 = div.find('h4')
        if not h4:
            continue
        label = h4.get_text(strip=True).lower()
        explanation = div.find('div', class_='explanation')
        if explanation:
            text = explanation.get_text().lower()
            device_match = re.search(r'device[:\s]*(yes|no|n/a)', text)
            app_match = re.search(r'app[:\s]*(yes|no|n/a)', text)
            device_val = device_match.group(1) == 'yes' if device_match else None
            app_val = app_match.group(1) == 'yes' if app_match else None

            if 'camera' in label:
                data["camera_device"] = device_val
                data["camera_app"] = app_val
            elif 'microphone' in label:
                data["microphone_device"] = device_val
                data["microphone_app"] = app_val
            elif 'location' in label or 'tracks' in label:
                data["tracks_location_device"] = device_val
                data["tracks_location_app"] = app_val

    # Biometrics
    biometric_terms = ['biometric', 'fingerprint', 'faceprint', 'voiceprint', 'facial recognition']
    data["collects_biometrics"] = any(term in text_lower for term in biometric_terms)

    # Data usage - check ding sections
    for section in soup.find_all('section', class_='show-ding'):
        section_text = section.get_text().lower()
        h3 = section.find('h3')
        h3_text = h3.get_text().lower() if h3 else ""
        if 'how does the company use' in h3_text:
            if 'sell' in section_text:
                data["sells_data"] = True
            if 'marketing' in section_text:
                data["shares_for_marketing"] = True

    # Direct patterns
    if 'sells and shares personal data' in text_lower or 'sells personal data' in text_lower:
        data["sells_data"] = True
    if 'shares personal data' in text_lower:
        data["shares_for_marketing"] = True

    data["targeted_advertising"] = any(term in text_lower for term in
        ['targeted advertising', 'behavioral advertising', 'cross-context behavioral'])

    # User control
    if 'right to' in text_lower and ('delete' in text_lower or 'erasure' in text_lower):
        data["data_deletion_available"] = "some_regions"
    data["opt_out_available"] = bool(re.search(r'opt[- ]?out', text_lower)) or 'do not sell' in text_lower

    # Ratings from h3 + rating pattern
    for h3 in soup.find_all('h3'):
        h3_text = h3.get_text().lower()
        parent = h3.find_parent('section') or h3.find_parent('div', class_='primary-info')
        if not parent:
            continue
        rating = parent.find('p', class_='rating')
        if rating:
            rating_text = rating.get_text(strip=True).lower()
            if 'user-friendly privacy' in h3_text:
                data["user_friendly_privacy_info"] = rating_text == 'yes'
            elif 'track record' in h3_text:
                if rating_text == 'good':
                    data["security_status"] = 'good'
                elif rating_text in ['average', 'needs improvement', 'bad']:
                    data["security_status"] = 'warning'
                section_text = parent.get_text().lower()
                if any(term in section_text for term in ['breach', 'attack', 'hack', 'ransomware']):
                    data["known_breaches"] = True
                    data["breach_severity"] = "significant" if 'significant' in section_text else "minor"

    # Privacy warning
    if soup.find('div', class_='privacy-ding-band') or '*privacy not included' in text_lower:
        data["privacy_warning"] = True

    return data


def calculate_privacy_score(data: dict) -> dict:
    """Calculate privacy score from extracted data."""
    score = {
        "total": 0,
        "grade": "F",
        "label": "Privacy Not Included",
        "data_collection": 0,
        "data_usage": 0,
        "user_control": 0,
        "security": 0,
        "transparency": 0,
    }

    # Data collection (25 pts max)
    dc = 0
    if data.get("camera_device") == False:
        dc += 3
    if data.get("camera_app") == False:
        dc += 3
    if data.get("microphone_device") == False:
        dc += 3
    if data.get("microphone_app") == False:
        dc += 3
    if data.get("tracks_location_device") == False:
        dc += 4
    if data.get("tracks_location_app") == False:
        dc += 4
    if not data.get("collects_biometrics"):
        dc += 5
    score["data_collection"] = min(dc, 25)

    # Data usage (25 pts max)
    du = 0
    if not data.get("sells_data"):
        du += 10
    if not data.get("shares_for_marketing"):
        du += 8
    if not data.get("targeted_advertising"):
        du += 7
    score["data_usage"] = min(du, 25)

    # User control (20 pts max)
    uc = 0
    deletion = data.get("data_deletion_available", "unclear")
    if deletion == "all":
        uc += 10
    elif deletion == "some_regions":
        uc += 5
    elif deletion == "unclear":
        uc += 2
    if data.get("opt_out_available"):
        uc += 5
    if data.get("user_friendly_privacy_info"):
        uc += 5
    score["user_control"] = min(uc, 20)

    # Security (20 pts max)
    sec = 0
    if not data.get("known_breaches"):
        sec += 12
    elif data.get("breach_severity") == "minor":
        sec += 6
    status = data.get("security_status", "unknown")
    if status == "good":
        sec += 8
    elif status == "unknown":
        sec += 4
    score["security"] = min(sec, 20)

    # Transparency (10 pts max)
    tr = 0
    if data.get("can_use_offline"):
        tr += 3
    if data.get("user_friendly_privacy_info"):
        tr += 3
    score["transparency"] = min(tr, 10)

    score["total"] = (
        score["data_collection"] +
        score["data_usage"] +
        score["user_control"] +
        score["security"] +
        score["transparency"]
    )
    score["total"] = max(0, min(100, score["total"]))

    # Grade
    grades = [(80, 'A', 'Privacy Friendly'), (60, 'B', 'Acceptable'),
              (40, 'C', 'Caution Advised'), (20, 'D', 'Privacy Concerns'),
              (0, 'F', 'Privacy Not Included')]
    for threshold, grade, label in grades:
        if score["total"] >= threshold:
            score["grade"] = grade
            score["label"] = label
            break

    return score


def scrape_privacy_scores(base_path: Path = PROJECT_ROOT) -> dict[str, dict]:
    """Scrape privacy scores for all available manufacturers."""
    results: dict[str, dict] = {}
    apps = available_apps(base_path)

    for manufacturer in apps:
        url = MANUFACTURER_PNI_URLS.get(manufacturer)
        if not url:
            print(f"  Skipping {manufacturer}: no PNI URL configured")
            continue

        print(f"  Fetching {manufacturer}...")
        html = fetch_pni_page(url)
        if not html:
            continue

        data = extract_privacy_data(html, url)
        score = calculate_privacy_score(data)
        results[manufacturer] = {"data": data, "score": score}

    return results


def save_privacy_bar_chart(scores: Mapping[str, dict], output_path: Path) -> Path:
    """Generate stacked bar chart of privacy scores by category."""
    if not scores:
        raise ValueError("No privacy scores provided")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    manufacturers = list(scores.keys())
    categories = ["data_collection", "data_usage", "user_control", "security", "transparency"]
    category_labels = ["Data Collection", "Data Usage", "User Control", "Security", "Transparency"]
    category_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    # Build values per category
    values_by_cat = {cat: [scores[m]["score"][cat] for m in manufacturers] for cat in categories}

    x_positions = list(range(len(manufacturers)))

    fig, ax = plt.subplots(figsize=(max(6, len(manufacturers) * 0.9), 5))

    # Stacked bars
    bottom = [0] * len(manufacturers)
    for cat, label, color in zip(categories, category_labels, category_colors):
        vals = values_by_cat[cat]
        ax.bar(x_positions, vals, bottom=bottom, color=color, label=label)
        bottom = [b + v for b, v in zip(bottom, vals)]

    # Add total score labels on top
    for i, m in enumerate(manufacturers):
        total = scores[m]["score"]["total"]
        grade = scores[m]["score"]["grade"]
        ax.text(i, bottom[i] + 1, f"{total} ({grade})",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_ylabel("Privacy Score")
    ax.set_title("Mozilla Privacy Not Included Scores by Manufacturer (by category)")
    ax.set_xticks(x_positions, manufacturers, rotation=45, ha="right")
    max_value = max(bottom) if bottom else 0
    ax.set_ylim(0, max_value + 10)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(title="Category", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def save_privacy_summary_csv(scores: Mapping[str, dict], output_path: Path) -> Path:
    """Save privacy scores summary to CSV."""
    if not scores:
        raise ValueError("No privacy scores provided")

    rows = []
    for m, result in scores.items():
        s = result["score"]
        d = result["data"]
        rows.append({
            "manufacturer": m,
            "total_score": s["total"],
            "grade": s["grade"],
            "label": s["label"],
            "data_collection": s["data_collection"],
            "data_usage": s["data_usage"],
            "user_control": s["user_control"],
            "security": s["security"],
            "transparency": s["transparency"],
            "sells_data": d.get("sells_data", False),
            "shares_for_marketing": d.get("shares_for_marketing", False),
            "known_breaches": d.get("known_breaches", False),
            "privacy_warning": d.get("privacy_warning", False),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("total_score", ascending=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def save_privacy_json(scores: Mapping[str, dict], output_path: Path) -> Path:
    """Save full privacy data to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(scores, f, indent=2)
    return output_path


def generate_pni_report(base_path: Path = PROJECT_ROOT) -> Path | None:
    """Main entry point: scrape and generate PNI reports."""
    print("Scraping Mozilla Privacy Not Included pages...")
    scores = scrape_privacy_scores(base_path)

    if not scores:
        print("No PNI data collected")
        return None

    PNI_DIR.mkdir(parents=True, exist_ok=True)

    # Generate outputs
    chart_path = PNI_DIR / "pni_scores.png"
    save_privacy_bar_chart(scores, chart_path)
    print(f"  Saved chart: {chart_path}")

    csv_path = PNI_DIR / "pni_summary.csv"
    save_privacy_summary_csv(scores, csv_path)
    print(f"  Saved CSV: {csv_path}")

    json_path = PNI_DIR / "pni_full.json"
    save_privacy_json(scores, json_path)
    print(f"  Saved JSON: {json_path}")

    return chart_path


if __name__ == "__main__":
    path = generate_pni_report()
    if path:
        print(f"\nPNI report generated successfully")
    else:
        print("Failed to generate PNI report")
