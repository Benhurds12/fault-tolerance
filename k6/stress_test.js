import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '5s', target: 20 },
        { duration: '5s', target: 200 },
        { duration: '5s', target: 400 },
        { duration: '10s', target: 0 },
    ],
};

export default function () {
    const url = 'http://localhost:5000/buyTicket';

    const payload = JSON.stringify({
        flight: "AA123",
        day: "2025-10-30",
        user: "Bola",
        ft: true,
    });

    const params = { headers: { 'Content-Type': 'application/json' } };

    const res = http.post(url, payload, params);

    check(res, {
        'status is 200 or FT working': (r) => r.status === 200 || r.status === 504,
    });

    sleep(0.5);
}
