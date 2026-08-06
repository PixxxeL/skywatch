# SkyWatch — architecture

## Overview

```
external sources                       SkyWatch
─────────────────                      ────────────────────────────────────────────
Fink (Kafka, Avro)  ──► connector-ztf ──► Kafka: ingest.ztf.alerts ─┬─► consumer-alerts ──► ClickHouse
GCN (Kafka)  [later]──► connector-gcn ──► Kafka: ingest.gcn.notices ┘        (group: ch-writer)
NOAA (HTTP)  [later]──► connector-noaa ─► Kafka: ingest.noaa.spaceweather
                                          Kafka: ingest.deadletter ◄── malformed messages

ClickHouse ──► query-api (FastAPI) ──► dashboard (Vue) ── nginx (prod)
```

The principle: a **connector** talks to the outside world and normalizes the data,
the **internal Kafka** is a single bus, and **consumers** know nothing about the sources.

## Conventions

### Topics

`ingest.<source>.<type>` — e.g. `ingest.ztf.alerts`. 3 partitions (enough at this scale;
in production the number is derived from throughput). The message key is a stable entity ID
(for ZTF — `objectId`), so that all events of one object land in one partition and keep
their order.

### Envelope

All internal messages are Avro, schema [schemas/envelope.avsc](schemas/envelope.avsc):

| Field           | Type   | Meaning                                          |
|-----------------|--------|--------------------------------------------------|
| `source`        | string | `ztf`, `gcn`, ...                                |
| `event_type`    | string | `alert`, `notice`, ...                           |
| `event_id`      | string | unique event ID assigned by the source           |
| `event_ts`      | long   | event time (timestamp-millis, UTC)               |
| `ingest_ts`     | long   | time the connector received the event            |
| `schema_version`| int    | payload schema version                           |
| `payload`       | bytes  | normalized event body (Avro, its own schema)     |

The ZTF payload is [schemas/ztf_alert_lite.avsc](schemas/ztf_alert_lite.avsc): a compact
subset of the full ZTF alert (we don't need all ~60 fields and the image cutouts). Schemas
live as files in the repo and are loaded by services via `services/common`; a Schema Registry
is deliberately not used (fewer moving parts; the envelope carries `schema_version`).

### Delivery guarantees

At-least-once: the consumer commits offsets **after** the batch is successfully inserted
into ClickHouse. Duplicates are handled on the ClickHouse side: `ReplacingMergeTree` over
`(object_id, candidate_id)` plus `FINAL`/`GROUP BY` in queries where exactness matters.

A message that cannot be parsed goes to `ingest.deadletter` with headers
`error`, `src_topic`, `src_partition`, `src_offset` — and is committed
(it does not block the stream).

## ClickHouse

Database `skywatch`, DDL: [deploy/clickhouse/init/01_schema.sql](deploy/clickhouse/init/01_schema.sql).

- `ztf_alerts` — ReplacingMergeTree, `PARTITION BY toYYYYMM(event_ts)`,
  `ORDER BY (object_id, candidate_id)`. The raw alert is kept in `raw` (ZSTD) so history
  can be re-parsed if the schema changes.
- `alerts_daily` — SummingMergeTree + a materialized view: per-day/per-classification
  counters are computed at insert time.

## Services

- **connector-ztf** — the only service that knows about Fink. Source modes
  (fink / synthetic, archive replay planned) behind a common source interface —
  modes are switched by configuration, the rest of the code stays the same.
- **consumer-alerts** — a batcher: accumulates up to `BATCH_SIZE` messages or
  `BATCH_TIMEOUT_S` seconds, inserts them as a single INSERT, then commits offsets.
- **query-api** — a thin SQL→JSON layer. No business logic, only parameterized queries.

## How to add a new source (e.g. GCN)

1. Copy `services/connector-ztf` → `services/connector-gcn`, implement your own source
   (for GCN — a `gcn-kafka` consumer; for HTTP sources — a poller).
2. Describe the payload schema in `schemas/gcn_notice.avsc`, wrap it in the same envelope.
3. Add the `ingest.gcn.notices` topic to `deploy/kafka/create-topics.sh`.
4. Table + (if needed) an MV in `deploy/clickhouse/init/`.
5. Consumer: either a new small service, or subscribe consumer-alerts to the second topic
   and dispatch by the envelope's `source` field.
6. Service in compose (prod profile), an endpoint in query-api, a tab in the dashboard.

## Decisions and reasons (in short)

- **Own Kafka between the source and the consumers** instead of everyone reading Fink
  directly: decoupling, own retention/replay, a single internal format.
- **Avro without a Registry**: an industry-standard format with minimal infrastructure.
  A Registry is an obvious next step and has a clear place in the compose file.
- **aiokafka** rather than confluent-kafka: pure Python + asyncio, easier to install
  everywhere; confluent-kafka (librdkafka) remains an option for future connectors.
- **Two compose files** (`docker-compose.dev.yml` — infrastructure only, code runs on the
  host; `docker-compose.prod.yml` — infrastructure + applications): each reads as a whole,
  no profiles or overrides.
