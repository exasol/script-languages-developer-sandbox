from unittest.mock import MagicMock, call

import pytest

from exasol_script_languages_developer_sandbox.lib.aws_access.ami import Ami
from exasol_script_languages_developer_sandbox.lib.export_vm.run_export_vm import export_vm
from exasol_script_languages_developer_sandbox.lib.export_vm.vm_disk_image_format import VmDiskImageFormat
from test.aws_mock_data import get_ami_image_mock_data, TEST_AMI_ID, TEST_ROLE_ID, TEST_BUCKET_ID, INSTANCE_ID, \
    get_only_vm_stack_side_effect, get_export_image_task_mock_data


def call_counter(func):
    """
    Decorator which passes automatically a counter to the decorated function.
    :param func: The decorated function
    """
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(helper.calls, *args, **kwargs)

    helper.calls = 0
    return helper


@call_counter
def get_ami_side_effect(counter: int, ami_id: str) -> Ami:
    """
    This mock function returns a mocked Ami fascade object.
    On the first 2 invocations the state of the object will be "pending"
    On the 3rd time the returned state will be "available".
    :raises ValueError if the parameter ami_id does not match the expected value.
    """
    if ami_id == TEST_AMI_ID:
        if counter < 3:
            state = "pending"
        else:
            state = "available"
        return get_ami_image_mock_data(state)
    else:
        raise ValueError(f"Unexpect parameter: {ami_id}")


@pytest.fixture
def aws_vm_export_mock():
    """
    Assembles an AwsAccess mock object which:
    :return: 1. Returns the mocked VM Bucket Cloudformation stack when calling get_all_stack_resources()
             2. Returns TEST_AMI_ID when calling create_image_from_ec2_instance()
             3. Returns the mocked ExportImageTask object when calling get_export_image_task()
             4. Returns the mocked Ami object when calling get_ami() (see method get_ami_side_effect() for details
    """
    aws_access_mock = MagicMock()
    aws_access_mock.get_all_stack_resources.side_effect = get_only_vm_stack_side_effect
    aws_access_mock.create_image_from_ec2_instance.return_value = TEST_AMI_ID
    aws_access_mock.get_export_image_task.return_value = get_export_image_task_mock_data(False)
    aws_access_mock.get_ami.side_effect = get_ami_side_effect
    return aws_access_mock


vm_formats = [
    (VmDiskImageFormat.VMDK,),
    (VmDiskImageFormat.VHD,),
    (VmDiskImageFormat.VHD, VmDiskImageFormat.VMDK),
    tuple(vm_format for vm_format in VmDiskImageFormat),
    tuple()
]


@pytest.mark.parametrize("vm_formats_to_test", vm_formats)
def test_export_vm(aws_vm_export_mock, default_asset_id, vm_formats_to_test, test_config):
    """"
    Test if function export_vm() will be invoked
    with expected values when we run_export_vm()
    """
    export_vm(aws_access=aws_vm_export_mock, instance_id=INSTANCE_ID,
              vm_image_formats=tuple(vm_image_format.value for vm_image_format in vm_formats_to_test),
              asset_id=default_asset_id, configuration=test_config)

    aws_vm_export_mock.create_image_from_ec2_instance.assert_called_once_with(INSTANCE_ID,
                                                                              name=default_asset_id.ami_name,
                                                                              tag_value=default_asset_id.tag_value,
                                                                              description="Image Description")

    expected_calls = [
        call(image_id=TEST_AMI_ID,
             tag_value=default_asset_id.tag_value,
             description="VM Description",
             role_name=TEST_ROLE_ID,
             disk_format=disk_format,
             s3_bucket=TEST_BUCKET_ID,
             s3_prefix=f"{default_asset_id.bucket_prefix}/")
        for disk_format in vm_formats_to_test]
    assert aws_vm_export_mock.export_ami_image_to_vm.call_args_list == expected_calls
