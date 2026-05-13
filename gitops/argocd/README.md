# Argo CD bootstrap (examples)

These manifests expect **Argo CD** installed in the target cluster (namespace `argocd`).

## Prereqs

1. Install Argo CD: https://argo-cd.readthedocs.io/en/stable/getting_started/
2. Replace the placeholder `repoURL` in each `Application` with your Git remote.
3. Ensure the cluster can pull private images (Docker Hub pull secret if needed).

## Applications

- `application-pipeline-commerce-staging.yaml` — Kustomize overlay `k8s/overlays/staging`
- `application-pipeline-commerce-prod.yaml` — Kustomize overlay `k8s/overlays/prod`
- `application-airflow-staging.yaml` — Helm chart `apache-airflow/airflow` + values from `k8s/helm/airflow-values-staging.yaml` (requires Argo CD 2.6+ multi-source)

Apply:

```bash
kubectl apply -f gitops/argocd/
```

Sync policies are conservative (`automated.prune: false`). Enable prune in staging only after you trust the overlay.

## Airflow chart repo

Add the Helm repo to Argo CD (UI *Settings → Repositories* or declaratively), then reference chart in the Application as shown in the YAML.
