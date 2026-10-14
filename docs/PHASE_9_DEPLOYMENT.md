# Phase 9: Temporary cloud deployment

## Scope

The repository now contains Terraform for a single Ubuntu 24.04 AMD64 EC2 host
and a separate production Docker Compose stack. The host bootstrap installs
Docker; application deployment is performed manually over SSH. The stack
contains React/Nginx, FastAPI, PostgreSQL/pgvector, and Ollama. Only HTTP is
public, SSH is restricted to a configured `/32` IPv4 source, and the database,
Ollama, and API ports are internal to Docker Compose.

This is intentionally a short-lived portfolio demo architecture. It does not
include TLS/domain provisioning, managed database, backups, high availability,
centralized logs, or automated cloud deployment. The public IP is ephemeral.

## Cost and safety

The configured EC2 size is `m7i-flex.large` with a 40 GiB encrypted gp3 root
volume to provide more capacity than a micro instance. These resources are **not
guaranteed to be free**. Free plan eligibility and credits are account-specific
and can change; storage, public IPv4, data transfer, and usage outside current
allowances can be billable. Check the account plan and estimate before apply.

The temporary AWS demo was deployed and smoke-tested, then destroyed. The
frontend, API health endpoint, four ingested PDFs, and a generated answer were
checked during the demo. Terraform state is now empty. The endpoint used plain
HTTP and the local Ollama model produced slow responses; this was a portfolio
demo, not production hosting.

## Repository workflow

Follow [`infra/README.md`](../infra/README.md) for prerequisites, AWS CLI SSO,
Terraform setup, manual provisioning, remote deployment, verification, and
cleanup. The deployment uses generated database credentials in a server-local
`.env`; no AWS or database secret should be committed to Git.

The frontend is built as a static production bundle in
[`frontend/Dockerfile`](../frontend/Dockerfile). Nginx serves the SPA and
proxies `/api/*` to the internal FastAPI container. The production compose file
[`docker-compose.prod.yml`](../docker-compose.prod.yml) does not publish the
database or backend ports to the internet.

## Verification completed and limitations

The following smoke checks were completed during the temporary deployment:

1. Terraform formatting and validation passed.
2. The public frontend and API health endpoint responded.
3. Four sample PDFs were ingested and listed by the API.
4. A sample query returned a generated answer in the browser.
5. The Terraform-managed instance and security group were destroyed.

The deployment was temporary and HTTP-only. AWS billing data can lag, so check
the account's billing pages for any residual or delayed charges.
