# Reaching the app on a cluster (staging)

Kubernetes `ClusterIP` services are not browser-open by default. Pick **one** stable approach for your environment.

## Option A — Real DNS + Ingress (recommended for shared staging)

1. Point `app.staging.example.com` (and `airflow.staging.example.com`) at your ingress controller external IP or load balancer.
2. Update ingress host rules in `k8s/base/ingress/ingress.yaml` via a Kustomize patch in `k8s/overlays/staging/` (or use your real domain in overlay patches).
3. Optional: install **cert-manager** for TLS.

## Option B — `nip.io` / `sslip.io` without editing `/etc/hosts`

If your ingress has a stable IP (for example `192.168.49.2` from Minikube):

- Some setups support `http://app.192.168.49.2.nip.io` resolving to that IP (verify with `dig`).

**sslip.io** pattern (replace dots with dashes in the IP octets):

```text
http://app.192-168-49-2.sslip.io
```

Use that hostname in an ingress patch for staging so browsers resolve it without `/etc/hosts`.

## Option C — Minikube Docker driver on Linux (common dev fallback)

The Minikube **VM IP** often does **not** accept `:80` directly from the host. Use either:

### C1 — `minikube tunnel` (gives services a routable IP)

In a dedicated terminal:

```bash
minikube tunnel
```

Then use the `EXTERNAL-IP` shown on `ingress-nginx-controller` service (or your ingress) in the browser.

### C2 — `minikube service` tunnel (temporary local URL)

```bash
minikube service ingress-nginx-controller -n ingress-nginx --url
```

Keep that terminal open. Curl or browse using the printed `http://127.0.0.1:PORT` with:

```bash
curl -H "Host: app.pipeline-commerce.local" http://127.0.0.1:<PORT>/health
```

## What not to rely on for daily development

Use **Docker Compose** for UI/API iteration ([docs/local-dev.md](local-dev.md)). Use the cluster only when you intentionally test Kubernetes networking, GitOps sync, or production-like config.
