# SkyWatch

Ingestion of astronomical events (ZTF alerts via the Fink broker), storage and analytics, dashboard.

New sources (GCN, NOAA, etc.) are added as separate connectors without touching the core.
See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Components

| Component          | What it does                                                 | Stack                 |
|--------------------|--------------------------------------------------------------|-----------------------|
| `deploy/`          | docker-compose: Kafka (KRaft), Kafka UI, ClickHouse, nginx   | Docker Compose        |
| `schemas/`         | Avro schemas of internal messages (envelope)                 | Avro                  |
| `services/common`  | Shared code: envelope, Avro serialization, settings          | Python                |
| `services/connector-ztf` | Source: Fink live / archive replay / synthetic → Kafka | Python, aiokafka      |
| `services/consumer-alerts` | Kafka → batch inserts into ClickHouse                 | Python, aiokafka      |
| `services/query-api` | REST API on top of ClickHouse for the dashboard             | Python, FastAPI       |
| `services/dashboard` | Dashboard: latest alerts, light curves, statistics          | Vue 3, TS, Pinia, SASS|

## License

MIT — see [LICENSE](LICENSE).

---

Built with the help of AI (Anthropic Claude): architecture discussions, code review
and parts of the implementation. All design decisions were made and verified by a human.
