"""Data source availability check for SkyWatch — run BEFORE starting development.

Usage (plain Python 3.10+, nothing to install):
    python tools/check_sources.py

Checks three independent things:
  1. Fink REST API       — is the ZTF alert processing pipeline alive (fresh data?)
  2. Fink Kafka port     — is the live-stream broker reachable from YOUR network
     (does not mean you get in without credentials — but if the port is blocked
      or filtered by the ISP, we learn it right away)
  3. ZTF alert archive   — is the fallback available (replay without registration)

None of the checks require registration.
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
    """Fresh alerts via the public Fink REST API (no keys needed)."""
    url = ("https://api.fink-portal.org/api/v1/latests"
           "?class=SN%20candidate&n=1&columns=i:objectId,v:lastdate")
    try:
        data = json.loads(http_get(url))
    except Exception as e:
        print(f"{FAIL} Fink REST API: {e}")
        return False
    if not data:
        print(f"{WARN} Fink REST API responds but returned nothing")
        return False
    last = data[0]
    lastdate = last.get("v:lastdate", "?")
    print(f"{OK} Fink REST API is alive. Latest supernova candidate: "
          f"{last.get('i:objectId', '?')} from {lastdate}")
    # Freshness: an alert younger than 7 days = the stream is definitely flowing
    try:
        dt = datetime.fromisoformat(lastdate).replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).days
        if age_days > 7:
            print(f"{WARN} ...but the latest alert is {age_days} days old — the stream may be stalled")
            return False
        print(f"{OK} The alert is fresh ({age_days} d) — the ZTF→Fink pipeline works")
    except ValueError:
        print(f"{WARN} Could not parse date '{lastdate}' — judge the freshness yourself")
    return True


def check_fink_kafka_port() -> bool:
    """TCP reachability of the Fink Kafka broker from the current network."""
    host, port = "kafka-ztf.fink-broker.org", 24499
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT):
            print(f"{OK} Fink Kafka broker is reachable: {host}:{port} (TCP connect)")
            return True
    except OSError as e:
        print(f"{FAIL} Fink Kafka broker is unreachable ({host}:{port}): {e}")
        print("       Possible reasons: a firewall/ISP blocks the non-standard port,")
        print("       the broker moved (check the fink-client docs), temporary outage.")
        return False


def check_ztf_archive() -> bool:
    """Fallback: public nightly alert archives (for the replay mode)."""
    url = "https://ztf.uw.edu/alerts/public/"
    try:
        html = http_get(url).decode("utf-8", "replace")
    except Exception as e:
        print(f"{FAIL} ZTF archive is unavailable: {e}")
        return False
    dates = sorted(set(re.findall(r"ztf_public_(\d{8})\.tar\.gz", html)))
    if not dates:
        print(f"{WARN} The archive page opened but no files are listed (format changed?)")
        return False
    newest = dates[-1]
    print(f"{OK} ZTF archive is available. Nights listed: {len(dates)}, "
          f"newest: {newest[:4]}-{newest[4:6]}-{newest[6:]}")
    age = (datetime.now(timezone.utc)
           - datetime.strptime(newest, "%Y%m%d").replace(tzinfo=timezone.utc)).days
    if age > 14:
        print(f"{WARN} The newest archive is over {age} days old. Not critical for replay "
              f"(any night will do), but publication seems delayed/stopped")
    return True


def main() -> int:
    print("=== SkyWatch: data source check ===\n")
    results = {
        "Fink REST API (pipeline alive)": check_fink_api(),
        "Fink Kafka (live stream)": check_fink_kafka_port(),
        "ZTF archive (replay fallback)": check_ztf_archive(),
    }
    print("\n=== Summary ===")
    for name, ok in results.items():
        print(f"  {'yes' if ok else 'NO':>3}  {name}")

    if results["ZTF archive (replay fallback)"]:
        print("\nConclusion: at least one source of real data exists — the project makes sense.")
    if results["Fink Kafka (live stream)"]:
        print("The Fink Kafka port is reachable: you can apply for credentials "
              "(the form is linked from https://github.com/astrolabsoftware/fink-client"
              "/blob/master/docs/livestream_manual.md) "
              "and start with synthetic/replay in the meantime.")
    else:
        print("The live stream is uncertain for now — start with synthetic/replay, "
              "it does not block anything.")
    return 0 if any(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
