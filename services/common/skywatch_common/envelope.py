"""Envelope — the common format of messages in the internal topics.

Why: consumers do not need to know about every source. They read the envelope
(who, what, when), while the event body (payload) is parsed only by whoever
needs it, using the schema identified by (source, event_type, schema_version).

Serialization — Avro. Schemas live in schemas/*.avsc.
"""

import io
import os
import time
from dataclasses import dataclass
from pathlib import Path

import fastavro

# In a repo checkout schemas/ lives in the repo root
# (services/common/skywatch_common/ -> ../../..). In a container the package is
# pip-installed into site-packages, so the relative path breaks — there the
# location is set explicitly via SKYWATCH_SCHEMAS_DIR (see the Dockerfiles).
SCHEMAS_DIR = Path(
    os.environ.get("SKYWATCH_SCHEMAS_DIR")
    or Path(__file__).resolve().parents[3] / "schemas"
)


def load_schema(name: str) -> dict:
    """Reads and parses an Avro schema from schemas/<name>.avsc."""
    return fastavro.schema.load_schema(SCHEMAS_DIR / f"{name}.avsc")


ENVELOPE_SCHEMA = load_schema("envelope")
ZTF_ALERT_SCHEMA = load_schema("ztf_alert_lite")


@dataclass
class Envelope:
    source: str
    event_type: str
    event_id: str
    event_ts: int          # timestamp-millis UTC
    schema_version: int
    payload: bytes
    ingest_ts: int = 0

    def __post_init__(self) -> None:
        if not self.ingest_ts:
            self.ingest_ts = int(time.time() * 1000)


def _dumps(record: dict, schema: dict) -> bytes:
    """dict -> Avro bytes (schemaless: the schema is not written into the
    message, both sides take it from the repo; the version travels in the
    envelope)."""
    buf = io.BytesIO()
    fastavro.schemaless_writer(buf, schema, record)
    return buf.getvalue()


def _loads(data: bytes, schema: dict) -> dict:
    return fastavro.schemaless_reader(io.BytesIO(data), schema)


def pack_envelope(env: Envelope) -> bytes:
    return _dumps(env.__dict__, ENVELOPE_SCHEMA)


def unpack_envelope(data: bytes) -> dict:
    return _loads(data, ENVELOPE_SCHEMA)


def pack_ztf_alert(alert: dict) -> bytes:
    return _dumps(alert, ZTF_ALERT_SCHEMA)


def unpack_ztf_alert(data: bytes) -> dict:
    return _loads(data, ZTF_ALERT_SCHEMA)
