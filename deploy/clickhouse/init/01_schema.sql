-- Runs automatically on the first start of the ClickHouse container.

CREATE DATABASE IF NOT EXISTS skywatch;

-- Main alerts table.
-- ReplacingMergeTree(ingest_ts): rows with the same (object_id, candidate_id)
-- collapse into one during background merges (the freshest by ingest_ts wins) —
-- this is how we absorb duplicates from at-least-once Kafka delivery.
CREATE TABLE IF NOT EXISTS skywatch.ztf_alerts
(
    object_id       String,                       -- ZTF object ID, e.g. ZTF26aaabbbc
    candidate_id    UInt64,                       -- unique ID of a single measurement
    event_ts        DateTime64(3, 'UTC'),         -- observation time
    ingest_ts       DateTime64(3, 'UTC'),         -- time our connector received the event
    ra              Float64,                      -- right ascension, degrees
    dec             Float64,                      -- declination, degrees
    magpsf          Float32,                      -- magnitude (brightness; lower = brighter)
    sigmapsf        Float32,                      -- its uncertainty
    fid             UInt8,                        -- filter: 1=g (green), 2=r (red), 3=i
    classification  LowCardinality(String),       -- class from Fink: SN candidate, Solar System...
    class_score     Float32,                      -- classifier confidence 0..1
    raw             String CODEC(ZSTD(3))         -- original event (JSON) for future re-parsing
)
ENGINE = ReplacingMergeTree(ingest_ts)
PARTITION BY toYYYYMM(event_ts)
ORDER BY (object_id, candidate_id);

-- Daily aggregates: filled automatically by a materialized view on every insert.
-- SummingMergeTree adds up cnt of rows with the same key during merges.
CREATE TABLE IF NOT EXISTS skywatch.alerts_daily
(
    day            Date,
    classification LowCardinality(String),
    cnt            UInt64
)
ENGINE = SummingMergeTree
ORDER BY (day, classification);

CREATE MATERIALIZED VIEW IF NOT EXISTS skywatch.alerts_daily_mv
TO skywatch.alerts_daily
AS SELECT
    toDate(event_ts)  AS day,
    classification,
    count()           AS cnt
FROM skywatch.ztf_alerts
GROUP BY day, classification;

-- Note: the MV sees only NEW inserts, so Kafka duplicates end up here as well.
-- Good enough for dashboard trends; for exact numbers query ztf_alerts with FINAL.
