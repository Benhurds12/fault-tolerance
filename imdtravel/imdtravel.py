from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/buyTicket', methods=['POST'])
def buy_ticket():
    data = request.json
    flight = data.get('flight')
    day = data.get('day')
    user = data.get('user')
    
    transaction_id = random.randint(1000, 9999)
    return jsonify(success=True, transaction_id=transaction_id), 200

@app.route('/flight', methods=['GET'])
def get_flight():
    flight = request.args.get('flight')
    day = request.args.get('day')
    return jsonify(flight=flight, day=day, value=random.uniform(100, 500)), 200

@app.route('/sell', methods=['POST'])
def sell_ticket():
    return jsonify(transaction_id=random.randint(1000, 9999)), 200

@app.route('/bonus', methods=['POST'])
def bonus():
    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)