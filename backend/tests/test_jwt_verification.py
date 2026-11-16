"""Verify actual signatures/claims; no auth dependency or jwt.decode bypass."""
import time
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from app.core import auth
from app.core.config import settings


@pytest.fixture
def verifier(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://issuer.example")
    private = ec.generate_private_key(ec.SECP256R1())
    client = SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=private.public_key()))
    monkeypatch.setattr(auth, "_jwks_client", lambda url: client)
    claims = {
        "sub": str(uuid4()), "aud": "authenticated", "role": "authenticated",
        "iss": "https://issuer.example/auth/v1", "iat": int(time.time()),
        "exp": int(time.time()) + 120,
    }
    return private, claims, client


def verify(token):
    return auth.get_current_user(
        Request({"type": "http"}),
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
    )


@pytest.mark.parametrize("algorithm", ["ES256", "RS256"])
def test_valid_asymmetric_token(algorithm, verifier):
    private, claims, client = verifier
    if algorithm == "RS256":
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        client.get_signing_key_from_jwt = lambda token: SimpleNamespace(key=private.public_key())
    token = jwt.encode(claims, private, algorithm=algorithm)
    assert str(verify(token)) == claims["sub"]


@pytest.mark.parametrize("claim,value", [
    ("exp", 1), ("iat", 9999999999), ("aud", "different-app"),
    ("iss", "https://attacker.example/auth/v1"), ("role", "anon"),
    ("role", "service_role"), ("sub", "not-a-uuid"),
])
def test_invalid_signed_claims_rejected(verifier, claim, value):
    private, claims, _ = verifier
    claims[claim] = value
    with pytest.raises(HTTPException) as error:
        verify(jwt.encode(claims, private, algorithm="ES256"))
    assert error.value.status_code == 401


@pytest.mark.parametrize("claim", ["exp", "iat", "sub", "iss", "aud"])
def test_required_claims_cannot_be_omitted(verifier, claim):
    private, claims, _ = verifier
    del claims[claim]
    with pytest.raises(HTTPException) as error:
        verify(jwt.encode(claims, private, algorithm="ES256"))
    assert error.value.status_code == 401


def test_wrong_signature_is_rejected(verifier):
    _, claims, _ = verifier
    attacker_key = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(HTTPException) as error:
        verify(jwt.encode(claims, attacker_key, algorithm="ES256"))
    assert error.value.status_code == 401


def test_hmac_algorithm_is_rejected_even_with_matching_key(verifier):
    _, claims, client = verifier
    secret = "test-only-hmac-secret-with-sufficient-length"
    client.get_signing_key_from_jwt = lambda token: SimpleNamespace(key=secret)
    with pytest.raises(HTTPException) as error:
        verify(jwt.encode(claims, secret, algorithm="HS256"))
    assert error.value.status_code == 401


def test_jwks_outage_is_temporary_unavailability(verifier):
    private, claims, client = verifier
    def unavailable(token):
        raise jwt.PyJWKClientConnectionError("private upstream error")
    client.get_signing_key_from_jwt = unavailable
    with pytest.raises(HTTPException) as error:
        verify(jwt.encode(claims, private, algorithm="ES256"))
    assert error.value.status_code == 503
    assert "private upstream" not in error.value.detail
