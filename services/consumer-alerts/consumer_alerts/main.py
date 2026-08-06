import asyncio
import json
import logging

import aiohttp
import aiokafka

from skywatch_common.envelope import unpack_envelope, unpack_ztf_alert
from skywatch_common.settings import settings


log = logging.getLogger('consumer-alerts')

INSERT_QUERY = f'INSERT INTO {settings.clickhouse_db}.ztf_alerts FORMAT JSONEachRow'
RETRY_DELAY_S = 5.0


def format_ts(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


def parse_message(msg) -> dict | Exception:
    try:
        env = unpack_envelope(msg.value)
        alert = unpack_ztf_alert(env['payload'])
    except Exception as e:
        return e
    alert['event_ts'] = format_ts(alert['event_ts'])
    alert['ingest_ts'] = format_ts(env['ingest_ts'])
    return alert


async def insert_batch(session, rows):
    body = '\n'.join(json.dumps(row) for row in rows)
    resp = await session.post(
        settings.clickhouse_url,
        params={'query': INSERT_QUERY},
        data=body.encode(),
        headers={
            'X-ClickHouse-User': settings.clickhouse_user,
            'X-ClickHouse-Key': settings.clickhouse_password,
        },
    )
    if resp.status != 200:
        error = f'ClickHouse error {resp.status}: {await resp.text()}'
        log.error(error)
        raise RuntimeError(error)


async def send_to_deadletter(producer, msg, error):
    log.warning(f'deadletter {msg.topic}[{msg.partition}]@{msg.offset}: {error!r}')
    try:
        await producer.send_and_wait(
            settings.topic_deadletter,
            value=msg.value,
            key=msg.key,
            headers=[
                ('error', repr(error).encode()),
                ('src_topic', msg.topic.encode()),
                ('src_partition', str(msg.partition).encode()),
                ('src_offset', str(msg.offset).encode()),
            ]
        )
    except Exception as e:
        log.error(f'send_to_deadletter failed, message lost: {e}')


async def run():
    producer = aiokafka.AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap)
    await producer.start()
    consumer = aiokafka.AIOKafkaConsumer(
        settings.topic_alerts,
        bootstrap_servers=settings.kafka_bootstrap,
        group_id=f'{settings.consumer_group}-test',
        auto_offset_reset='earliest',
        enable_auto_commit=False
    )
    await consumer.start()
    try:
        async with aiohttp.ClientSession() as session:
            while True:
                result = await consumer.getmany(
                    timeout_ms=int(settings.batch_timeout_s * 1000),
                    max_records=settings.batch_size
                )
                if not result:
                    continue
                rows = []
                for messages in result.values():
                    for msg in messages:
                        parsed = parse_message(msg)
                        if isinstance(parsed, dict):
                            rows.append(parsed)
                        else:
                            await send_to_deadletter(producer, msg, parsed)
                if rows:
                    while True:
                        try:
                            await insert_batch(session, rows)
                            break
                        except Exception as e:
                            log.error(f'insert failed, retry in {RETRY_DELAY_S}s: {e}')
                            await asyncio.sleep(RETRY_DELAY_S)
                await consumer.commit()
                log.info(f'inserted {len(rows)} rows')
    finally:
        await consumer.stop()
        await producer.stop()
