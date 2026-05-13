import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { DashboardLoginCard } from "../components/DashboardLoginCard";
import { PageLayout } from "../components/PageLayout";
import { explorerOrder, explorerPedidosPorCliente } from "../lib/api";
import { formatApiErrorBody } from "../lib/errors";

export function ExplorerPage() {
  const { authorization, isLoggedIn } = useAuth();
  const [orderMode, setOrderMode] = useState<"id" | "codigo">("id");
  const [pedidoId, setPedidoId] = useState("");
  const [pedidoCodigo, setPedidoCodigo] = useState("");
  const [clienteId, setClienteId] = useState("");
  const [orderResult, setOrderResult] = useState("");
  const [clienteResult, setClienteResult] = useState("");
  const [orderErr, setOrderErr] = useState("");
  const [clienteErr, setClienteErr] = useState("");
  const [busyOrder, setBusyOrder] = useState(false);
  const [busyCliente, setBusyCliente] = useState(false);

  async function loadOrder() {
    if (!authorization) return;
    setOrderErr("");
    setOrderResult("");
    setBusyOrder(true);
    try {
      const params =
        orderMode === "id"
          ? { pedido_id: Number(pedidoId.trim()), pedido_codigo: undefined as string | undefined }
          : { pedido_id: undefined as number | undefined, pedido_codigo: pedidoCodigo.trim() };
      if (orderMode === "id" && (Number.isNaN(params.pedido_id) || pedidoId.trim() === "")) {
        setOrderErr("pedido_id must be a number.");
        return;
      }
      if (orderMode === "codigo" && !params.pedido_codigo) {
        setOrderErr("Enter a pedido_codigo.");
        return;
      }
      const data = await explorerOrder(authorization, params);
      setOrderResult(JSON.stringify(data, null, 2));
    } catch (err: unknown) {
      const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
      setOrderErr(formatApiErrorBody(body));
    } finally {
      setBusyOrder(false);
    }
  }

  async function loadCliente() {
    if (!authorization) return;
    setClienteErr("");
    setClienteResult("");
    setBusyCliente(true);
    try {
      const id = Number(clienteId.trim());
      if (Number.isNaN(id) || clienteId.trim() === "") {
        setClienteErr("cliente_id must be a number.");
        return;
      }
      const data = await explorerPedidosPorCliente(authorization, id);
      setClienteResult(JSON.stringify(data, null, 2));
    } catch (err: unknown) {
      const body = err && typeof err === "object" && "body" in err ? (err as { body: unknown }).body : null;
      setClienteErr(formatApiErrorBody(body));
    } finally {
      setBusyCliente(false);
    }
  }

  if (!isLoggedIn || !authorization) {
    return (
      <PageLayout title="Explorer" subtitle="Order graph and customer orders (authenticated).">
        <DashboardLoginCard title="Sign in to explorer" />
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Explorer" subtitle="Order lookup and pedidos por cliente (warehouse reads).">
      <div className="grid gap-8 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Order lookup</h2>
          <p className="mt-1 text-sm text-slate-600">Provide exactly one of pedido_id or pedido_codigo.</p>
          <div className="mt-4 flex gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="order-key"
                checked={orderMode === "id"}
                onChange={() => setOrderMode("id")}
              />
              pedido_id
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="order-key"
                checked={orderMode === "codigo"}
                onChange={() => setOrderMode("codigo")}
              />
              pedido_codigo
            </label>
          </div>
          {orderMode === "id" ? (
            <input
              className="mt-3 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-sm"
              placeholder="e.g. 1001"
              value={pedidoId}
              onChange={(e) => setPedidoId(e.target.value)}
            />
          ) : (
            <input
              className="mt-3 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-sm"
              placeholder="Order code"
              value={pedidoCodigo}
              onChange={(e) => setPedidoCodigo(e.target.value)}
            />
          )}
          <button
            type="button"
            disabled={busyOrder}
            className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            onClick={() => void loadOrder()}
          >
            {busyOrder ? "Loading…" : "Load order"}
          </button>
          {orderErr ? (
            <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-red-50 p-3 text-xs text-red-800">{orderErr}</pre>
          ) : null}
          {orderResult ? (
            <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-800">
              {orderResult}
            </pre>
          ) : null}
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Pedidos por cliente</h2>
          <p className="mt-1 text-sm text-slate-600">GET /api/explorer/pedidos-por-cliente?cliente_id=…</p>
          <input
            className="mt-4 w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-sm"
            placeholder="cliente_id"
            value={clienteId}
            onChange={(e) => setClienteId(e.target.value)}
          />
          <button
            type="button"
            disabled={busyCliente}
            className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            onClick={() => void loadCliente()}
          >
            {busyCliente ? "Loading…" : "Load pedidos"}
          </button>
          {clienteErr ? (
            <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-red-50 p-3 text-xs text-red-800">{clienteErr}</pre>
          ) : null}
          {clienteResult ? (
            <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-800">
              {clienteResult}
            </pre>
          ) : null}
        </section>
      </div>
    </PageLayout>
  );
}
