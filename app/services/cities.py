"""In-memory city index loaded once from app/data/cities.tsv.

Replaces the ``cities`` DB table. Prefix search is a bisect over the sorted
folded names; coordinates lookup is a dict keyed by (folded city, folded country).
"""
from __future__ import annotations

import bisect
from pathlib import Path
import unicodedata

_DATA = Path(__file__).resolve().parents[1] / "data" / "cities.tsv"


def _fold(s: str) -> str:
    """Lowercase and strip diacritics so 'Zürich' matches 'zurich'."""
    return (
        unicodedata.normalize("NFKD", s)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )


class _CityIndex:
    def __init__(self) -> None:
        self._rows: list[tuple[str, str, float, float]] = []
        self._by_key: dict[tuple[str, str], tuple[float, float]] = {}

        for line in _DATA.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            city, country, lat, lng = line.split("\t")
            self._rows.append((city, country, float(lat), float(lng)))

        self._rows.sort(key=lambda r: (_fold(r[0]), r[1].casefold()))
        self._keys = [_fold(r[0]) for r in self._rows]
        for city, country, lat, lng in self._rows:
            self._by_key.setdefault((_fold(city), _fold(country)), (lat, lng))

    def search(self, prefix: str, limit: int) -> list[tuple[str, str, float, float]]:
        key = _fold(prefix)
        i = bisect.bisect_left(self._keys, key)
        out: list[tuple[str, str, float, float]] = []
        n = len(self._keys)
        while i < n and len(out) < limit and self._keys[i].startswith(key):
            out.append(self._rows[i])
            i += 1
        return out

    def coordinates(self, city: str, country: str) -> tuple[float, float] | None:
        return self._by_key.get((_fold(city), _fold(country)))


INDEX = _CityIndex()


def search_cities(prefix: str, limit: int = 10) -> list[tuple[str, str, float, float]]:
    return INDEX.search(prefix, limit)


def get_coordinates(city: str, country: str) -> tuple[float, float] | None:
    return INDEX.coordinates(city, country)
