#!/usr/bin/env python3
"""Experimental HTTPS/HTTP2 payload tunnel client.

This is request/response transport and does not replace vpn-ws L2 websocket tunnel.
"""

import argparse
import requests


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', required=True, help='https://server/potato_h2')
    p.add_argument('--client-id', default='client1')
    p.add_argument('--cafile', help='CA cert file for self-signed server cert')
    p.add_argument('--send', help='Text payload to send')
    p.add_argument('--recv', action='store_true')
    args = p.parse_args()

    headers = {'X-Client-Id': args.client_id}
    verify = args.cafile if args.cafile else True

    if args.send:
        r = requests.post(args.base + '/send', data=args.send.encode(), headers=headers, verify=verify)
        print(r.status_code, r.text)

    if args.recv:
        r = requests.get(args.base + '/recv', headers=headers, verify=verify)
        print(r.status_code, r.content.decode(errors='replace'))


if __name__ == '__main__':
    main()
