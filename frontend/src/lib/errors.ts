/** Human-readable message from FastAPI-style error bodies. */
export function formatApiErrorBody(body: unknown): string {
  if (body == null) return "Request failed.";
  if (typeof body === "string") return body;
  if (typeof body !== "object") return String(body);
  const o = body as Record<string, unknown>;
  if (typeof o.detail === "string") return o.detail;
  if (Array.isArray(o.detail)) {
    return o.detail
      .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: unknown }).msg) : JSON.stringify(d)))
      .join("; ");
  }
  if (o.detail && typeof o.detail === "object") {
    const d = o.detail as Record<string, unknown>;
    if (Array.isArray(d.validation_errors)) {
      return d.validation_errors.map((e) => JSON.stringify(e)).join("\n");
    }
    return JSON.stringify(o.detail, null, 2);
  }
  if (typeof o.message === "string") return o.message;
  return JSON.stringify(body, null, 2);
}
