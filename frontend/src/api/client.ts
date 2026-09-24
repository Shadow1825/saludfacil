const API_BASE = "/api";

export interface HealthResponse {
  status: string;
  service: string;
  database: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`No se pudo conectar con el servidor (HTTP ${response.status})`);
  }
  return (await response.json()) as HealthResponse;
}