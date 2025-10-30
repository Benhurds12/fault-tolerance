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
        flight_data = requests.get('http://airlineshub:5001/flight', params={'flight': flight, 'day': day}).json()
        exchange_rate = requests.get('http://exchange:5002/convert').json()['rate']
        transaction_id = requests.post('http://airlineshub:5001/sell', params={'flight': flight, 'day': day}).json()['transaction_id']
        bonus = requests.post('http://fidelity:5003/bonus', json={'user': user, 'amount': round(flight_data['value'])}).json()['success']

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

    # Enviar junto com a requisição para debug
    debug = {
        'flight_data': flight_data,
        'exchange_rate': exchange_rate,
        'transaction_id': transaction_id,
        'bonus_credited': bonus
    }

    return jsonify(success=True, transaction_id=transaction_id), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)