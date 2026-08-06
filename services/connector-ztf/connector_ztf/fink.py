import asyncio
import json
import logging

from fink_client.consumer import AlertConsumer

from skywatch_common.settings import settings
from skywatch_common.envelope import (
    Envelope,
    pack_envelope,
    pack_ztf_alert,
)


log = logging.getLogger('connector-ztf.fink')

POLL_TIMEOUT_S = 5
LOOP_LOG_RATE = 50
JD_UNIX_EPOCH = 2440587.5
SCORE_FIELDS = ('snn_sn_vs_all', 'snn_snia_vs_nonia', 'rf_snia_vs_nonia')


def jd_to_millis(jd):
    return int((jd - JD_UNIX_EPOCH) * 86400 * 1000)


def topic_to_classification(topic):
    return topic.removeprefix('fink_').removesuffix('_ztf')


def get_class_score(alert):
    for key in SCORE_FIELDS:
        value = alert.get(key)
        if value is not None:
            return float(value)
    return 0.0


def make_item(topic, alert):
    candidate = alert['candidate']
    raw = {k: v for k, v in alert.items() if not k.startswith('cutout')}
    return {
        'object_id': alert['objectId'],
        'candidate_id': alert['candid'],
        'event_ts': jd_to_millis(candidate['jd']),
        'ra': candidate['ra'],
        'dec': candidate['dec'],
        'magpsf': candidate['magpsf'],
        'sigmapsf': candidate['sigmapsf'],
        'fid': candidate['fid'],
        'classification': topic_to_classification(topic),
        'class_score': get_class_score(alert),
        'raw': json.dumps(raw, default=str),
    }


async def run_source(producer):
    config = {
        'bootstrap.servers': settings.fink_servers,
        'group.id': settings.fink_group_id,
    }
    topics = [t.strip() for t in settings.fink_topics.split(',')]
    consumer = AlertConsumer(topics, config, 'ztf')
    log.info(f'subscribed to {topics}')
    count = 0
    try:
        while True:
            topic, alert, _ = await asyncio.to_thread(
                consumer.poll, POLL_TIMEOUT_S
            )
            if alert is None:
                continue
            item = make_item(topic, alert)
            env = Envelope(
                source='ztf',
                event_type='alert',
                event_id=str(item['candidate_id']),
                event_ts=item['event_ts'],
                schema_version=1,
                payload=pack_ztf_alert(item),
            )
            await producer.send_and_wait(
                settings.topic_alerts,
                value=pack_envelope(env),
                key=item['object_id'].encode(),
            )
            count += 1
            if not count % LOOP_LOG_RATE:
                log.info(f'sent {count}')
    finally:
        consumer.close()
