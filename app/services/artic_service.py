import httpx
from fastapi import HTTPException

ARTIC_BASE_URL = "https://api.artic.edu/api/v1"
ARTIC_IMAGE_BASE_URL = "https://www.artic.edu/iiif/2"

# Fields we need from the artwork endpoint
ARTWORK_FIELDS = "id,title,artist_display,place_of_origin,image_id"


async def fetch_artwork(artwork_id: int) -> dict:
    """
    Fetch a single artwork from the Art Institute of Chicago API.
    Raises HTTP 422 if the artwork does not exist.
    """
    url = f"{ARTIC_BASE_URL}/artworks/{artwork_id}"
    params = {"fields": ARTWORK_FIELDS}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Could not reach the Art Institute of Chicago API: {exc}",
            )

    if response.status_code == 404:
        raise HTTPException(
            status_code=422,
            detail=f"Artwork with ID {artwork_id} does not exist in the Art Institute of Chicago API.",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Unexpected response from the Art Institute of Chicago API.",
        )

    data = response.json().get("data", {})
    return _normalize_artwork(data)


def _normalize_artwork(data: dict) -> dict:
    """Extract and normalize fields we care about from raw API data."""
    image_id = data.get("image_id")
    image_url = (
        f"{ARTIC_IMAGE_BASE_URL}/{image_id}/full/843,/0/default.jpg"
        if image_id
        else None
    )

    return {
        "external_id": data["id"],
        "title": data.get("title") or "Untitled",
        "artist": data.get("artist_display"),
        "place_of_origin": data.get("place_of_origin"),
        "image_url": image_url,
    }