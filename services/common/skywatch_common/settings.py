"""Настройки всех сервисов. Значения берутся из переменных окружения / .env
(pydantic-settings читает их сам). Один класс на всех — маленький проект,
дробить по сервисам пока незачем."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Kafka
    kafka_bootstrap: str = "localhost:29092"
    topic_alerts: str = "ingest.ztf.alerts"
    topic_deadletter: str = "ingest.deadletter"

    # ClickHouse (HTTP-интерфейс)
    clickhouse_url: str = "http://localhost:8123"
    clickhouse_db: str = "skywatch"
    clickhouse_user: str = "skywatch"
    clickhouse_password: str = "change-me"

    # connector-ztf
    source_mode: str = "synthetic"  # synthetic | replay | fink
    synthetic_rate: float = 5.0     # событий/сек
    data_dir: str = "./data/ztf"
    replay_rate: float = 50.0
    fink_username: str = ""
    fink_group_id: str = ""
    fink_servers: str = "kafka-ztf.fink-broker.org:24499"
    fink_topics: str = "fink_sso_ztf_candidates_ztf"

    # consumer-alerts
    consumer_group: str = "ch-writer"
    batch_size: int = 500
    batch_timeout_s: float = 2.0


settings = Settings()
