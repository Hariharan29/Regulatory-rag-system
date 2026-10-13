# Phase 9: Temporary cloud deployment

## Scope

The repository now contains Terraform for a single Ubuntu 24.04 ARM64 EC2 host
and a separate production Docker Compose stack. The host bootstrap installs
Docker; application deployment is performed manually over SSH. The stack
contains React/Nginx, FastAPI, PostgreSQL/pgvector, and Ollama. Only HTTP is
public, SSH is restricted to a configured `/32` IPv4 source, and the database,
Ollama, and API ports are internal to Docker Compose.

This is intentionally a short-lived portfolio demo architecture. It does not
include TLS/domain provisioning, managed database, backups, high availability,
centralized logs, or automated cloud deployment. The public IP is ephemeral.

## Cost and safety

The default EC2 size is `t4g.large` with a 40 GiB encrypted gp3 root volume so a
small local model has some memory/disk headroom. These resources are **not
guaranteed to be free**. Free plan eligibility and credits are account-specific
and can change; storage, public IPv4, data transfer, and usage outside current
allowances can be billable. Check the account plan and estimate before apply.

No AWS resources were created by preparing these files. Terraform `plan` is
read-only; `apply` creates billable resources and must be a separately reviewed
manual action. `terraform destroy` is documented for cleanup.

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

## Verification still required

The configuration is prepared, not deployed. Before calling Phase 9 complete:

1. Run Terraform formatting and validation locally.
2. Inspect the complete Terraform plan and current AWS account costs.
3. Only after explicit owner approval, apply and deploy to AWS.
4. Verify the public frontend, API health, document ingestion, query, and
   citation behavior.
5. Destroy the temporary deployment and confirm no billable resources remain.
