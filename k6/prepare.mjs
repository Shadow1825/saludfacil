import fs from "fs";
import path from "path";

const BASE = process.env.BASE ?? "http://localhost:8000/api";
const DIR = path.join(process.cwd(), "data");
fs.mkdirSync(DIR, { recursive: true });

async function req(method, ruta, body, token) {
  const res = await fetch(`${BASE}${ruta}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try {
    data = await res.json();
  } catch {}
  return { status: res.status, data };
}

function isoFecha(d) {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

const ADMIN = { email: "admin@saludfacil.com", password: "AdminSaludFacil!1" };
const Maria = 1;

async function main() {
  const login = await req("POST", "/auth/login", ADMIN);
  if (login.status !== 200) throw new Error(`login admin ${login.status}`);
  const token = login.data.access_token;

  for (const h of [
    { day: 3, start_time: "13:00", end_time: "17:00" },
    { day: 5, start_time: "08:00", end_time: "12:00" },
  ]) {
    const r = await req("POST", "/schedules", {
      professional_id: Maria,
      day: h.day,
      start_time: h.start_time,
      end_time: h.end_time,
    }, token);
    if (r.status !== 201 && r.status !== 409) {
      throw new Error(`horario ${JSON.stringify(h)} -> ${r.status}`);
    }
  }

  const slots = [];
  const d = new Date();
  for (let i = 1; i <= 180 && slots.length < 120; i += 1) {
    const candidato = new Date(d.getFullYear(), d.getMonth(), d.getDate() + i);
    if (![1, 3, 5].includes(candidato.getDay())) continue;
    const r = await req(
      "GET",
      `/directory/slots?professional_id=${Maria}&fecha=${isoFecha(candidato)}`,
      undefined,
      token,
    );
    if (r.status === 200) {
      for (const s of r.data) {
        slots.push({ fecha: isoFecha(candidato), hora: s.hora_inicio, professional_id: Maria });
      }
    }
  }
  if (slots.length < 100) {
    throw new Error(`Solo ${slots.length} slots disponibles para 50 VUs x 2 iteraciones.`);
  }
  fs.writeFileSync(path.join(DIR, "slots.json"), JSON.stringify(slots.slice(0, 110)), "utf8");

  const users = [];
  for (let i = 0; i < 50; i += 1) {
    const user = {
      first_name: "Carga",
      last_name: `VU${String(i).padStart(2, "0")}`,
      dni: String(30000000 + i).padStart(8, "0"),
      email: `k6carga${i}@test.com`,
      phone: "999000111",
      password: "K6ClaveSegura!1",
    };
    const r = await req("POST", "/auth/register", user);
    if (r.status !== 201 && r.status !== 409) {
      throw new Error(`registro k6carga${i} -> ${r.status}`);
    }
    users.push({ email: user.email, password: user.password });
  }
  fs.writeFileSync(path.join(DIR, "users.json"), JSON.stringify(users), "utf8");

  console.log(`Preparación K6 lista: ${slots.length} slots guardados, ${users.length} usuarios.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});