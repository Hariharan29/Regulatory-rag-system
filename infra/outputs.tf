output "instance_id" {
  description = "EC2 instance ID for monitoring and cleanup."
  value       = aws_instance.demo.id
}

output "public_ip" {
  description = "Ephemeral public IPv4 address; it may change if the instance is replaced or stopped."
  value       = aws_instance.demo.public_ip
}

output "app_url" {
  description = "HTTP URL for the demo frontend. This configuration does not provision TLS."
  value       = "http://${aws_instance.demo.public_ip}"
}

output "ssh_command" {
  description = "SSH command template; replace the private key path with your local key file."
  value       = "ssh -i <path-to-private-key.pem> ubuntu@${aws_instance.demo.public_ip}"
}
