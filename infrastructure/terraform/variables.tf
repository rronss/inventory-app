variable "name" {
  description = "Used for resource names and the Project tag."
  type        = string
  default     = "crate"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "domain" {
  description = "Domain that will point at the server, for HTTPS. Empty until there is one."
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "An ARM (Graviton) type: the images are built for arm64."
  type        = string
  default     = "t4g.micro"
}

variable "server_disk_gb" {
  type    = number
  default = 20
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_storage_gb" {
  type    = number
  default = 20
}

variable "db_backup_days" {
  type    = number
  default = 7
}
