/**
 * Decisio Snake Web API Client
 * Clean typed wrappers for interacting with the backend SnakeSession endpoints.
 */

export async function fetchStatus() {
  const res = await fetch("/api/status", { cache: "no-store" });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to fetch status: ${res.status} ${errorText}`);
  }
  return res.json();
}

export async function postStep() {
  const started = performance.now();
  const res = await fetch("/api/step", {
    method: "POST",
    cache: "no-store",
  });
  const clientRoundtripMs = performance.now() - started;

  if (!res.ok) {
    let message = `Step request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.error) message = body.error;
    } catch {
      // Ignore JSON parse errors
    }
    const error = new Error(message);
    error.status = res.status;
    throw error;
  }

  const data = await res.json();
  data.client_roundtrip_ms = clientRoundtripMs;
  return data;
}

export async function postReset() {
  const res = await fetch("/api/reset", {
    method: "POST",
    cache: "no-store",
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Reset failed: ${res.status} ${errorText}`);
  }
  return res.json();
}
