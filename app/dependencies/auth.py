import os
import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def validate_basic_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify HTTP Basic auth credentials against environment variables."""
    username = os.getenv("BASIC_AUTH_USERNAME")
    password = os.getenv("BASIC_AUTH_PASSWORD")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Basic auth is not configured. Set BASIC_AUTH_USERNAME and "
                "BASIC_AUTH_PASSWORD in environment variables."
            ),
        )

    valid_username = secrets.compare_digest(credentials.username, username)
    valid_password = secrets.compare_digest(credentials.password, password)

    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
