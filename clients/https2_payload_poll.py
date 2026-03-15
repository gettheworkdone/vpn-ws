#!/usr/bin/env python3
"""Long-poll helper for Lollipop GUI HTTPS2 mode."""

from __future__ import annotations

import argparse
import json
import time
import requests


def load_headers(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, dict):
        raise ValueError("headers json must be an object")
    return {str(k): str(v) for k, v in data.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--cafile")
    ap.add_argument("--headers-json")
    ap.add_argument("--interval", type=float, default=0.8)
    args = ap.parse_args()

    verify = args.cafile if args.cafile else True
    headers = {"X-Client-Id": args.client_id}
    headers.update(load_headers(args.headers_json))

    while True:
        try:
            resp = requests.get(args.base + "/recv", headers=headers, verify=verify, timeout=10)
            if resp.status_code == 200 and resp.content:
                print(resp.content.decode(errors="replace"), flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[h2-loop] error: {exc}", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
