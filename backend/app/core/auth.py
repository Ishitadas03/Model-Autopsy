"""Supabase Auth JWT verification and tenant isolation.

Only asymmetric JWT signing keys are accepted. Never trust user IDs supplied in
request bodies or HTTP headers. The test-only bypass cannot be used in prod.
"""
from __future__ import annotations

from functools import lru_cache
from uuid import UUID

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=4)
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True, lifespan=300, timeout=5)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UUID | None:
    """Return verified user id; None is allowed only during explicit CI test mode."""
    if settings.APP_ENV == "test" and not settings.AUTH_REQUIRED:
        return None
    if not settings.AUTH_REQUIRED:
        raise HTTPException(status_code=503, detail="Authentication cannot be disabled in this environment")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not settings.SUPABASE_URL:
        raise HTTPException(status_code=503, detail="Authentication service is not configured")

    base = settings.SUPABASE_URL.rstrip("/")
    url = base + "/auth/v1/.well-known/jwks.json"
    try:
        key = _jwks_client(url).get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            key.key,
            algorithms=["RS256", "ES256"],
            issuer=base + "/auth/v1",
            audience="authenticated",
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            leeway=30,
        )
        if claims.get("role") != "authenticated":
            raise ValueError("Unexpected token role")
        user = UUID(str(claims["sub"]))
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=401, detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        # Do not leak JWKS server errors or signing-key details.
        raise HTTPException(status_code=503, detail="Authentication verification temporarily unavailable")
    request.state.user_id = user
    return user


def can_read_dataset(dataset, user_id: UUID | None) -> bool:
    if user_id is None and settings.APP_ENV == "test":
        return True
    return bool(
        dataset is not None and (
            dataset.owner_id == user_id or (
                dataset.is_public and dataset.owner_id is None
            )
        )
    )


def can_read_experiment(experiment, user_id: UUID | None) -> bool:
    if user_id is None and settings.APP_ENV == "test":
        return True
    return bool(
        experiment is not None and
        experiment.owner_id is not None and
        experiment.owner_id == user_id
    )


def assert_dataset_access(dataset, user_id: UUID | None) -> None:
    if not can_read_dataset(dataset, user_id):
        raise HTTPException(status_code=404, detail="Dataset not found")


def assert_experiment_access(experiment, user_id: UUID | None) -> None:
    if not can_read_experiment(experiment, user_id):
        raise HTTPException(status_code=404, detail="Experiment not found")
