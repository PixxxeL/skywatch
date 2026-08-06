"""Конверт (envelope) — единый формат сообщений во внутренних топиках.

Зачем: консьюмерам не нужно знать про каждый источник. Они читают конверт
(кто, что, когда), а тело события (payload) разбирает тот, кому оно нужно,
по схеме, определяемой парой (source, event_type, schema_version).

Сериализация — Avro (см. docs/BASICS.md, «Avro»). Схемы лежат в schemas/*.avsc.
"""

import io
import time
from dataclasses import dataclass
from pathlib import Path

import fastavro

# schemas/ лежит в корне репозитория: services/common/skywatch_common/ -> ../../..
SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"


def load_schema(name: str) -> dict:
    """Читает и парсит Avro-схему из schemas/<name>.avsc."""
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
    """dict -> Avro-байты (schemaless: схема не пишется в сообщение,
    обе стороны берут её из репозитория; версия едет в конверте)."""
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
