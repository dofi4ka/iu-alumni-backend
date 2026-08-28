"""Regenerate app/data/cities.tsv from GeoNames cities5000 + countryInfo.

Idempotent. Run with:
    python -m scripts.generate_cities_data

The output is a TSV of ``city<TAB>country<TAB>lat<TAB>lng``, one row per city,
deduped on (city, country) keeping the highest-population entry, plus a pinned
Innopolis row (GeoNames records its population as 96, so it is absent from
every tiered dump; coordinates come from OpenStreetMap/Nominatim).
"""
from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

GEONAMES = "https://download.geonames.org/export/dump"
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "data" / "cities.tsv"

# lat/lng from OpenStreetMap (Nominatim), town of Innopolis, Tatarstan, Russia.
INNOPOLIS = ("Innopolis", "Russia", 55.7522117, 48.7445682)


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "iu-alumni-backend"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _countries(txt: str) -> dict[str, str]:
    """Map ISO-3166 2-letter code -> common English country name."""
    out: dict[str, str] = {}
    for line in txt.splitlines():
        if line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) > 4 and parts[0] and parts[4]:
            out[parts[0]] = parts[4]
    return out


def main() -> None:
    with zipfile.ZipFile(io.BytesIO(_fetch(f"{GEONAMES}/cities5000.zip"))) as zf:
        cities_txt = zf.read("cities5000.txt").decode("utf-8")
    countries = _countries(_fetch(f"{GEONAMES}/countryInfo.txt").decode("utf-8"))

    # (city.casefold(), country) -> (city, country, lat, lng, population)
    best: dict[tuple[str, str], tuple[str, str, float, float, int]] = {}
    for line in cities_txt.splitlines():
        p = line.split("\t")
        if len(p) < 15:
            continue
        name, cc = p[1].strip(), p[8]
        country = countries.get(cc)
        if not name or country is None:
            continue
        try:
            lat, lng = float(p[4]), float(p[5])
            pop = int(p[14]) if p[14] else 0
        except ValueError:
            continue
        key = (name.casefold(), country)
        if pop >= best.get(key, ("", "", 0.0, 0.0, -1))[4]:
            best[key] = (name, country, lat, lng, pop)

    rows = [(name, country, lat, lng) for name, country, lat, lng, _ in best.values()]
    rows.append(INNOPOLIS)
    rows.sort(key=lambda r: (r[0].casefold(), r[1]))

    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8", newline="") as f:
        for name, country, lat, lng in rows:
            f.write(f"{name}\t{country}\t{lat}\t{lng}\n")
    print(f"wrote {len(rows)} cities to {DATA}")


if __name__ == "__main__":
    main()
