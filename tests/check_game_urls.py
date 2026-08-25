"""Upstream reachability check for every entry in data/games.json (frontend-only static catalog)."""
import json
import concurrent.futures as cf

import requests

GAMES = json.load(open("/app/frontend/public/data/games.json"))


def check(g):
    url = g["src"]
    try:
        r = requests.get(url, timeout=25, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        body = next(r.iter_content(4096), b"") or b""
        txt = body.decode("utf-8", "ignore").lower()
        dead = "couldn't find the requested file" in txt or "couldn&#39;t find the requested file" in txt
        r.close()
        return g["name"], url, r.status_code, dead
    except Exception as e:
        return g["name"], url, "ERR:" + type(e).__name__, True


bad = []
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    for name, url, code, dead in ex.map(check, GAMES):
        if code != 200 or dead:
            bad.append((name, url, code, dead))

print(f"total={len(GAMES)} bad={len(bad)}")
for b in bad:
    print(b)
