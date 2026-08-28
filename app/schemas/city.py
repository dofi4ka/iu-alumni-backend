from pydantic import BaseModel


class CityLocation(BaseModel):
    """Matches the Dart CityLocation class"""

    city: str
    country: str
    lat: float
    lng: float

    class Config:
        from_attributes = True


class Coordinates(BaseModel):
    """Response for coordinates endpoint"""

    lat: float
    lng: float


class CitySearchResponse(BaseModel):
    """Response for city search"""

    cities: list[CityLocation]
