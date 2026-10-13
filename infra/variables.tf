variable "aws_region" {
  description = "AWS region in which the temporary demo instance will be created."
  type        = string
  default     = "ap-south-1"
}

variable "instance_type" {
  description = "ARM-based EC2 instance type; review the current account's pricing before use."
  type        = string
  default     = "t4g.large"

  validation {
    condition     = startswith(var.instance_type, "t4g.")
    error_message = "Use a Graviton t4g instance type compatible with the selected ARM64 Ubuntu image."
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
