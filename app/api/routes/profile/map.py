from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.profile import MapLocationGroup, MapLocationsResponse
from app.services import cities as city_service


router = APIRouter()


@router.get("/map", response_model=MapLocationsResponse)
def get_map_locations(
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Return alumni counts grouped by location for map pin display.

    Only alumni with ``show_location=True`` and a resolvable city/country are
    included. Coordinates come from the in-memory city index, so the mobile
    client does not need one round-trip per city to look up lat/lng.

    The location string is stored as ``"Country, City"`` (comma-space separated);
    we split it with PostgreSQL's ``split_part()`` and resolve lat/lng against
    the embedded cities dataset. Locations that don't resolve are dropped,
    matching the previous JOIN-with-cities-table semantics.
    """
    country_expr = func.split_part(Alumni.location, ", ", 1)
    city_expr = func.split_part(Alumni.location, ", ", 2)

    rows = (
        db.query(
            country_expr.label("country"),
            city_expr.label("city"),
            func.count(Alumni.id).label("count"),
        )
        .filter(
            Alumni.show_location.is_(True),
            Alumni.location.isnot(None),
            Alumni.location.like("%, %"),
            Alumni.is_verified.is_(True),
            Alumni.is_banned.is_(False),
        )
        .group_by(country_expr, city_expr)
        .all()
    )

    locations = []
    for row in rows:
        coords = city_service.get_coordinates(row.city, row.country)
        if coords is None:
            continue
        locations.append(
            MapLocationGroup(
                country=row.country,
                city=row.city,
                lat=coords[0],
                lng=coords[1],
                count=row.count,
            )
        )
    return MapLocationsResponse(locations=locations)
