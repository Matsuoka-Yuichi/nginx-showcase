import os
import datetime
import socket
from flask import Flask, jsonify

app = Flask(__name__)

INSTANCE_ID = os.environ.get("INSTANCE_ID", "default")


@app.route("/")
def index():
    return jsonify(
        instance=INSTANCE_ID,
        hostname=socket.gethostname(),
        timestamp=datetime.datetime.now().isoformat(),
    )


@app.route("/health")
def health():
    return jsonify(status="ok", instance=INSTANCE_ID)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
