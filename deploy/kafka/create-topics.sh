#!/bin/bash
# Явное создание топиков (auto-create выключен, чтобы опечатка в имени топика
# не порождала молча новый пустой топик — частая прод-практика).
set -e
BS=kafka:9092
KT=/opt/kafka/bin/kafka-topics.sh   # путь в официальном образе apache/kafka
create() {
  $KT --bootstrap-server $BS --create --if-not-exists \
    --topic "$1" --partitions "$2" --replication-factor 1 \
    --config retention.ms="$3"
}

# Основной поток алертов ZTF.
#   3 партиции — чтобы было что распараллеливать и на чём увидеть работу ключей;
#   retention 7 дней — как у Fink: неделю можно "отматывать" и переигрывать.
create ingest.ztf.alerts 3 604800000

# Dead letter queue: битые сообщения. Храним месяц, партиция одна — поток мизерный.
create ingest.deadletter 1 2592000000

echo "Topics:"
$KT --bootstrap-server $BS --list
