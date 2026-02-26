from flask import Flask, request, jsonify, Response
from collections import defaultdict, deque

app = Flask(__name__)
QUEUES = defaultdict(deque)


def client_id():
    return request.headers.get("X-Client-Id", "default")


@app.post('/send')
def send_data():
    cid = client_id()
    payload = request.get_data() or b''
    if payload:
        QUEUES[cid].append(payload)
    return jsonify({"queued": len(payload)})


@app.get('/recv')
def recv_data():
    cid = client_id()
    if QUEUES[cid]:
        payload = QUEUES[cid].popleft()
        return Response(payload, mimetype='application/octet-stream')
    return Response(b'', mimetype='application/octet-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18080)
