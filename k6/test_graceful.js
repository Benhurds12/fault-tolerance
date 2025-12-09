import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

// Métricas Personalizadas para o Relatório
const failureTime = new Trend('failure_duration'); // Tempo que levou para falhar
const successTime = new Trend('success_duration'); // Tempo que levou para dar certo

const FT_ENABLED = __ENV.FT === 'false' ? false : true;

export const options = {
    // Vamos rodar carga suficiente para acionar os 10% de falha
    stages: [
        { duration: '10s', target: 20 },
        { duration: '30s', target: 20 }, 
        { duration: '10s', target: 0 },
    ],
    thresholds: {
        // O teste passa se 95% das falhas forem rápidas (apenas se FT=true)
        // Se FT=false, esperamos que isso aqui falhe ou seja alto
        'failure_duration': ['p(95) < 2200'], 
    },
};

export default function () {
    const url = 'http://localhost:5000/buyTicket';

    const payload = JSON.stringify({
        flight: "AA123",
        day: "2025-10-30",
        user: "Tester_Latency",
        ft: FT_ENABLED,
    });

    const params = { 
        headers: { 'Content-Type': 'application/json' },
        timeout: '15s' // Timeout do K6 deve ser maior que o pior cenário do servidor
    };

    const res = http.post(url, payload, params);

    // Lógica de Separação de Métricas
    if (res.status === 200) {
        successTime.add(res.timings.duration);
        check(res, { 'Success 200': (r) => r.status === 200 });
    } 
    else {
        // Aqui está o ouro: Medimos quanto tempo demorou para dar erro
        failureTime.add(res.timings.duration);
        
        check(res, {
            'Graceful Failure (< 2.2s)': (r) => r.timings.duration < 2200,
            'Sluggish Failure (> 4.8s)': (r) => r.timings.duration > 4800,
        });
    }

    sleep(1);
}