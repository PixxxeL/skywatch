# SkyWatch — архитектура

## Общая схема

```
внешние источники                      SkyWatch
─────────────────                      ────────────────────────────────────────────
Fink (Kafka, Avro)  ──► connector-ztf ──► Kafka: ingest.ztf.alerts ─┬─► consumer-alerts ──► ClickHouse
GCN (Kafka)  [позже]──► connector-gcn ──► Kafka: ingest.gcn.notices ┘        (group: ch-writer)
NOAA (HTTP)  [позже]──► connector-noaa ─► Kafka: ingest.noaa.spaceweather
                                          Kafka: ingest.deadletter ◄── битые сообщения

ClickHouse ──► query-api (FastAPI) ──► dashboard (Vue) ── nginx (prod)
```

Принцип: **коннектор** отвечает за общение с внешним миром и нормализацию,
**внутренняя Kafka** — единая шина, **консьюмеры** ничего не знают об источниках.

## Конвенции

### Топики

`ingest.<source>.<type>` — например `ingest.ztf.alerts`. Партиций: 3 (учебно; в проде считается
от пропускной способности). Ключ сообщения — стабильный ID сущности (для ZTF — `objectId`),
чтобы события одного объекта шли в одну партицию и сохраняли порядок.

### Конверт (envelope)

Все внутренние сообщения — Avro по схеме [schemas/envelope.avsc](schemas/envelope.avsc):

| Поле            | Тип    | Смысл                                            |
|-----------------|--------|--------------------------------------------------|
| `source`        | string | `ztf`, `gcn`, ...                                |
| `event_type`    | string | `alert`, `notice`, ...                           |
| `event_id`      | string | уникальный ID события у источника                |
| `event_ts`      | long   | время события (timestamp-millis, UTC)            |
| `ingest_ts`     | long   | время приёма коннектором                         |
| `schema_version`| int    | версия схемы payload                             |
| `payload`       | bytes  | нормализованное тело события (Avro своей схемы)  |

Payload для ZTF — [schemas/ztf_alert_lite.avsc](schemas/ztf_alert_lite.avsc): выжимка из полного
алерта ZTF (~60 полей и вырезки изображений нам не нужны). Схемы лежат файлами в репо и
подключаются к сервисам через `services/common`; Schema Registry сознательно не используем
(меньше движущихся частей; конверт несёт `schema_version`).

### Гарантии доставки

At-least-once: консьюмер коммитит оффсеты **после** успешной вставки батча в ClickHouse.
Дубликаты гасятся на стороне ClickHouse: `ReplacingMergeTree` по `(object_id, candidate_id)`
+ `FINAL`/`GROUP BY` в запросах, где важна точность.

Сообщение, которое не удалось распарсить, уходит в `ingest.deadletter` с заголовками
`error`, `origin_topic` — и коммитится (не блокирует поток).

## ClickHouse

База `skywatch`, DDL: [deploy/clickhouse/init/01_schema.sql](deploy/clickhouse/init/01_schema.sql).

- `ztf_alerts` — ReplacingMergeTree, `PARTITION BY toYYYYMM(event_ts)`,
  `ORDER BY (object_id, candidate_id)`. Сырой алерт хранится в `raw` (ZSTD) — можно
  перепарсить историю при изменении схемы.
- `alerts_daily` — SummingMergeTree + материализованное вью: счётчики по дням/классификациям
  считаются в момент вставки.

## Сервисы

- **connector-ztf** — единственный сервис, знающий про Fink. Три режима источника
  (fink / replay / synthetic) за общим интерфейсом `AlertSource` — Fink-режим можно
  включить позже, не меняя остального кода.
- **consumer-alerts** — батчер: копит до `BATCH_SIZE` сообщений или `BATCH_TIMEOUT_S` секунд,
  вставляет одним INSERT, коммитит оффсеты.
- **query-api** — тонкий слой SQL→JSON. Никакой бизнес-логики, только параметризованные запросы.

## Как добавить новый источник (например GCN)

1. Скопировать `services/connector-ztf` → `services/connector-gcn`, реализовать свой `Source`
   (для GCN — консьюмер `gcn-kafka`; для HTTP-источников — поллер).
2. Описать payload-схему в `schemas/gcn_notice.avsc`, завернуть в тот же конверт.
3. Добавить топик `ingest.gcn.notices` в `deploy/kafka/create-topics.sh`.
4. Таблица + (при необходимости) MV в `deploy/clickhouse/init/`.
5. Консьюмер: либо новый маленький сервис, либо подписка consumer-alerts на второй топик
   с диспетчеризацией по `source` из конверта.
6. Сервис в compose (профиль prod), эндпоинт в query-api, вкладка в дашборде.

## Решения и их причины (кратко)

- **Своя Kafka между источником и потребителями**, а не прямое чтение Fink всеми:
  развязка, свой retention/реплей, единый формат — и это главный учебный паттерн.
- **Avro без Registry**: индустриальный формат, но минимум инфраструктуры. Registry — понятный
  следующий шаг, место для него в компоузе очевидно.
- **aiokafka**, а не confluent-kafka: чистый Python + asyncio, проще ставится на Windows;
  confluent-kafka (librdkafka) останется для connector-gcn — заодно сравнишь два клиента.
- **Два compose-файла** (`docker-compose.dev.yml` — только инфраструктура, код на хосте;
  `docker-compose.prod.yml` — инфраструктура + приложения): каждый читается целиком,
  без профилей и оверрайдов. VM в VirtualBox — репетиция VDS.
