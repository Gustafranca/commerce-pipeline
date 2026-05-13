export type ApiErrorBody = {
  detail?: unknown;
  message?: string;
};

async function parseJsonSafe(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export async function apiFetch(
  path: string,
  init: RequestInit & { auth?: string | null } = {},
): Promise<Response> {
  const { auth, headers: h, ...rest } = init;
  const headers = new Headers(h);
  if (auth) headers.set("Authorization", auth);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  return fetch(path, { ...rest, headers });
}

export async function apiJson<T>(
  path: string,
  init: RequestInit & { auth?: string | null } = {},
): Promise<T> {
  const res = await apiFetch(path, init);
  const body = (await parseJsonSafe(res)) as T;
  if (!res.ok) {
    const err = new Error(`HTTP ${res.status}`) as Error & { status: number; body: unknown };
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

/** GET /api/records — list staged records (filter by entity in the UI; API returns up to `limit`). */
export function fetchStagedRecords(auth: string, params?: { limit?: number }): Promise<unknown> {
  const q = new URLSearchParams();
  q.set("limit", String(params?.limit ?? 500));
  return apiJson(`/api/records?${q.toString()}`, { auth });
}

export function patchStagedRecord(
  auth: string,
  recordId: number,
  body: { payload: unknown; entity_name?: string | null },
): Promise<unknown> {
  return apiJson(`/api/records/${encodeURIComponent(String(recordId))}`, {
    method: "PATCH",
    auth,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function deleteStagedRecord(auth: string, recordId: number): Promise<unknown> {
  return apiJson(`/api/records/${encodeURIComponent(String(recordId))}`, {
    method: "DELETE",
    auth,
  });
}

/** One POST per staged row id (backend: POST /api/records/{record_id}/promote). */
export async function promoteStagedRecord(auth: string, recordId: number): Promise<unknown> {
  return apiJson(`/api/records/${encodeURIComponent(String(recordId))}/promote`, {
    method: "POST",
    auth,
  });
}

export function ingestEntity(entity: string, payload: unknown): Promise<unknown> {
  return apiJson(`/ingest/${encodeURIComponent(entity)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function browseTable(
  auth: string,
  entity: string,
  params?: { limit?: number; offset?: number },
): Promise<unknown> {
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  const base = `/api/browse/${encodeURIComponent(entity)}`;
  return apiJson(qs ? `${base}?${qs}` : base, { auth });
}

export function deleteBrowseRow(
  auth: string,
  entity: string,
  id: string | number,
): Promise<unknown> {
  return apiJson(`/api/browse/${encodeURIComponent(entity)}/${encodeURIComponent(String(id))}`, {
    method: "DELETE",
    auth,
  });
}

export function explorerOrder(
  auth: string,
  params: { pedido_id?: number; pedido_codigo?: string },
): Promise<unknown> {
  const q = new URLSearchParams();
  if (params.pedido_id != null) q.set("pedido_id", String(params.pedido_id));
  if (params.pedido_codigo != null && params.pedido_codigo !== "")
    q.set("pedido_codigo", params.pedido_codigo);
  return apiJson(`/api/explorer/order?${q.toString()}`, { auth });
}

export function explorerPedidosPorCliente(auth: string, clienteId: number): Promise<unknown> {
  return apiJson(`/api/explorer/pedidos-por-cliente?cliente_id=${encodeURIComponent(String(clienteId))}`, {
    auth,
  });
}
