# Built from the repo ROOT (see build.context in docker-compose.yml):
# this puts services/common and schemas, shared by all services, into the context.
FROM python:3.12-slim
WORKDIR /app
COPY services/consumer-alerts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/common ./services/common
COPY schemas ./schemas
RUN pip install --no-cache-dir ./services/common
ENV SKYWATCH_SCHEMAS_DIR=/app/schemas
COPY services/consumer-alerts/consumer_alerts ./consumer_alerts
CMD ["python", "-m", "consumer_alerts"]
