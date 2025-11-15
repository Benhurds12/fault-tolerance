from flask import Flask, request, jsonify
import random, time
app = Flask(__name__)

@app.route('/flight', methods=['GET'])
def get_flight():
    if simulate_failure(0.2):
        print("Simulated omission failure")
        return jsonify(error='Failure occurred: Omission'), 408
    else:    
        flight = request.args.get('flight')
        day = request.args.get('day')
        return jsonify(flight=flight, day=day, value=random.uniform(100, 500)), 200

@app.route('/sell', methods=['POST'])
def sell_ticket():
    #Tempo
    if simulate_failure(0.1):
        print("Simulated TIME/DELAY failure on Request 3 (/sell)")
        time.sleep(5)  # simulando timeout
        return jsonify({
            'Success': False,
            "Error": "Timeout Request 3"
        }), 504
    else:
        return jsonify({
            'Success': True,
            'transaction_id': random.randint(1000, 9999)
        }), 200

def simulate_failure(probability):
    return random.random() < probability
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)