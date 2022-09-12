variable "instance_name" {
    type = string
    default = "my-instance"
}

variable "volume_size" {
    default = 30
}

variable "instance_profile_id" {
    type = string
}

variable "key_name" {
    type = string
    default = "ssh_key"
}
