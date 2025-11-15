from flask import Flask, request, jsonify
import random
import requests

app = Flask(__name__)

@app.route('/buyTicket', methods=['POST'])
def buy_ticket():
    data = request.json
    flight = data.get('flight')
    day = data.get('day')
    user = data.get('user')
    
    try:
        flight_resp = requests.get('http://airlineshub:5001/flight', params={'flight': flight, 'day': day}, timeout=2)
        flight_resp.raise_for_status()
        flight_data = flight_resp.json()

        exchange_resp = requests.get('http://exchange:5002/convert', timeout=2)
        exchange_resp.raise_for_status()
        exchange_rate = exchange_resp.json().get('rate')

        try:
            sell_response = requests.post(
                'http://airlineshub:5001/sell',
                params={'flight': flight, 'day': day},
                timeout=2
            )
        except requests.exceptions.Timeout:
            return jsonify(success=False, error='AirlinesHub took more than 2 seconds (Request 3)'), 504

        sell_response.raise_for_status()
        sell_json = sell_response.json()

        if not sell_json.get('Success', False):
            return jsonify(success=False, error='Error during ticket selling (Request 3)', details=sell_json), 504

        transaction_id = sell_json.get('transaction_id')

        bonus_resp = requests.post('http://fidelity:5003/bonus', json={'user': user, 'amount': round(flight_data.get('value', 0))}, timeout=2)
        bonus_resp.raise_for_status()
        bonus = bonus_resp.json().get('success')
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500
    
    # Enviar junto com a requisição para debug
    debug = {
        'flight_data': flight_data,
        'sell_response': sell_json,
        'exchange_rate': exchange_rate,
        'transaction_id': transaction_id,
        'bonus_credited': bonus
    }

    return jsonify(success=True, transaction_id=transaction_id, debug=debug), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)