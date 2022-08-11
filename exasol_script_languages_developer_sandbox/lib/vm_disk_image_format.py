from enum import Enum


class VmDiskImageFormat(Enum):
    """
    Contains supported VM image formats as described in
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.export_image
    """
    VMDK = "VMDK"
    RAW = "RAW"
    VHD = "VHD"


def all_vm_disk_image_formats():
    return [vm_format.value for vm_format in VmDiskImageFormat]
