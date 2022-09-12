resource "aws_instance" "compute_instance" {
    ami = "ami-02f3416038bdb17fb"
    instance_type = "t3.2xlarge"
    security_groups = [ "default" ]
    iam_instance_profile = var.instance_profile_id
    key_name = var.key_name
    tags = {
      "Name" = var.instance_name
    }
}

resource "aws_ebs_volume" "compute_volume" {
    availability_zone = aws_instance.compute_instance.availability_zone
    size = var.volume_size
    type = "gp2"
}

resource "aws_volume_attachment" "ebs_attach" {
    device_name = "/dev/sdh"
    volume_id = aws_ebs_volume.compute_volume.id
    instance_id = aws_instance.compute_instance.id
}