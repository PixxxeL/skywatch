# Собирается из КОРНЯ репо (см. build.context в docker-compose.yml):
# так в контекст попадают services/common и schemas, общие для всех сервисов.
FROM python:3.12-slim
WORKDIR /app
COPY services/connector-ztf/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/common ./services/common
COPY schemas ./schemas
RUN pip install --no-cache-dir ./services/common
COPY services/connector-ztf/connector_ztf ./connector_ztf
CMD ["python", "-m", "connector_ztf"]
