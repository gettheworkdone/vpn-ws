#!/usr/bin/env python3
"""Long-poll helper for Lollipop GUI HTTPS2 mode."""

from __future__ import annotations

import argparse
import time
import requests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--cafile")
    ap.add_argument("--interval", type=float, default=0.8)
    args = ap.parse_args()

    verify = args.cafile if args.cafile else True
    headers = {"X-Client-Id": args.client_id}

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
