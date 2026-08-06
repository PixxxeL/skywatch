# Собирается из КОРНЯ репо (см. build.context в docker-compose.yml):
# так в контекст попадают services/common и schemas, общие для всех сервисов.
FROM python:3.12-slim
WORKDIR /app
COPY services/consumer-alerts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/common ./services/common
COPY schemas ./schemas
RUN pip install --no-cache-dir ./services/common
COPY services/consumer-alerts/consumer_alerts ./consumer_alerts
CMD ["python", "-m", "consumer_alerts"]
