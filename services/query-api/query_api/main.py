from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query

from query_api import queries
from query_api.ch import ch


@asynccontextmanager
async def lifespan(app):
    await ch.start()
    yield
    await ch.stop()


app = FastAPI(title='SkyWatch Query API', lifespan=lifespan)


async def run_query(query, **params):
    if query is None:
        raise HTTPException(501, 'query not implemented yet')
    return await ch.select(query, **params)


@app.get('/api/stats/daily')
async def stats_daily(days: int = Query(30, ge=1, le=365)):
    return await run_query(queries.DAILY_STATS, days=days)


@app.get('/api/stats/classes')
async def stats_classes():
    return await run_query(queries.CLASS_COUNTS)


@app.get('/api/alerts/latest')
async def alerts_latest(
    limit: int = Query(50, ge=1, le=500),
    classification: str = '',
    date_from: date = date(1970, 1, 1),
    date_to: date = date(2149, 6, 6),
):
    return await run_query(
        queries.LATEST_ALERTS,
        limit=limit,
        cls=classification,
        date_from=date_from,
        date_to=date_to,
    )


@app.get('/api/objects/interesting')
async def objects_interesting(
    limit: int = Query(15, ge=1, le=100),
    min_events: int = Query(5, ge=1),
):
    return await run_query(
        queries.INTERESTING_OBJECTS,
        limit=limit,
        min_events=min_events,
    )


@app.get('/api/objects/{object_id}')
async def object_history(object_id: str):
    rows = await run_query(queries.OBJECT_HISTORY, object_id=object_id)
    if not rows:
        raise HTTPException(404, 'object not found')
    return rows
