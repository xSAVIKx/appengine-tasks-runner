import os
import time
from random import randint
from time import sleep

from flask import Flask, request

app = Flask(__name__)


def _sleep_timeout_seconds() -> int:
    request_payload = request.get_json()
    if isinstance(request_payload, dict):
        try:
            return int(request_payload.get("sleepTimeoutSeconds"))
        except:
            pass
    return randint(1, 100)


@app.route("/")
def waiting_workload():
    """An example workload that is capable of waiting."""
    start_time = time.time()
    sleep_timeout = _sleep_timeout_seconds()
    print(f"Sleeping for {sleep_timeout} seconds.")
    sleep(sleep_timeout)
    request_time = time.time() - start_time
    print(f"Request processed in {request_time} seconds.")
    return dict(status="OK", request_time=request_time), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
