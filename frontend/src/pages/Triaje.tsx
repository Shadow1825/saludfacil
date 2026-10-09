import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { listAppointments } from "../api/appointments";
import type { Cita } from "../api/appointments";
import { CLASIFICACION_LABEL, createTriaje, listTriajes, SINTOMAS_ALTA_CANONICOS } from "../api/triage";
import type { Severidad, Sintoma, Triage } from "../api/triage";

function puedeTriajarse(cita: Cita): boolean {
  return cita.estado === "reservada" && cita.fecha >= new Date().toISOString().slice(0, 10);
}

export function TriajePage(): JSX.Element {
  const [citas, setCitas] = useState<Cita[]>([]);
  const [historial, setHistorial] = useState<Triage[]>([]);
  const [citaId, setCitaId] = useState("");
  const [marcados, setMarcados] = useState<Record<string, boolean>>({});
  const [extras, setExtras] = useState<Sintoma[]>([{ nombre: "", severidad: "moderada" }]);
  const [resultado, setResultado] = useState<Triage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const misCitas = await listAppointments();
      setCitas(misCitas.filter(puedeTriajarse));
      setHistorial(await listTriajes());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los datos.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function toggleCanonico(nombre: string, activo: boolean): void {
    setMarcados((prev) => ({ ...prev, [nombre]: activo }));
    setResultado(null);
  }

  function updateExtra(index: number, campo: "nombre" | "severidad", valor: string): void {
    setExtras((prev) => prev.map((e, i) => (i === index ? { ...e, [campo]: valor } : e)));
    setResultado(null);
  }

  function addFila(): void {
    setExtras((prev) => [...prev, { nombre: "", severidad: "moderada" }]);
  }

  async function handleEnviar(): Promise<void> {
    setError(null);
    setResultado(null);
    const sintomas: Sintoma[] = [];
    SINTOMAS_ALTA_CANONICOS.forEach((s) => {
      if (marcados[s.nombre]) {
        sintomas.push({ nombre: s.nombre.toLowerCase(), severidad: "intensa" as Severidad });
      }
    });
    extras.forEach((e) => {
      const nombre = e.nombre.trim();
      if (nombre) {
        sintomas.push({ nombre, severidad: e.severidad });
      }
    });
    if (!citaId) {
      setError("Seleccione la cita para la que desea registrar el triaje.");
      return;
    }
    if (sintomas.length === 0) {
      setError("Debe registrar al menos un síntoma.");
      return;
    }
    setBusy(true);
    try {
      const triaje = await createTriaje(Number(citaId), sintomas);
      setResultado(triaje);
      setMarcados({});
      setExtras([{ nombre: "", severidad: "moderada" }]);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo registrar el triaje.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section aria-labelledby="titulo-triaje">
        <h2 id="titulo-triaje">Triaje inicial</h2>
        <p>
          Registre los síntomas que presenta y obtenga una clasificación inicial
          orientativa. Esta clasificación no constituye un diagnóstico médico.
        </p>
        {error && <p className="error" role="alert">{error}</p>}

        <form className="card" onSubmit={(e) => { e.preventDefault(); void handleEnviar(); }}>
          <div className="field">
            <label htmlFor="cita-triaje">Cita para el triaje</label>
            <select id="cita-triaje" value={citaId} onChange={(e) => { setCitaId(e.target.value); setResultado(null); }}>
              <option value="">Seleccione una cita reservada…</option>
              {citas.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.fecha} {c.hora_inicio} · {c.profesional}
                </option>
              ))}
            </select>
            {citas.length === 0 && <small>No tiene citas reservadas próximas para registar triaje.</small>}
          </div>

          <fieldset>
            <legend>Síntomas de severidad intensa (R1-R3)</legend>
            {SINTOMAS_ALTA_CANONICOS.map((s) => (
              <label key={s.nombre} className="row">
                <input
                  type="checkbox"
                  checked={marcados[s.nombre] ?? false}
                  onChange={(e) => toggleCanonico(s.nombre, e.target.checked)}
                />
                {s.descripcion}
              </label>
            ))}
          </fieldset>

          <fieldset>
            <legend>Otros síntomas (severidad moderada o leve)</legend>
            {extras.map((extra, index) => (
              <div className="row" key={index}>
                <input
                  type="text"
                  aria-label="Síntoma adicional"
                  placeholder="Ej.: fiebre, tos, cefalea"
                  value={extra.nombre}
                  onChange={(e) => updateExtra(index, "nombre", e.target.value)}
                />
                <select
                  aria-label="Severidad del síntoma"
                  value={extra.severidad}
                  onChange={(e) => updateExtra(index, "severidad", e.target.value as Severidad)}
                >
                  <option value="moderada">Moderada</option>
                  <option value="leve">Leve</option>
                </select>
              </div>
            ))}
            <button type="button" className="button button--small" onClick={addFila}>
              Agregar síntoma
            </button>
          </fieldset>

          <div className="form-actions">
            <button type="submit" className="button" disabled={busy}>
              {busy ? "Clasificando…" : "Obtener clasificación inicial"}
            </button>
          </div>
        </form>

        {resultado && (
          <div className="card notice" role="status">
            <h3>Resultado: {CLASIFICACION_LABEL[resultado.clasificacion]}</h3>
            <p>{resultado.mensaje}</p>
            <ul>
              {resultado.sintomas.map((s, i) => (
                <li key={i}>
                  {s.nombre} ({s.severidad})
                </li>
              ))}
            </ul>
          </div>
        )}

        <h3>Historial de triaje</h3>
        {historial.length === 0 ? (
          <p>Aún no ha registrado triajes.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Fecha</th>
                  <th scope="col">Profesional</th>
                  <th scope="col">Especialidad</th>
                  <th scope="col">Clasificación inicial</th>
                </tr>
              </thead>
              <tbody>
                {historial.map((t) => (
                  <tr key={t.id}>
                    <td>
                      {t.fecha} {t.hora_inicio}
                    </td>
                    <td>{t.profesional}</td>
                    <td>{t.specialty_name}</td>
                    <td>{t.resultado}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}