import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


ARTIC_BASE_URL = "https://api.artic.edu/api/v1"
ARTIC_IMAGE_BASE_URL = "https://www.artic.edu/iiif/2"
ARTIC_CACHE_TTL_SECONDS = int(os.getenv("ARTIC_CACHE_TTL_SECONDS", "300"))

# Fields we need from the artwork endpoint
ARTWORK_FIELDS = "id,title,artist_display,place_of_origin,image_id"


# DATABASE_URL can be overridden via environment variable (e.g. in Docker)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./travel_planner.db",
)

MAX_PLACES_PER_PROJECT = 10
