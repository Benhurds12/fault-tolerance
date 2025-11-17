from time import time
from flask import Flask, request, jsonify
import random
import requests
from collections import deque
app = Flask(__name__)

DEFAULT_RATE = 5.5
successful_rates = deque([DEFAULT_RATE] * 10, maxlen=10)

@app.route('/buyTicket', methods=['POST'])
def buy_ticket():
    ft = True
    data = request.json
    flight = data.get('flight')
    day = data.get('day')
    user = data.get('user')
    ft = data.get('ft', True)
    flight_data = None
    exchange_rate = None
    transaction_id = None
    sell_json = None
    bonus = None
    
    # 1. Definir o número de tentativas com base no flag 'ft'
    # Se ft=True, tenta 3 vezes. Se ft=False, tenta 1 vez (fail-fast).
    MAX_RETRIES_FLIGHT = 3 if ft else 1 
    
    is_flight_failure = False

    for attempt in range(MAX_RETRIES_FLIGHT):
        try:
            flight_resp = requests.get(
                'http://airlineshub:5001/flight',
                params={'flight': flight, 'day': day},
                timeout=2 
            )
            flight_resp.raise_for_status() 
            
            flight_data = flight_resp.json()
            
            # SUCESSO!
            print(f"Tentativa {attempt + 1}/{MAX_RETRIES_FLIGHT}: Sucesso ao obter voo.")
            is_flight_failure = False
            break 

        except requests.exceptions.RequestException as e:
            print(f"Tentativa {attempt + 1}/{MAX_RETRIES_FLIGHT} falhou para /flight: {e}")
            is_flight_failure = True
            
            # 2. Só aplicar o backoff se houver mais tentativas
            if attempt < MAX_RETRIES_FLIGHT - 1:
                print("Aplicando backoff e tentando novamente...")
                time.sleep(0.5 * (attempt + 1)) 
    
    # --- Verifica o resultado das tentativas do Voo ---
    if is_flight_failure:
        # 3. Ajustar a mensagem de erro
        if MAX_RETRIES_FLIGHT > 1:
            error_message = 'Serviço /flight indisponível após múltiplas tentativas.'
        else:
            error_message = 'Serviço /flight indisponível (ft=False, sem retentativas).'
        
        return jsonify(success=False, error=error_message), 504

    exchange_rate = None
    is_exchange_failure = False
    try:
        exchange_resp = requests.get('http://exchange:5002/convert', timeout=2)
        exchange_resp.raise_for_status() 
        rate_data = exchange_resp.json()
        proposed_rate = rate_data.get('rate')

        if proposed_rate is None or proposed_rate < 0:
            print("Falha de lógica: Serviço de câmbio retornou taxa inválida.")
            is_exchange_failure = True
        else:
            exchange_rate = proposed_rate
            successful_rates.append(exchange_rate)
            print(f"Taxa de câmbio obtida com sucesso: {exchange_rate}")

    except requests.exceptions.RequestException as e:
        print(f"Falha de rede: Serviço de câmbio falhou: {e}")
        is_exchange_failure = True
    
    if is_exchange_failure:
        if ft:
            avg_rate = sum(successful_rates) / len(successful_rates)
            exchange_rate = avg_rate
            print(f"TOLERÂNCIA A FALHAS ATIVADA: Usando taxa média: {exchange_rate}")
        else:
            return jsonify(success=False, error='Serviço de câmbio falhou e tolerância a falhas está desligada'), 504

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

    # Enviar junto com a requisição para debug
    debug = {
        'flight_data': flight_data,
        'sell_response': sell_json,
        'exchange_rate': exchange_rate,
        'transaction_id': transaction_id,
        'bonus_credited': bonus,
        'fault_tolerance_applied': (is_exchange_failure and ft)
    }

    return jsonify(success=True, transaction_id=transaction_id, debug=debug), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)