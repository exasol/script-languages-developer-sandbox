
default_config = {
    "time_to_wait_for_polling": 10.0,
    # Source AMI is set to Ubuntu 20.04
    "source_ami_filters": {
        "name": "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*",
        "owner-id": "099720109477",
        "architecture": "x86_64",
        "state": "available"
    }
}


class ConfigObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


global_config = ConfigObject(**default_config)
