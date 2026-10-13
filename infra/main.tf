resource "aws_security_group" "demo" {
  name        = "finance-rag-demo"
  description = "Temporary public web demo; SSH limited to the operator's IP."
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP demo frontend"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from the configured operator IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_ingress_cidr]
  }

  egress {
    description = "Allow package, model, and container image downloads"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "finance-rag-demo"
    ManagedBy = "Terraform"
    Purpose   = "Temporary portfolio demonstration"
  }
}

resource "aws_instance" "demo" {
  ami                         = data.aws_ssm_parameter.ubuntu_arm64_ami.value
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnet.selected.id
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.demo.id]
  key_name                    = var.ssh_key_name
  user_data                   = file("${path.module}/bootstrap.sh")
  user_data_replace_on_change = true
  credit_specification {
    cpu_credits = "standard"
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.volume_size_gib
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name      = "finance-rag-demo"
    ManagedBy = "Terraform"
    Purpose   = "Temporary portfolio demonstration"
  }
}
