import threading
from time import time, sleep
from flask import Flask, request, jsonify
import random
import requests
from collections import deque
import logging
import os

app = Flask(__name__)

# Configuração do logging para aparecer imediatamente no Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Configurações Globais ---
DEFAULT_RATE = 5.5
successful_rates = deque([DEFAULT_RATE] * 10, maxlen=10)

# Locks para garantir Thread Safety
log_lock = threading.Lock()   # Protege o arquivo log.txt
rates_lock = threading.Lock() # Protege a lista de taxas de câmbio

# --- Worker (Store and Forward) ---
def background_retry_worker():
    """
    Roda em background. Verifica o log a cada 5 segundos para reprocessar falhas.
    """
    while True:
        sleep(5) 
        
        # Verifica se arquivo existe e não está vazio
        if not os.path.exists("log.txt") or os.path.getsize("log.txt") == 0:
            continue

        logging.info("--- WORKER ACORDOU: Encontrou falhas pendentes no log! ---")

        pending_lines = []
        with log_lock:
            try:
                with open("log.txt", "r") as file:
                    pending_lines = file.readlines()
            except Exception as e:
                logging.error(f"Worker: Erro de leitura: {e}")
                continue
        
        if not pending_lines:
            continue

        lines_to_keep = []
        processed_count = 0
        
        logging.info(f"--- Processando fila com {len(pending_lines)} itens ---")

        for line in pending_lines:
            try:
                user_id, amount_str = line.strip().split()
                amount = float(amount_str)
                bonus_data = {'user': user_id, 'amount': round(amount)}
                
                # Tenta enviar novamente para o Fidelity
                bonus_response = requests.post('http://fidelity:5003/bonus', json=bonus_data, timeout=2)
                bonus_response.raise_for_status()
                
                logging.info(f"Worker: SUCESSO! Recuperado envio para {user_id} [OK]")
                processed_count += 1
                
            except Exception:
                # Se falhar novamente, mantém na lista para a próxima tentativa
                lines_to_keep.append(line)

        # Atualiza o arquivo de log
        if processed_count > 0:
            with log_lock:
                with open("log.txt", "w") as file:
                    file.writelines(lines_to_keep)
            logging.info(f"--- WORKER FINALIZOU CICLO: {processed_count} recuperados. {len(lines_to_keep)} ainda pendentes. ---")
        else:
            logging.info(f"--- WORKER FALHOU: O serviço Fidelity continua fora do ar. Tentará novamente em 5s. ---")

# Inicia o worker assim que o app arranca
retry_thread = threading.Thread(target=background_retry_worker, daemon=True)
retry_thread.start()


# --- Rotas da Aplicação ---
@app.route('/buyTicket', methods=['POST'])
def buy_ticket():
    # Parse dos dados
    data = request.json
    flight = data.get('flight')
    day = data.get('day')
    user = data.get('user')
    ft = data.get('ft', True) # Default: True (Com tolerância a falhas)
    
    # Variáveis de resposta/debug
    flight_data = None
    exchange_rate = None
    transaction_id = None
    sell_json = None
    bonus_status = "Not Attempted"
    is_exchange_failure = False

    # ---------------------------------------------------------
    # 1. Compra de Voo (Com Retry)
    # ---------------------------------------------------------
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
            is_flight_failure = False
            break # Sucesso, sai do loop
        except requests.exceptions.RequestException as e:
            logging.warning(f"Tentativa {attempt + 1} falhou para voo: {e}")
            is_flight_failure = True
            if attempt < MAX_RETRIES_FLIGHT - 1:
                sleep(0.5 * (attempt + 1)) # Backoff simples
    
    if is_flight_failure:
        error_msg = 'Serviço /flight indisponível.'
        return jsonify(success=False, error=error_msg), 504

    flight_value = flight_data.get('value', 1000)

    # ---------------------------------------------------------
    # 2. Câmbio (Com Sliding Window Cache + Lock)
    # ---------------------------------------------------------
    try:
        exchange_resp = requests.get('http://exchange:5002/convert', timeout=2)
        exchange_resp.raise_for_status() 
        rate_data = exchange_resp.json()
        exchange_rate = rate_data.get('rate')
        
        # Protege a escrita na memória compartilhada
        with rates_lock:
            successful_rates.append(exchange_rate)
            
    except requests.exceptions.RequestException:
        is_exchange_failure = True
    
    if is_exchange_failure:
        if ft:
            # Protege a leitura da memória compartilhada para o cálculo
            with rates_lock:
                if successful_rates:
                    exchange_rate = sum(successful_rates) / len(successful_rates)
                else:
                    exchange_rate = DEFAULT_RATE
            
            logging.warning(f"Câmbio falhou. Usando taxa média segura: {exchange_rate}")
        else:
            return jsonify(success=False, error='Câmbio falhou e FT desligada'), 504

    # ---------------------------------------------------------
    # 3. Venda (Com Fail Fast para Latência)
    # ---------------------------------------------------------
    
    # timeout dinâmico para permitir testes de comparação
    # FT ON: 2s (Fail Fast - aborta se lento)
    # FT OFF: 15s (Permissivo - sofre com a lentidão de 5s do serviço)
    request_timeout = 2 if ft else 15

    try:
        sell_response = requests.post(
            'http://airlineshub:5001/sell',
            params={'flight': flight, 'day': day},
            timeout=request_timeout
        )
        sell_response.raise_for_status()
        sell_json = sell_response.json()

    except requests.exceptions.Timeout:
        # Se cair aqui e FT=True, o Fail Fast funcionou (abortou em 2s)
        if ft:
            logging.error("Timeout Fail-Fast (>2s) acionado no AirlinesHub.")
            return jsonify(success=False, error='Timeout Fail-Fast (>2s)'), 504
        else:
            # Se FT=False e cair aqui, significa que demorou mais que 15s (improvável no teste)
            raise

    except requests.exceptions.RequestException:
        # Outros erros de conexão
        if ft:
            return jsonify(success=False, error='Erro de conexão no AirlinesHub /sell'), 504
        raise

    if not sell_json.get('Success', False):
         return jsonify(success=False, error='Erro na venda (Recusado)', details=sell_json), 504
    
    transaction_id = sell_json.get('transaction_id')

    # ---------------------------------------------------------
    # 4. Bonificação (Com Store and Forward)
    # ---------------------------------------------------------
    message = ""
    try:
        bonus_resp = requests.post(
            'http://fidelity:5003/bonus', 
            json={'user': user, 'amount': flight_value}, 
            timeout=2
        )
        bonus_resp.raise_for_status()
        message = "Operação realizada com sucesso total."
        bonus_status = "Credited (Online)"
        
    except requests.exceptions.RequestException:
        if ft:
            logging.warning(f"Fidelity indisponível. Salvando {user} no log para processamento posterior.")
            
            with log_lock:
                with open("log.txt", "a") as log_file:
                    log_file.write(f"{user} {flight_value}\n")
            
            message = "Operação realizada. Bonificação salva no log (Store & Forward)."
            bonus_status = "Queued in Log (Offline)"
        else:
            message = "Operação realizada, mas bonificação falhou (FT=False)."
            bonus_status = "Failed (FT Disabled)"

    # Dados para Debug e Validação no K6
    debug = {
        'flight_data': flight_data,
        'exchange_rate': exchange_rate,
        'bonus_status': bonus_status,
        'fault_tolerance_triggered': (bonus_status == "Queued in Log (Offline)")
    }

    return jsonify(success=True, message=message, debug=debug), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)