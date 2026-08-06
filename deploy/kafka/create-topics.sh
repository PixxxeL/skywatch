#!/bin/bash
# Explicit topic creation (auto-create is disabled so that a typo in a topic
# name does not silently spawn a new empty topic — a common production practice).
set -e
BS=kafka:9092
KT=/opt/kafka/bin/kafka-topics.sh   # path inside the official apache/kafka image
create() {
  $KT --bootstrap-server $BS --create --if-not-exists \
    --topic "$1" --partitions "$2" --replication-factor 1 \
    --config retention.ms="$3"
}

# Main ZTF alert stream.
#   3 partitions — enough parallelism at this scale;
#   retention 7 days — same as Fink: a week of history to rewind and replay.
create ingest.ztf.alerts 3 604800000

# Dead letter queue: malformed messages. Kept for a month; one partition — the stream is tiny.
create ingest.deadletter 1 2592000000

echo "Topics:"
$KT --bootstrap-server $BS --list
