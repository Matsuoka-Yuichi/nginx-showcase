import time
import datetime
import socket
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify(
        service="cache-demo-backend",
        hostname=socket.gethostname(),
        timestamp=datetime.datetime.now().isoformat(),
    )


@app.route("/slow")
def slow():
    """Simulates a slow API call — takes 2 seconds to respond."""
    time.sleep(2)
    return jsonify(
        endpoint="slow",
        hostname=socket.gethostname(),
        timestamp=datetime.datetime.now().isoformat(),
        message="This response took 2 seconds to generate",
    )


@app.route("/fast")
def fast():
    return jsonify(
        endpoint="fast",
        hostname=socket.gethostname(),
        timestamp=datetime.datetime.now().isoformat(),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
