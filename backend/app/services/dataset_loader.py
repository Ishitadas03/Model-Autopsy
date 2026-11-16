"""Load the registered CSV bytes identically for baseline and queued execution."""
from __future__ import annotations

import hashlib
import io

import pandas as pd

from app.services.storage_service import storage_service


def load_registered_csv(dataset_id: str, storage_key: str | None = None,
                        expected_sha256: str | None = None) -> pd.DataFrame:
    """Caller authorizes the dataset; this layer verifies its stored contents."""
    key = storage_key or f"datasets/{dataset_id}/data.csv"
    raw = storage_service.retrieve_bytes(key)
    if raw is None:
        raise FileNotFoundError("Registered dataset is unavailable in configured storage")
    if expected_sha256 and hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Dataset checksum mismatch; refusing to evaluate changed data")
    return pd.read_csv(io.BytesIO(raw))
