"""Проверка доступности источников данных для SkyWatch — ДО начала разработки.

Запуск (обычный Python 3.10+, ничего ставить не нужно):
    python tools/check_sources.py

Проверяет три независимые вещи:
  1. REST API Fink       — жив ли конвейер обработки алертов ZTF (свежие данные?)
  2. Kafka-порт Fink     — достижим ли брокер живого потока из ТВОЕЙ сети
     (это ещё не значит, что пустят без кредов — но если порт закрыт/зафильтрован
      провайдером, узнаем сразу)
  3. Архив алертов ZTF   — доступен ли запасной вариант (replay без регистрации)

Ни одна проверка не требует регистрации.
"""

import json
import re
import socket
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

TIMEOUT = 15
OK, FAIL, WARN = "[ OK ]", "[FAIL]", "[WARN]"


def http_get(url: str, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "skywatch-check/0.1"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        return r.read()


def check_fink_api() -> bool:
    """Свежие алерты через публичный REST API Fink (без ключей)."""
    url = ("https://api.fink-portal.org/api/v1/latests"
           "?class=SN%20candidate&n=1&columns=i:objectId,v:lastdate")
    try:
        data = json.loads(http_get(url))
    except Exception as e:
        print(f"{FAIL} Fink REST API: {e}")
        return False
    if not data:
        print(f"{WARN} Fink REST API отвечает, но вернул пусто")
        return False
    last = data[0]
    lastdate = last.get("v:lastdate", "?")
    print(f"{OK} Fink REST API жив. Последний кандидат в сверхновые: "
          f"{last.get('i:objectId', '?')} от {lastdate}")
    # Свежесть: алерт младше 7 дней = поток точно идёт
    try:
        dt = datetime.fromisoformat(lastdate).replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).days
        if age_days > 7:
            print(f"{WARN} ...но последнему алерту {age_days} дн. — поток, возможно, стоит")
            return False
        print(f"{OK} Алерт свежий ({age_days} дн.) — конвейер ZTF→Fink работает")
    except ValueError:
        print(f"{WARN} Не смог разобрать дату '{lastdate}' — оцени свежесть глазами")
    return True


def check_fink_kafka_port() -> bool:
    """TCP-доступность Kafka-брокера Fink из текущей сети."""
    host, port = "kafka-ztf.fink-broker.org", 24499
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT):
            print(f"{OK} Kafka-брокер Fink достижим: {host}:{port} (TCP connect)")
            return True
    except OSError as e:
        print(f"{FAIL} Kafka-брокер Fink недоступен ({host}:{port}): {e}")
        print("       Возможные причины: фаервол/провайдер режет нестандартный порт,")
        print("       брокер переехал (сверься с доками fink-client), временный даун.")
        return False


def check_ztf_archive() -> bool:
    """Запасной вариант: публичные ночные архивы алертов (для режима replay)."""
    url = "https://ztf.uw.edu/alerts/public/"
    try:
        html = http_get(url).decode("utf-8", "replace")
    except Exception as e:
        print(f"{FAIL} Архив ZTF недоступен: {e}")
        return False
    dates = sorted(set(re.findall(r"ztf_public_(\d{8})\.tar\.gz", html)))
    if not dates:
        print(f"{WARN} Страница архива открылась, но файлов не видно (изменился формат?)")
        return False
    newest = dates[-1]
    print(f"{OK} Архив ZTF доступен. Всего ночей в списке: {len(dates)}, "
          f"свежайшая: {newest[:4]}-{newest[4:6]}-{newest[6:]}")
    age = (datetime.now(timezone.utc)
           - datetime.strptime(newest, "%Y%m%d").replace(tzinfo=timezone.utc)).days
    if age > 14:
        print(f"{WARN} Свежайший архив старше {age} дн. Для replay это не критично "
              f"(любая ночь подойдёт), но публикация, похоже, отстаёт/остановлена")
    return True


def main() -> int:
    print("=== SkyWatch: проверка источников данных ===\n")
    results = {
        "Fink REST API (конвейер жив)": check_fink_api(),
        "Fink Kafka (живой поток)": check_fink_kafka_port(),
        "Архив ZTF (запасной replay)": check_ztf_archive(),
    }
    print("\n=== Итог ===")
    for name, ok in results.items():
        print(f"  {'да' if ok else 'НЕТ':>3}  {name}")

    if results["Архив ZTF (запасной replay)"]:
        print("\nВывод: минимум один источник реальных данных есть — проект имеет смысл.")
    if results["Fink Kafka (живой поток)"]:
        print("Kafka-порт Fink доступен: можно подавать заявку на креды "
              "(форма — по ссылке в https://github.com/astrolabsoftware/fink-client"
              "/blob/master/docs/livestream_manual.md) "
              "и параллельно начинать с синтетики/реплея.")
    else:
        print("Живой поток пока под вопросом — начинаем с синтетики/реплея, "
              "это не блокирует ни один шаг плана.")
    return 0 if any(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
