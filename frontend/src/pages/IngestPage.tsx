import { useMemo, useState } from "react";
import { INGEST_ENTITIES } from "../data/entities";
import { PageLayout } from "../components/PageLayout";
import { ingestEntity } from "../lib/api";
import { formatApiErrorBody } from "../lib/errors";

export function IngestPage() {
  const [entityId, setEntityId] = useState(INGEST_ENTITIES[0]?.id ?? "");
  const entity = useMemo(() => INGEST_ENTITIES.find((e) => e.id === entityId), [entityId]);
  const [values, setValues] = useState<Record<string, string>>(() => {
    const e = INGEST_ENTITIES[0];
    const o: Record<string, string> = {};
    e?.fields.forEach((f) => {
      o[f] = "";
    });
    return o;
  });

  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string>("");
  const [error, setError] = useState<string>("");

  function selectEntity(id: string) {
    setEntityId(id);
    const e = INGEST_ENTITIES.find((x) => x.id === id);
    const o: Record<string, string> = {};
    e?.fields.forEach((f) => {
      o[f] = "";
    });
    setValues(o);
    setResult("");
    setError("");
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!entity) return;
    setBusy(true);
    setError("");
    setResult("");
    const payload: Record<string, string> = {};
    for (const f of entity.fields) {
      payload[f] = (values[f] ?? "").trim();
    }
    try {
      const data = await ingestEntity(entity.id, payload);
      setResult(JSON.stringify(data, null, 2));
    } catch (err: unknown) {
      const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
      setError(formatApiErrorBody(body));
    } finally {
      setBusy(false);
    }
  }

  return (
    <PageLayout
      title="Manual ingestion"
      subtitle="POST JSON to the ingest API for each commerce entity (no dashboard login required)."
    >
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">Entity</label>
          <select
            className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
            value={entityId}
            onChange={(e) => selectEntity(e.target.value)}
          >
            {INGEST_ENTITIES.map((en) => (
              <option key={en.id} value={en.id}>
                {en.label}
              </option>
            ))}
          </select>
          {entity ? (
            <form className="mt-6 space-y-3" onSubmit={(e) => void submit(e)}>
              {entity.fields.map((field) => (
                <div key={field}>
                  <label className="block text-xs font-medium text-slate-500">{field}</label>
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-sm outline-none ring-slate-400 focus:ring-2"
                    value={values[field] ?? ""}
                    onChange={(e) => setValues((v) => ({ ...v, [field]: e.target.value }))}
                  />
                </div>
              ))}
              <button
                type="submit"
                disabled={busy}
                className="mt-2 w-full rounded-lg bg-emerald-700 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
              >
                {busy ? "Submitting…" : "Submit record"}
              </button>
            </form>
          ) : null}
        </div>
        <div className="space-y-4">
          {error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4">
              <p className="text-sm font-medium text-red-900">Error</p>
              <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap font-mono text-xs text-red-800">
                {error}
              </pre>
            </div>
          ) : null}
          {result ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-slate-900">Response</p>
              <pre className="mt-2 max-h-[32rem] overflow-auto whitespace-pre-wrap font-mono text-xs text-slate-700">
                {result}
              </pre>
            </div>
          ) : null}
        </div>
      </div>
    </PageLayout>
  );
}
