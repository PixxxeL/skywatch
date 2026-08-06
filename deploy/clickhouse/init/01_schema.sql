-- Выполняется автоматически при первом старте контейнера ClickHouse.
-- Термины (MergeTree, ORDER BY, партиции, MV) — в docs/BASICS.md, часть 2.

CREATE DATABASE IF NOT EXISTS skywatch;

-- Основная таблица алертов.
-- ReplacingMergeTree(ingest_ts): строки с одинаковым (object_id, candidate_id)
-- при фоновом слиянии схлопнутся в одну (останется свежайшая по ingest_ts) —
-- так гасим дубли от at-least-once доставки из Kafka.
CREATE TABLE IF NOT EXISTS skywatch.ztf_alerts
(
    object_id       String,                       -- ID объекта у ZTF, напр. ZTF26aaabbbc
    candidate_id    UInt64,                       -- уникальный ID конкретного измерения
    event_ts        DateTime64(3, 'UTC'),         -- время наблюдения
    ingest_ts       DateTime64(3, 'UTC'),         -- время приёма нашим коннектором
    ra              Float64,                      -- прямое восхождение, град
    dec             Float64,                      -- склонение, град
    magpsf          Float32,                      -- звёздная величина (яркость; меньше = ярче)
    sigmapsf        Float32,                      -- её погрешность
    fid             UInt8,                        -- фильтр: 1=g (зелёный), 2=r (красный), 3=i
    classification  LowCardinality(String),       -- класс от Fink: SN candidate, Solar System...
    class_score     Float32,                      -- уверенность классификатора 0..1
    raw             String CODEC(ZSTD(3))         -- исходное событие (JSON) на случай перепарсинга
)
ENGINE = ReplacingMergeTree(ingest_ts)
PARTITION BY toYYYYMM(event_ts)
ORDER BY (object_id, candidate_id);

-- Агрегаты по дням: наполняются автоматически материализованным вью при каждой вставке.
-- SummingMergeTree складывает cnt у строк с одинаковым ключом при слияниях.
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

-- Примечание: MV видит только НОВЫЕ вставки, дубли Kafka сюда тоже попадут.
-- Для учебного дашборда это ок; точные цифры — запросом с FINAL по ztf_alerts.
