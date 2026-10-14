variable "aws_region" {
  description = "AWS region in which the temporary demo instance will be created."
  type        = string
  default     = "ap-southeast-2"
}

variable "instance_type" {
  description = "Configured EC2 instance type; verify account eligibility and current pricing before use."
  type        = string
  default     = "m7i-flex.large"

  validation {
    condition     = var.instance_type == "m7i-flex.large"
    error_message = "This deployment is configured for m7i-flex.large and the matching AMD64 Ubuntu image."
  }
}

variable "ssh_ingress_cidr" {
  description = "Your public IPv4 address in CIDR notation, e.g. 198.51.100.25/32. SSH is never open to all IPs."
  type        = string

  validation {
    condition     = can(cidrnetmask(var.ssh_ingress_cidr)) && endswith(var.ssh_ingress_cidr, "/32")
    error_message = "Set ssh_ingress_cidr to your single public IPv4 address with a /32 mask."
  }
}

variable "ssh_key_name" {
  description = "Name of an existing EC2 key pair in aws_region. Keep its private key private."
  type        = string
}

variable "volume_size_gib" {
  description = "Encrypted root volume size. Increase only after reviewing storage costs."
  type        = number
  default     = 40

  validation {
    condition     = var.volume_size_gib >= 30 && var.volume_size_gib <= 100
    error_message = "volume_size_gib must be between 30 and 100 GiB."
  }
}
