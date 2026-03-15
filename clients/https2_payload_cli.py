#!/usr/bin/env python3
"""HTTPS2 payload CLI for Lollipop."""

import argparse
import json
import requests


def load_headers(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, dict):
        raise ValueError("headers json must be an object")
    return {str(k): str(v) for k, v in data.items()}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, help="https://server/potato_h2")
    p.add_argument("--client-id", default="client1")
    p.add_argument("--cafile", help="CA cert file for self-signed server cert")
    p.add_argument("--headers-json", help="path to headers json")
    p.add_argument("--send", help="Text payload to send")
    p.add_argument("--recv", action="store_true")
    args = p.parse_args()

    headers = {"X-Client-Id": args.client_id}
    headers.update(load_headers(args.headers_json))
    verify = args.cafile if args.cafile else True

    if args.send:
        r = requests.post(args.base + "/send", data=args.send.encode(), headers=headers, verify=verify)
        print(r.status_code, r.text)

    if args.recv:
        r = requests.get(args.base + "/recv", headers=headers, verify=verify)
        print(r.status_code, r.content.decode(errors="replace"))


if __name__ == "__main__":
    main()
