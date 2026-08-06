import logging

import aiokafka

from skywatch_common.settings import settings

from connector_ztf import fink, synthetic


log = logging.getLogger('connector-ztf')

SOURCES = {
    'synthetic': synthetic.run_source,
    'fink': fink.run_source,
}


async def run():
    if settings.source_mode not in SOURCES:
        raise SystemExit(
            f'unknown SOURCE_MODE={settings.source_mode!r}, '
            f'expected one of {sorted(SOURCES)}'
        )
    producer = aiokafka.AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap)
    await producer.start()
    log.info(f'started, source_mode={settings.source_mode}')
    try:
        await SOURCES[settings.source_mode](producer)
    finally:
        await producer.stop()
