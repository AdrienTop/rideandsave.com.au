#!/usr/bin/env python3
"""
update_prices.py
Fetch national Australian fuel prices from GlobalPetrolPrices and patch index.html.

Usage:
  py update_prices.py              # fetch from globalpetrolprices.com + update index.html
  py update_prices.py --dry-run   # show what would change, don't write
  py update_prices.py --manual 1.87 2.27 "25 May 2026"  # skip fetch, use given values

Data source: globalpetrolprices.com — national Australian weekly averages.
"""

import re
import sys
import datetime
import urllib.request
import urllib.error

PETROL_URL = "https://www.globalpetrolprices.com/Australia/gasoline_prices/"
DIESEL_URL = "https://www.globalpetrolprices.com/Australia/diesel_prices/"
INDEX_HTML = "index.html"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}


def _fetch_text(url):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text)
    return text


def fetch_prices():
    """Scrape national petrol/diesel prices from GlobalPetrolPrices.com.

    Returns (petrol_dollars, diesel_dollars, date_str).
    Raises ValueError if prices aren't found in the HTML.
    """
    petrol_text = _fetch_text(PETROL_URL)
    diesel_text = _fetch_text(DIESEL_URL)

    # "...Australia is AUD 1.84 per liter or USD..." — anchor on "or USD" to skip historical avg
    price_re = re.compile(r"AUD ([\d.]+) per liter or USD")

    petrol_m = price_re.search(petrol_text)
    diesel_m = price_re.search(diesel_text)

    if not petrol_m:
        raise ValueError(
            "Petrol price not found on GlobalPetrolPrices.\n"
            "Use --manual mode (see usage at top of script)."
        )
    if not diesel_m:
        raise ValueError(
            "Diesel price not found on GlobalPetrolPrices.\n"
            "Use --manual mode (see usage at top of script)."
        )

    petrol = float(petrol_m.group(1))
    diesel = float(diesel_m.group(1))

    # "...was updated on 25-May-2026..." -> "25 May 2026"
    date_m = re.search(r"updated on (\d{1,2}-\w+-\d{4})", petrol_text)
    if date_m:
        date_str = date_m.group(1).replace("-", " ")
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
        print(f"Fetching {PETROL_URL} ...")
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
