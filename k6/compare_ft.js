import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 40,
    duration: '25s',
};

export default function () {
    const url = 'http://localhost:5000/buyTicket';

    const ft_enabled = Math.random() > 0.5;

    const payload = JSON.stringify({
        flight: "AA123",
        day: "2025-10-30",
        user: "Bola",
        ft: ft_enabled,
    });

    const params = { headers: { 'Content-Type': 'application/json' } };

    const res = http.post(url, payload, params);

    check(res, {
        '200 when FT enabled': (r) => ft_enabled ? r.status === 200 : true,
        'failures happen when FT disabled': (r) => !ft_enabled ? (r.status === 200 || r.status === 504) : true,
    });

    sleep(1);
}
