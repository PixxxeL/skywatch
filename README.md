# SkyWatch

Учебно-практический проект: приём астрономических событий (алерты ZTF через брокер Fink)
в Kafka, складирование и аналитика в ClickHouse, дашборд на Vue.

Цель — изучить Kafka и ClickHouse на живом потоке, но с расширяемой архитектурой:
новые источники (GCN, NOAA и др.) добавляются как отдельные коннекторы, ядро не меняется.
Подробности — в [ARCHITECTURE.md](ARCHITECTURE.md).

## Состав

| Компонент          | Что делает                                                   | Стек                  |
|--------------------|--------------------------------------------------------------|-----------------------|
| `deploy/`          | docker-compose: Kafka (KRaft), Kafka UI, ClickHouse, nginx   | Docker Compose        |
| `schemas/`         | Avro-схемы внутренних сообщений (конверт)                    | Avro                  |
| `services/common`  | Общий код: конверт, Avro-сериализация, настройки             | Python                |
| `services/connector-ztf` | Источник: Fink live / реплей архива / синтетика → Kafka | Python, aiokafka      |
| `services/consumer-alerts` | Kafka → батч-вставка в ClickHouse                     | Python, aiokafka      |
| `services/query-api` | REST API поверх ClickHouse для дашборда                     | Python, FastAPI       |
| `dashboard/`       | Дашборд: свежие алерты, кривые блеска, статистика            | Vue 3, TS, Pinia, SASS|

## Среда разработки (Windows 10 + VirtualBox)

Kafka и ClickHouse не работают нативно под Windows — они живут в одной VM:

1. VirtualBox → Ubuntu Server 24.04, 4+ GB RAM, 20+ GB диск.
   Сеть: адаптер 1 — NAT, в его «Дополнительно → Проброс портов» правила
   (адрес хоста `127.0.0.1`, адрес гостя пустой):
   `2222→22` (ssh), `29092→29092` (Kafka), `8123→8123` (ClickHouse), `8085→8085` (Kafka UI).
   Такая схема не зависит от VPN, роутера и смены сетей — всё ходит через localhost.
2. В VM: установить Docker (`curl -fsSL https://get.docker.com | sh`) и docker compose plugin.
3. Склонировать/скопировать в VM только каталог `deploy/` (например scp через `-P 2222`).
4. В `deploy/.env`: `KAFKA_EXTERNAL_HOST=127.0.0.1` (см. `.env.example`).
5. В VM: `cd deploy && docker compose -f docker-compose.dev.yml up -d`.
   Проверка: Kafka UI на `http://127.0.0.1:8085`, ClickHouse на `http://127.0.0.1:8123/play`.
6. Создать топики руками (в VM; это упражнение — разберись с каждым флагом):

   ```bash
   docker compose -f docker-compose.dev.yml exec kafka \
     /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create \
     --topic ingest.ztf.alerts --partitions 3 --config retention.ms=604800000

   docker compose -f docker-compose.dev.yml exec kafka \
     /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create \
     --topic ingest.deadletter --partitions 1 --config retention.ms=2592000000

   # посмотреть, что получилось:
   docker compose -f docker-compose.dev.yml exec kafka \
     /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe
   ```

   (в prod то же самое делает контейнер kafka-init скриптом `kafka/create-topics.sh`)

7. Накатить схему ClickHouse руками. Рекомендуемый способ — интерактивный клиент:

   ```bash
   docker compose -f docker-compose.dev.yml exec clickhouse \
     clickhouse-client --user skywatch --password <из .env>
   ```

   и выполнить стейтменты из `clickhouse/init/01_schema.sql` по одному, читая
   комментарии (CREATE DATABASE → таблицы → материализованное вью), потом
   `SHOW TABLES FROM skywatch`. Одной командой (если лень):

   ```bash
   docker compose -f docker-compose.dev.yml exec -T clickhouse \
     clickhouse-client --user skywatch --password <из .env> --multiquery \
     < clickhouse/init/01_schema.sql
   ```

   (в prod схема накатывается автоматически при первом старте контейнера)

Python-сервисы и дашборд запускаются на Windows-хосте и ходят в VM через проброшенные порты.
SSH в машину: `ssh -p 2222 user@127.0.0.1`.

### Запуск сервисов на хосте

```bat
:: один venv на все сервисы
python -m venv .venv
.venv\Scripts\activate
pip install -e services\common -r services\connector-ztf\requirements.txt ^
    -r services\consumer-alerts\requirements.txt -r services\query-api\requirements.txt

copy .env.example .env   :: и поправить KAFKA_* / CLICKHOUSE_* под IP твоей VM

:: терминал 1 — источник (для старта синтетика, Fink не нужен)
python -m connector_ztf

:: терминал 2 — консьюмер в ClickHouse
python -m consumer_alerts

:: терминал 3 — API
uvicorn query_api.main:app --reload --port 8000
```

Дашборд:

```bat
cd dashboard
npm install
npm run dev   :: http://localhost:5173, проксирует /api на localhost:8000
```

### Режимы коннектора (`SOURCE_MODE` в `.env`)

- `synthetic` — генерирует правдоподобные алерты (по умолчанию; ничего не нужно).
- `replay` — читает Avro-файлы алертов ZTF из `DATA_DIR` и проигрывает с заданной скоростью.
  Ночные архивы: https://ztf.uw.edu/alerts/public/
- `fink` — живой поток от брокера Fink. Нужна бесплатная регистрация: форма по ссылке в
  https://github.com/astrolabsoftware/fink-client/blob/master/docs/livestream_manual.md
  (доки: https://doc.ztf.fink-broker.org). Креды — в `.env` (`FINK_*`).

## Прод (VDS, Ubuntu)

Тот же compose, профиль prod: приложения в контейнерах, а nginx — системный, на хосте
(так проще certbot и это общий reverse proxy для всего на сервере).

```bash
cd deploy
cp .env.example .env       # заполнить прод-значения
docker compose -f docker-compose.prod.yml up -d --build

# nginx хоста:
sudo cp nginx/skywatch.conf /etc/nginx/sites-available/skywatch
sudo ln -s /etc/nginx/sites-available/skywatch /etc/nginx/sites-enabled/
# дашборд: npm run build и выложить dist/ в /var/www/skywatch
sudo nginx -t && sudo systemctl reload nginx
# TLS: sudo certbot --nginx -d <домен>
```

Наружу открыты только 80/443 (nginx); query-api опубликован на 127.0.0.1:8000 хоста,
Kafka и ClickHouse — только внутри docker-сети.

## Чему тут учиться (чек-лист)

- [ ] Партиции и ключи: алерты одного объекта попадают в одну партицию (ключ = objectId)
- [ ] Consumer groups: второй консьюмер на том же топике (например, алертер) — fan-out
- [ ] Оффсеты: ручной коммит после успешной вставки (at-least-once), реплей с `--from-beginning`
- [ ] Отставание (lag): нагнать поток после остановки консьюмера, посмотреть lag в Kafka UI
- [ ] DLQ: битые сообщения уходят в `ingest.deadletter`
- [ ] Avro: эволюция схемы конверта (добавить поле, не сломав старых консьюмеров)
- [ ] ClickHouse: батч-вставки, ReplacingMergeTree и дедупликация, партиции по месяцам
- [ ] Материализованные вью: дневная статистика считается на вставке
- [ ] Новый источник: добавить connector-gcn по гайду в ARCHITECTURE.md

## License

MIT — see [LICENSE](LICENSE).

---

Built with the help of AI (Anthropic Claude): architecture discussions, code review
and parts of the implementation. All design decisions were made and verified by a human.
