import asyncio
import json
import logging
import random
import time

from skywatch_common.settings import settings
from skywatch_common.envelope import (
    Envelope,
    pack_envelope,
    pack_ztf_alert,
)


log = logging.getLogger('connector-ztf.synthetic')
LOOP_LOG_RATE = 50
MSG_ID_MAX = 15


def make_item():
    num = random.randint(1, MSG_ID_MAX)
    object_id = f'ZTF26test00{num}'
    ts = int(time.time() * 1000)
    item = {
        'object_id': object_id,
        'candidate_id': random.randint(10**9, 10**10),
        'event_ts': ts,
        'ra': random.uniform(0, 360),
        'dec': random.uniform(-90, 90),
        'magpsf': random.uniform(15, 21),
        'sigmapsf': random.uniform(0.01, 0.3),
        'fid': random.choice([1, 2]),
        'classification': random.choice(['SN candidate', 'Solar System', 'unknown']),
    }
    item['raw'] = json.dumps(item)
    return item


async def run_source(producer):
    count = 0
    while 1:
        value = make_item()
        payload = pack_ztf_alert(value)
        env = Envelope(
            source='ztf',
            event_type='alert',
            event_id=str(value['candidate_id']),
            event_ts=value['event_ts'],
            schema_version=1,
            payload=payload
        )
        await producer.send_and_wait(
            settings.topic_alerts,
            value=pack_envelope(env),
            key=value['object_id'].encode()
        )
        if not count % LOOP_LOG_RATE:
            log.info(f'sent {count}')
        count += 1
        await asyncio.sleep(1 / settings.synthetic_rate)
