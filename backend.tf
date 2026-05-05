terraform {
  backend "s3" {
    bucket         = "gazette-concierge-terraform-state"
    key            = "gazette/terraform.tfstate"
    region         = "ap-south-1"
    use_lockfile   = true
    encrypt        = true
  }
}