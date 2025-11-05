from flask import Flask, request, jsonify
import random
import os
import signal
app = Flask(__name__)

@app.route('/bonus', methods=['POST'])
def bonus():
    if simulate_failure(0.02):
         return os.kill(os.getpid(), signal.SIGINT)
    return jsonify(success=True), 200

def simulate_failure(probability):
    return random.random() < probability

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)