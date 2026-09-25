# infra/
#
# Terraform files are added in Phase 9.
# Expected files:
#   main.tf       — provider, EC2 instance, security group, Elastic IP
#   variables.tf  — input variables (openai_api_key, db_password marked sensitive)
#   outputs.tf    — exposes the public IP of the EC2 instance
#   terraform.tfvars.example — template; NEVER commit the real terraform.tfvars
#
# State: local .tfstate (gitignored). Back it up privately.
# Apply: run manually from your machine — never auto-applied in CI.
