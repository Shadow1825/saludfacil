import http from "k6/http";
import { check, sleep } from "k6";
import { SharedArray } from "k6/data";

const BASE = __ENV.BASE ?? "http://localhost:8000/api";

const slots = new SharedArray("slots", () => JSON.parse(open("./data/slots.json")));
const users = new SharedArray("users", () => JSON.parse(open("./data/users.json")));

export const options = {
  scenarios: {
    carga: {
      executor: "per-vu-iterations",
      vus: 50,
      iterations: 2,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<2000"],
    "http_req_duration{name:login}": ["p(95)<2000"],
    "http_req_duration{name:horarios}": ["p(95)<2000"],
    "http_req_duration{name:reserva}": ["p(95)<2000"],
  },
};

const VUS = 50;

const tokens = {};

export default function () {
  const user = users[__VU - 1];
  let token = tokens[__VU - 1];

  if (!token) {
    sleep(__VU * 0.15);
    const login = http.post(
      `${BASE}/auth/login`,
      JSON.stringify({ email: user.email, password: user.password }),
      { headers: { "Content-Type": "application/json" }, tags: { name: "login" } },
    );
    check(login, { "login 200": (r) => r.status === 200 });
    token = login.json("access_token");
    tokens[__VU - 1] = token;
  }

  const auth = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const idx = (__VU - 1 + __ITER * VUS) % slots.length;
  const slot = slots[idx];

  const horarios = http.get(
    `${BASE}/directory/slots?professional_id=${slot.professional_id}&fecha=${slot.fecha}`,
    { headers: { Authorization: `Bearer ${token}` }, tags: { name: "horarios" } },
  );
  check(horarios, { "horarios 200": (r) => r.status === 200 });

  const reserva = http.post(
    `${BASE}/appointments`,
    JSON.stringify({ professional_id: slot.professional_id, fecha: slot.fecha, hora_inicio: slot.hora }),
    { headers: auth, tags: { name: "reserva" } },
  );
  check(reserva, { "reserva 201": (r) => r.status === 201 });

  sleep(0.2);
}