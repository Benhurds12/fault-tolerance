from flask import Flask, jsonify
import time
import random

app = Flask(__name__)
timer_start = None


@app.route('/convert', methods=['GET'])
def convert_currency():
    if simulate_failure(0.1):
        print("Simulated response failure")
        conversion_rate = random.uniform(-6, -5)
    else:
        conversion_rate = random.uniform(5, 6)
    return jsonify(rate=conversion_rate), 200

def simulate_failure(probability):
    global timer_start

    if random.random() < probability:
        if timer_start is None:
            timer_start = time.time()  

    if timer_start is not None:
        if time.time() - timer_start <= 5: 
            return True
        else:
            timer_start = None  

    return False

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)