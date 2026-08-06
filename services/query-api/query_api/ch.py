import aiohttp

from skywatch_common.settings import settings


class ClickHouseError(Exception):
    pass


class ClickHouse:
    def __init__(self):
        self._session = None

    async def start(self):
        self._session = aiohttp.ClientSession()

    async def stop(self):
        await self._session.close()

    async def select(self, query, **params):
        request_params = {
            'query': f'{query} FORMAT JSON',
            'database': settings.clickhouse_db,
        }
        for name, value in params.items():
            request_params[f'param_{name}'] = str(value)
        resp = await self._session.post(
            settings.clickhouse_url,
            params=request_params,
            headers={
                'X-ClickHouse-User': settings.clickhouse_user,
                'X-ClickHouse-Key': settings.clickhouse_password,
            },
        )
        if resp.status != 200:
            raise ClickHouseError(await resp.text())
        payload = await resp.json()
        return payload['data']


ch = ClickHouse()
