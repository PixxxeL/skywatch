# Built from the repo ROOT (see build.context in docker-compose.yml):
# this puts services/common and schemas, shared by all services, into the context.
FROM python:3.12-slim
WORKDIR /app
COPY services/connector-ztf/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/common ./services/common
COPY schemas ./schemas
RUN pip install --no-cache-dir ./services/common
ENV SKYWATCH_SCHEMAS_DIR=/app/schemas
COPY services/connector-ztf/connector_ztf ./connector_ztf
CMD ["python", "-m", "connector_ztf"]
