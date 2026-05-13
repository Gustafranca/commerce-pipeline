# Kubernetes manifests (GitOps-friendly)

Application resources are built with **Kustomize**:

- [base/](base/) — shared manifests (namespace, Postgres, backend, frontend, ingress, Airflow secrets).
- [overlays/staging/](overlays/staging/) — staging image tags (update via CI or `scripts/set-image-tags.sh`).
- [overlays/prod/](overlays/prod/) — production image tags (pin semver or digest here).

Airflow is installed with **Helm** separately from Kustomize; values live in [helm/](helm/).

## Preview manifests

```bash
kubectl kustomize k8s/overlays/staging
kubectl kustomize k8s/overlays/prod
```

## Apply manually (without GitOps)

```bash
kubectl apply -k k8s/overlays/staging
```

For Airflow (after secrets exist in the cluster):

```bash
helm upgrade --install airflow apache-airflow/airflow \
  --namespace pipeline-commerce \
  --create-namespace \
  --version 1.16.0 \
  -f k8s/helm/airflow-values-staging.yaml
```

## GitOps

See [gitops/argocd/README.md](../gitops/argocd/README.md) for Argo CD `Application` examples.

## Cluster access (Minikube / ingress)

See [docs/staging-cluster-access.md](../docs/staging-cluster-access.md).
