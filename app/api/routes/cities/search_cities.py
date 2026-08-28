from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.schemas.city import CityLocation, CitySearchResponse, Coordinates
from app.services import cities as city_service


router = APIRouter()


@router.get("/coordinates", response_model=Coordinates | None)
async def get_coordinates(
    city: str = Query(..., description="City name"),
    country: str = Query(..., description="Country name"),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Get coordinates (lat/lng) for a specific city and country.

    Returns null if the city/country combination is not found.
    """
    result = city_service.get_coordinates(city, country)
    if result is None:
        return None
    return Coordinates(lat=result[0], lng=result[1])


@router.get("/search", response_model=CitySearchResponse)
async def search_cities(
    q: str = Query(..., description="Search query for city name", min_length=1),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=10),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """
    Search for cities by partial name match (prefix, case- and accent-insensitive).

    Returns up to 10 cities matching the search query.
    """
    search_term = q.strip()

    if not search_term:
        return CitySearchResponse(cities=[])

    rows = city_service.search_cities(search_term, limit)
    return CitySearchResponse(
        cities=[
            CityLocation(city=c, country=cc, lat=la, lng=lo) for c, cc, la, lo in rows
        ]
    )
