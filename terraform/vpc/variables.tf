variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  default     = "10.1.0.0/16"
}

variable "environment" {
  description = "environment"
  default     = "temporal-dev"
}

variable "azs" {
  description = "List of availability zones in the region"
  type        = list(string)
  default     = ["ap-northeast-1a", "ap-northeast-1c"]
}
