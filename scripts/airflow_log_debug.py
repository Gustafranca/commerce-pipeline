#!/usr/bin/env python3
"""Compare Airflow webserver vs scheduler secret_key and clocks (403 served-log issues)."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# docker-compose.yml container_name per service — used when Compose project name
# does not match (folder rename, or stack started before `name:` was set in compose).
SERVICE_CONTAINER_NAME = {
    "airflow-webserver": "airflow_webserver",
    "airflow-scheduler": "airflow_scheduler",
}


def _compose_connect_failed(stderr: str) -> bool:
    """True if docker compose could not attach (wrong project / service down)."""
    s = (stderr or "").lower()
    return "is not running" in s or "no such service" in s


def _detect_compose_project() -> str | None:
    """Return com.docker.compose.project from a running Airflow container, if any."""
    for cname in SERVICE_CONTAINER_NAME.values():
        r = subprocess.run(
            [
                "docker",
                "inspect",
                "-f",
                "{{index .Config.Labels \"com.docker.compose.project\"}}",
                cname,
            ],
            capture_output=True,
            text=True,
        )
        out = (r.stdout or "").strip()
        if r.returncode == 0 and out and out != "<no value>":
            return out
    return None


def _exec(service: str, args: list[str]) -> tuple[int, str, str]:
    """Run command in container: compose (default project), compose -p <detected>, then docker exec."""
    attempts: list[list[str]] = [
        ["docker", "compose", "exec", "-T", service, *args],
    ]
    project = _detect_compose_project()
    if project:
        attempts.append(
            ["docker", "compose", "-p", project, "exec", "-T", service, *args],
        )
    cname = SERVICE_CONTAINER_NAME.get(service)
    if cname:
        attempts.append(["docker", "exec", cname, *args])

    last_connect_err = ""
    for argv in attempts:
        r = subprocess.run(
            argv,
            cwd=REPO_ROOT if len(argv) > 1 and argv[1] == "compose" else None,
            capture_output=True,
            text=True,
        )
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        if r.returncode == 0:
            return 0, out, err
        # Attached to a container but the inner command failed (e.g. unset env var).
        if not _compose_connect_failed(err):
            return r.returncode, out, err
        last_connect_err = err or last_connect_err
    return 1, "", last_connect_err


def main() -> int:
    services = ["airflow-webserver", "airflow-scheduler"]
    hashes: dict[str, str | None] = {}
    epochs: dict[str, int | None] = {}

    project = _detect_compose_project()
    if project:
        print(f"detected_compose_project: {project}", file=sys.stderr)

    recreate_cmd = (
        f"docker compose -p {project} up -d --force-recreate airflow-webserver airflow-scheduler"
        if project
        else "docker compose up -d --force-recreate airflow-webserver airflow-scheduler"
    )

    for svc in services:
        code, secret, err = _exec(svc, ["printenv", "AIRFLOW__WEBSERVER__SECRET_KEY"])
        ok = code == 0 and bool(secret)
        if not ok:
            hint = err or (
                f"(variable unset — recreate with current compose; try: {recreate_cmd})"
            )
            print(f"{svc}: AIRFLOW__WEBSERVER__SECRET_KEY missing or exec failed: {hint}", file=sys.stderr)
            hashes[svc] = None
        else:
            hashes[svc] = hashlib.sha256(secret.encode()).hexdigest()

        code_t, epoch_out, err_t = _exec(svc, ["date", "-u", "+%s"])
        if code_t == 0 and epoch_out.isdigit():
            epochs[svc] = int(epoch_out)
        else:
            print(f"{svc}: date failed: {err_t}", file=sys.stderr)

    w, s = hashes.get("airflow-webserver"), hashes.get("airflow-scheduler")
    match = w is not None and w == s
    print(f"secret_sha256_match: {match}")
    if w and s:
        print(f"  webserver: {w[:16]}...")
        print(f"  scheduler: {s[:16]}...")

    ew, es = epochs.get("airflow-webserver"), epochs.get("airflow-scheduler")
    if ew is not None and es is not None:
        print(f"utc_epoch_skew_seconds: {abs(ew - es)}")

    code_a, out_a, _ = _exec(
        services[0],
        [
            "python",
            "-c",
            "from airflow.configuration import conf; print(conf.get('webserver','secret_key'))",
        ],
    )
    code_b, out_b, _ = _exec(
        services[1],
        [
            "python",
            "-c",
            "from airflow.configuration import conf; print(conf.get('webserver','secret_key'))",
        ],
    )
    resolved = (
        code_a == 0
        and code_b == 0
        and out_a
        and out_a == out_b
    )
    print(f"resolved_conf_secret_match: {resolved}")
    return 0 if match and resolved else 1


if __name__ == "__main__":
    raise SystemExit(main())
