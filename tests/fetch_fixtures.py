"""Fetch real device data from the XiaoDu cloud and save it as test fixtures.

Run this on a machine that has network access. It reuses the integration's own
``XiaoDuAPI`` so the requests match exactly what the integration does.

Usage:
    XIAODU_COOKIE='your_bduss_cookie' python tests/fetch_fixtures.py

Output (written next to this file, under tests/fixtures/):
    homes.json                  -> {houseId: houseName}
    devices_<houseId>.json      -> raw appliance list for that house
                                   (each item has applianceTypes + friendlyName)
    detail_<applianceId>.json   -> full appliancedetails response per device

NOTE:
* The cookie is read only from the environment and is never written to disk.
* The saved JSON DOES contain your device names / appliance IDs / house names.
  Review before sharing publicly.
"""
import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path

import aiohttp

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"

# Load XiaoDuAPI by file path so we don't import the package __init__
# (which pulls in homeassistant and isn't needed for plain API calls).
_API_PATH = HERE.parent / "custom_components" / "xiaodu" / "api" / "XiaoDuAPI.py"
_spec = importlib.util.spec_from_file_location("xiaodu_api", _API_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
XiaoDuAPI = _mod.XiaoDuAPI


def _save(name: str, data) -> None:
    FIXTURES.mkdir(exist_ok=True)
    path = FIXTURES / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  saved {path.relative_to(HERE.parent)}")


async def main() -> int:
    cookie = os.environ.get("XIAODU_COOKIE")
    if not cookie:
        print("ERROR: set XIAODU_COOKIE env var with your BDUSS cookie.", file=sys.stderr)
        return 2

    # Force aiohttp's thread-based DNS resolver. The default async resolver
    # (aiodns) is broken on some installs (aiodns 3.2 vs pycares 5.x):
    # "Channel.getaddrinfo() takes 3 positional arguments but 4 were given".
    connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
    async with aiohttp.ClientSession(connector=connector) as session:
        api = XiaoDuAPI(cookie=cookie, session=session)

        ok, reason = await api.checkSession()
        if not ok:
            print(f"ERROR: cookie check failed: {reason}", file=sys.stderr)
            return 1

        homes = await api.get_home_id_list()
        if not homes:
            print("ERROR: no homes returned (cookie expired?).", file=sys.stderr)
            return 1
        _save("homes.json", homes)
        print(f"Found {len(homes)} home(s): {homes}")

        type_summary = []
        for house_id in homes:
            appliances = await api.get_device_wifi_id(house_id)
            _save(f"devices_{house_id}.json", appliances)
            print(f"House {house_id}: {len(appliances)} device(s)")

            for ap in appliances:
                aid = ap.get("applianceId")
                name = ap.get("friendlyName")
                types = ap.get("applianceTypes")
                type_summary.append((name, types))
                if not aid:
                    continue
                api.applianceId = aid
                api.houseId = house_id
                detail = await api.get_detail()
                _save(f"detail_{aid}.json", detail)

        print("\n=== 设备类型一览 (name -> applianceTypes) ===")
        for name, types in type_summary:
            print(f"  {name}: {types}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
