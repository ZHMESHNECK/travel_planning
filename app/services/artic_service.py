from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from config import ARTIC_CACHE_TTL_SECONDS, ARTWORK_FIELDS, ARTIC_BASE_URL, ARTIC_IMAGE_BASE_URL
import asyncio
import httpx



_artic_cache: dict[int, tuple[dict, datetime]] = {}
_artic_cache_lock = asyncio.Lock()


async def _get_cached_artwork(artwork_id: int) -> dict | None:
    entry = _artic_cache.get(artwork_id)
    if not entry:
        return None

    data, expires_at = entry
    if datetime.now(timezone.utc) >= expires_at:
        async with _artic_cache_lock:
            _artic_cache.pop(artwork_id, None)
        return None

    return data.copy()


async def _set_cached_artwork(artwork_id: int, artwork: dict) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ARTIC_CACHE_TTL_SECONDS)
    async with _artic_cache_lock:
        _artic_cache[artwork_id] = (artwork.copy(), expires_at)


async def fetch_artwork(artwork_id: int) -> dict:
    """
    Fetch a single artwork from the Art Institute of Chicago API.
    Raises HTTP 422 if the artwork does not exist.
    """
    cached = await _get_cached_artwork(artwork_id)
    if cached is not None:
        return cached

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

    data = response.json().get("data")
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=502,
            detail="Unexpected data returned from the Art Institute of Chicago API.",
        )

    artwork = _normalize_artwork(data)
    await _set_cached_artwork(artwork_id, artwork)
    return artwork


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