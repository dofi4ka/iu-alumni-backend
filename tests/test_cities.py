"""Tests for the embedded cities dataset and the cities/map endpoints."""
from app.core.security import get_current_user
from app.models.users import Alumni
from app.services.cities import get_coordinates, search_cities


def test_search_is_prefix_and_accent_insensitive():
    assert any(c == "Innopolis" for c, *_ in search_cities("inno", 10))
    assert any(c == "Zürich" for c, *_ in search_cities("zuri", 10))
    assert any(c == "Moscow" for c, *_ in search_cities("mosc", 10))


def test_search_respects_limit():
    assert len(search_cities("san", 5)) == 5


def test_coordinates_lookup():
    assert get_coordinates("Moscow", "Russia") == (55.75204, 37.61781)
    # Innopolis is pinned from OSM, not GeoNames.
    assert get_coordinates("Innopolis", "Russia") == (55.7522117, 48.7445682)
    assert get_coordinates("Nowhere", "Nowhereland") is None


def test_cities_routes(client, db_session):
    alumni = Alumni(
        id="city-tester",
        email="city-tester@innopolis.university",
        first_name="City",
        last_name="Tester",
        graduation_year="2026",
    )
    db_session.add(alumni)
    db_session.commit()
    client.app.dependency_overrides[get_current_user] = lambda: alumni

    search = client.get("/api/v1/cities/search", params={"q": "inno"})
    assert search.status_code == 200
    cities = search.json()["cities"]
    assert any(c["city"] == "Innopolis" and c["country"] == "Russia" for c in cities)

    empty = client.get("/api/v1/cities/search", params={"q": "  "})
    assert empty.status_code == 200
    assert empty.json() == {"cities": []}

    coords = client.get(
        "/api/v1/cities/coordinates",
        params={"city": "Moscow", "country": "Russia"},
    )
    assert coords.status_code == 200
    assert coords.json() == {"lat": 55.75204, "lng": 37.61781}
