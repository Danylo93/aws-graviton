terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region
  default_tags { tags = { Project = "graviton-gitlab-lab", Owner = "lab" } }
}

variable "region" {
  type = string
  default = "us-east-1"
}
variable "ssh_cidr" {
  type = string
  description = "IP público da máquina com runner próprio, em CIDR /32"
  validation {
    condition = can(cidrhost(var.ssh_cidr, 0)) && endswith(var.ssh_cidr, "/32")
    error_message = "Informe um único IP público IPv4 em /32."
  }
}
variable "public_key_path" {
  type = string
  description = "Caminho absoluto da chave SSH pública; a privada fica fora do repositório."
}

data "aws_vpc" "default" { default = true }
data "aws_subnets" "default" {
  filter {
    name = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name = "default-for-az"
    values = ["true"]
  }
}
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

resource "aws_security_group" "lab" {
  name_prefix = "graviton-gitlab-lab-"
  description = "SSH limitado ao IP do runner local"
  vpc_id = data.aws_vpc.default.id
  ingress {
    description = "SSH do runner local"
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "lab" {
  key_name_prefix = "graviton-gitlab-lab-"
  public_key = file(pathexpand(var.public_key_path))
}

resource "aws_instance" "lab" {
  ami = data.aws_ssm_parameter.al2023.value
  instance_type = "t4g.small"
  subnet_id = sort(data.aws_subnets.default.ids)[0]
  vpc_security_group_ids = [aws_security_group.lab.id]
  key_name = aws_key_pair.lab.key_name
  associate_public_ip_address = true
  monitoring = false
  credit_specification { cpu_credits = "standard" }
  metadata_options {
    http_endpoint = "enabled"
    http_tokens = "required"
  }
  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted = true
    delete_on_termination = true
  }
  user_data = <<-USERDATA
    #!/bin/bash
    set -euxo pipefail
    dnf install -y docker
    systemctl enable --now docker
    usermod -aG docker ec2-user
  USERDATA
  tags = { Name = "graviton-gitlab-lab" }
}

output "public_ip" { value = aws_instance.lab.public_ip }
output "instance_id" { value = aws_instance.lab.id }
