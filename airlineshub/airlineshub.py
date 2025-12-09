from flask import Flask, request, jsonify
import random
import time

app = Flask(__name__)

# Variável global para rastrear até quando o sistema está em "falha"
# Armazena o timestamp (tempo do relógio) de quando a falha deve acabar
failure_end_time = 0

@app.route('/flight', methods=['GET'])
def get_flight():
    # Mantive sua lógica original aqui para o flight
    if random.random() < 0.2:
        print("Simulated omission failure")
        return jsonify(error='Failure occurred: Omission'), 408
    else:    
        flight = request.args.get('flight')
        day = request.args.get('day')
        return jsonify(flight=flight, day=day, value=random.uniform(100, 500)), 200

@app.route('/sell', methods=['POST'])
def sell_ticket():
    global failure_end_time
    current_time = time.time()

    # 1. VERIFICAÇÃO DE ESTADO: O sistema já está quebrado?
    if current_time < failure_end_time:
        remaining = int(failure_end_time - current_time)
        print(f"--> [SISTEMA LENTO] Falha ativa. Restam {remaining}s. Aplicando delay de 5s...")
        
        time.sleep(5)  
        
        return jsonify({
            'Success': False,
            "Error": "Timeout Request 3 (Persistent Failure)"
        }), 504

    # 2. GATILHO: Se o sistema está saudável, vamos ver se ele quebra agora?
    # Probabilidade de 0.1 (10%)
    if random.random() < 0.1:
        print("--> [FALHA INICIADA] Ocorreu um azar! Sistema ficará lento por 10s.")
        
        # Define o futuro: O sistema ficará ruim até (Agora + 10 segundos)
        failure_end_time = current_time + 10
        
        time.sleep(5) 
        
        return jsonify({
            'Success': False,
            "Error": "Timeout Request 3 (New Failure Triggered)"
        }), 504

    # 3. CENÁRIO SAUDÁVEL
    return jsonify({
        'Success': True,
        'transaction_id': random.randint(1000, 9999)
    }), 200

if __name__ == '__main__':
    # Threaded=True é importante para simular requisições simultâneas sofrendo delay
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)