#!/usr/bin/env python3
"""
update_prices.py
Fetch current fuel prices from the NRMA weekly report and patch index.html.

Usage:
  py update_prices.py              # fetch from NRMA + update index.html
  py update_prices.py --dry-run   # show what would change, don't write
  py update_prices.py --manual 1.87 2.27 "25 May 2026"  # skip fetch, use given values

If the NRMA page is JavaScript-rendered and prices aren't found automatically,
use --manual with the values you see on the weekly report page.
"""

import re
import sys
import datetime
import urllib.request
import urllib.error

REPORT_URL = "https://www.mynrma.com.au/cars-and-driving/fuel-finder/weekly-report"
INDEX_HTML  = "index.html"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}


def fetch_prices():
    """Scrape petrol/diesel prices from the NRMA weekly report page.

    Returns (petrol_dollars, diesel_dollars, date_str).
    Raises ValueError if prices aren't found in the raw HTML (JS-rendered page).
    """
    req = urllib.request.Request(REPORT_URL, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    # Flatten HTML to plain text for regex search
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text)

    # "regular unleaded ... 186.8 cents per litre"
    petrol_m = re.search(
        r"(?:regular\s+unleaded|ULP)[^.]{0,150}?(\d{2,3}(?:\.\d)?)\s*cents?\s*per\s*litre",
        text, re.IGNORECASE,
    )
    # "diesel ... 227.2 cents per litre"
    diesel_m = re.search(
        r"\bdiesel\b[^.]{0,150}?(\d{2,3}(?:\.\d)?)\s*cents?\s*per\s*litre",
        text, re.IGNORECASE,
    )

    if not petrol_m:
        raise ValueError(
            "Petrol price not found in raw HTML.\n"
            "The NRMA page may require JavaScript to render prices.\n"
            "Use --manual mode (see usage at top of script)."
        )
    if not diesel_m:
        raise ValueError(
            "Diesel price not found in raw HTML.\n"
            "Use --manual mode (see usage at top of script)."
        )

    petrol = float(petrol_m.group(1)) / 100
    diesel = float(diesel_m.group(1)) / 100

    # Try to extract the report date, e.g. "Monday, 25 May 2026"
    date_m = re.search(
        r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
        r"[,\s]+(\d{1,2}\s+\w+\s+\d{4})",
        text, re.IGNORECASE,
    )
    if date_m:
        date_str = date_m.group(1).strip()
    else:
        today = datetime.date.today()
        date_str = f"{today.day} {today.strftime('%B %Y')}"

    return petrol, diesel, date_str


def _sub(html, pattern, repl, desc, changes):
    new = re.sub(pattern, repl, html)
    if new != html:
        changes.append(desc)
    return new


def patch_html(html, petrol, diesel, date_str):
    """Apply all price/date substitutions. Returns (new_html, list_of_changes)."""
    p = f"{petrol:.2f}"
    d = f"{diesel:.2f}"
    we = f"w/e {date_str}"
    changes = []

    # 1. fuelPrice input default value
    html = _sub(
        html,
        r'(<input[^>]+id="fuelPrice"[^>]+value=")[\d.]+(")',
        rf'\g<1>{p}\g<2>',
        f'fuelPrice input default -> {p}',
        changes,
    )

    # 2. updateFuelPrice() petrol branch
    html = _sub(
        html,
        r"(selFuel==='petrol'\)\s*document\.getElementById\('fuelPrice'\)\.value=')[\d.]+(')",
        rf"\g<1>{p}\g<2>",
        f"updateFuelPrice petrol -> {p}",
        changes,
    )

    # 3. updateFuelPrice() diesel branch
    html = _sub(
        html,
        r"(selFuel==='diesel'\)\s*document\.getElementById\('fuelPrice'\)\.value=')[\d.]+(')",
        rf"\g<1>{d}\g<2>",
        f"updateFuelPrice diesel -> {d}",
        changes,
    )

    # 4. calculate() fallback value  e.g. ||1.81;
    html = _sub(
        html,
        r"(\|\|)[\d.]+(\s*;\s*\n\s*fuelCost)",
        rf"\g<1>{p}\g<2>",
        f"calculate() fallback -> {p}",
        changes,
    )

    # 5. Date label in hint text  "w/e 18 May 2026"
    html = _sub(
        html,
        r"w/e \d{1,2} \w+ \d{4}",
        we,
        f"Date label -> {we}",
        changes,
    )

    # 6. Fuel alert banner  "⚠️ Petrol averaging $1.80+ per litre"
    html = _sub(
        html,
        r"(⚠️ Petrol averaging \$)[\d.]+(\+ per litre)",
        rf"\g<1>{p}\g<2>",
        f"Alert banner -> ${p}+",
        changes,
    )

    return html, changes


def main():
    dry_run = "--dry-run" in sys.argv

    # --manual PETROL DIESEL DATE
    manual_i = next((i for i, a in enumerate(sys.argv) if a == "--manual"), None)
    if manual_i is not None:
        try:
            petrol   = float(sys.argv[manual_i + 1])
            diesel   = float(sys.argv[manual_i + 2])
            date_str = sys.argv[manual_i + 3]
        except (IndexError, ValueError):
            print("Usage: py update_prices.py --manual <petrol> <diesel> <date>")
            print('Example: py update_prices.py --manual 1.87 2.27 "25 May 2026"')
            sys.exit(1)
        print(f"[manual]  Petrol: ${petrol:.2f}/L  Diesel: ${diesel:.2f}/L  Date: {date_str}")
    else:
        print(f"Fetching {REPORT_URL} ...")
        try:
            petrol, diesel, date_str = fetch_prices()
        except ValueError as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"Network error: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"Petrol:   ${petrol:.2f}/L")
        print(f"Diesel:   ${diesel:.2f}/L")
        print(f"Date:     {date_str}")

    print()

    with open(INDEX_HTML, encoding="utf-8") as f:
        original = f.read()

    new_html, changes = patch_html(original, petrol, diesel, date_str)

    if not changes:
        print("No changes — prices already up to date.")
        return

    print("Changes:")
    for c in changes:
        print(f"  {c}")

    if dry_run:
        print("\n[dry-run] index.html not modified.")
        return

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"\nindex.html updated.")


if __name__ == "__main__":
    main()
