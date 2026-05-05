provider "aws" {
  region = "ap-south-1"
}

data "aws_ami" "latest_al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = "gazette-key"
  public_key = file("~/.ssh/gazette-key.pub")
}

resource "aws_security_group" "gazette_sg" {
  name        = "gazette-sg"
  description = "Security group for Gazette app"

  ingress {
    description = "Allow SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["106.222.205.101/32"] 
  }

  ingress {
    description = "App traffic (HTTP)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "App traffic (HTTPS)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.latest_al2023.id
  instance_type = "t3.micro"
  vpc_security_group_ids = [aws_security_group.gazette_sg.id]

  key_name = "gazette-key"

  tags = {
    Name = "gazette-app"
  }

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install docker -y
              service docker start
              usermod -aG docker ec2-user
              EOF
}