provider "aws" {
  region = "us-east-1"
}

# ANTI-PATTERN 1: Oversized Instance for a Dev Environment
# A 't3.2xlarge' cost ~$300/mo. A dev box usually needs a 't3.medium' ($30/mo).
resource "aws_instance" "app_server_dev" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.2xlarge"  # <--- COST LEAK HERE

  tags = {
    Name = "Dev-App-Server"
    # ANTI-PATTERN 2: Missing Cost Center Tags
  }
}

# ANTI-PATTERN 3: Legacy Storage Type
# 'gp2' is older and more expensive than 'gp3'.
resource "aws_ebs_volume" "app_data" {
  availability_zone = "us-east-1a"
  size              = 100
  type              = "gp2" # <--- COST LEAK HERE (Should be gp3)
}

# DEPENDENCY (The Safety Check):
# This volume is attached to the instance. 
# If we delete the instance, we might orphan the volume.
resource "aws_volume_attachment" "ebs_att" {
  device_name = "/dev/sdh"
  volume_id   = aws_ebs_volume.app_data.id
  instance_id = aws_instance.app_server_dev.id
}