# Built from the repo ROOT (see build.context in docker-compose.yml).
FROM python:3.12-slim
WORKDIR /app
COPY services/query-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/common ./services/common
COPY schemas ./schemas
RUN pip install --no-cache-dir ./services/common
COPY services/query-api/query_api ./query_api
CMD ["uvicorn", "query_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
