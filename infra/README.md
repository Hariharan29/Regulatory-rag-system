# Temporary AWS demo infrastructure

Terraform configuration for a single Ubuntu 24.04 ARM64 EC2 host. It installs
Docker Engine and the Compose plugin, then leaves application deployment to the
operator. The production Compose stack runs the frontend, API, PostgreSQL with
pgvector, and Ollama on that host.

This is a portfolio/demo configuration, not production-hardened hosting. It
exposes HTTP on port 80 to the internet and restricts SSH on port 22 to one
configured IPv4 address. PostgreSQL, Ollama, and the API have no public port
mappings. HTTPS, DNS, backups, high availability, and monitoring are not
provisioned.

## Before provisioning

- Verify that your AWS account is eligible for the plan/credits you intend to
  use. A `t4g.large` instance and 40 GiB encrypted gp3 volume are **not
  guaranteed to be free**. Credits, eligibility, and service limits vary;
  review the AWS Billing console and current terms before applying. CPU credit
  mode is set to `standard` to avoid unlimited-mode surplus-credit charges.
- Install AWS CLI and Terraform. Configure AWS CLI with IAM Identity Center/SSO
  or another temporary-credential mechanism; do not create root access keys.
- Create an EC2 key pair in the selected region and store its private key
  securely outside the repository.
- Confirm that the selected region has a default VPC and a public subnet.
- Get your current public IPv4 address and use it as `ssh_ingress_cidr` with a
  `/32` suffix. The example address in `terraform.tfvars.example` is reserved
  for documentation and must be replaced.
- Ensure the nested application repository is available for cloning from the
  instance. Do not put a GitHub token in Terraform variables, user data, or Git.
- Understand that this configuration uses a changing public IPv4 address and
  plain HTTP. Do not use it for sensitive data or real regulatory workflows.

Terraform uses the credentials in the active AWS CLI profile. It does not
create access keys, store app secrets, run SSH commands, or deploy the app.
The bootstrap script installs Docker only; no AWS API credentials are installed
on the EC2 instance.

## Review and provision manually

From this directory in PowerShell:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars
terraform init
terraform fmt -check
terraform validate
$env:AWS_PROFILE = "finance-rag"
aws sso login --profile $env:AWS_PROFILE
terraform plan -out=tfplan
terraform show tfplan
```

Review every planned resource and the account's current cost/free-plan status.
Provisioning is a separate, explicit action:

```powershell
terraform apply tfplan
terraform output
```

Do not run `terraform apply` unless you personally approve the plan and any
possible charges. CI does not provision infrastructure.

Terraform state is local, ignored by Git, and should be kept private. Back it up
securely if the deployment must be managed from another machine. The committed
`.terraform.lock.hcl` should be retained to pin the selected provider version.

## Deploy the application after provisioning

Wait for cloud-init to finish, then connect using the output IP and the private
key for the EC2 key pair:

```powershell
ssh -i C:\path\to\finance-rag-demo.pem ubuntu@<public-ip>
```

On the EC2 instance, check cloud-init and clone the repository. Replace the
repository URL with the clone URL for your repository. If it is private,
configure access securely on the instance; never embed a personal access token
in a clone URL or shell history. Check out the reviewed commit or branch that
contains the deployment files before continuing.

```bash
cloud-init status --wait
git clone <repository-url> /opt/finance-rag
cd /opt/finance-rag
mkdir -p data/raw_pdfs
umask 077
DB_PASSWORD="$(openssl rand -hex 24)"
cat > .env <<EOF
DATABASE_URL=postgresql+psycopg2://raguser:${DB_PASSWORD}@db:5432/financerag
DB_PASSWORD=${DB_PASSWORD}
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434/v1
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.2:3b
LOG_LEVEL=INFO
EOF
unset DB_PASSWORD
```

Add the source PDFs to `data/raw_pdfs` on the instance. For example, from a
second PowerShell terminal:

```powershell
scp -i C:\path\to\finance-rag-demo.pem C:\path\to\regulatory.pdf ubuntu@<public-ip>:/opt/finance-rag/data/raw_pdfs/
```

Back on the instance, start the database and model service, download the models,
build/start the application, apply migrations, and ingest the PDFs:

```bash
docker compose -f docker-compose.prod.yml up -d db ollama
docker compose -f docker-compose.prod.yml exec ollama ollama pull nomic-embed-text
docker compose -f docker-compose.prod.yml exec ollama ollama pull llama3.2:3b
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm backend python -m scripts.ingest
```

The model downloads and Docker images consume disk and network traffic; allow
time for them to finish. The small demo instance has limited CPU. Local model
inference may be slow and can exhaust memory under concurrent load.

Verify `http://<public-ip>/` in a browser and `http://<public-ip>/api/health`.
The app and API are intentionally served from the same origin, so browser API
requests use the Nginx proxy rather than exposing port 8000.

## Stop and remove resources

When the demo is finished, destroy all Terraform-managed resources from this
directory. Review the destroy plan before confirming:

```powershell
terraform plan -destroy
terraform destroy
```

Destroying the instance permanently deletes its encrypted root volume and the
database/model data on it. Confirm the destroy completes; check the AWS
console's EC2, EBS, and billing pages afterward for any leftover resources.
Do not rely on stopping the instance as cost cleanup: attached storage may
continue to incur charges.
