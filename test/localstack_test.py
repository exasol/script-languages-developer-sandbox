import shlex
import subprocess
from typing import Any

import boto3

from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess

from exasol_script_languages_developer_sandbox.lib.run_setup_ec2 import run_lifecycle_for_ec2


class AwsLocalStackAccess(AwsAccess):
    def _get_aws_client(self, service_name: str) -> Any:
        return boto3.client(service_name, endpoint_url="http://localhost:4566", aws_access_key_id="test",
                            aws_secret_access_key="test", region_name="eu-central-1")


def test_with_local_stack():
    """
    This test uses cfn-lint to validate the Cloudformation template.
    (See https://github.com/aws-cloudformation/cfn-lint)
    """
    command = "localstack start -d"

    print("start localstack!")
    process = subprocess.run(shlex.split(command))
    assert process.returncode == 0

    command = "localstack wait -t 30"

    print("wait for localstack to be ready!")
    process = subprocess.run(shlex.split(command))
    assert process.returncode == 0

    try:
        print("run ec2_setup!")
        execution_generator = run_lifecycle_for_ec2(AwsLocalStackAccess(None), None, None)
        res = next(execution_generator)
        while res[0] == "pending":
            res = next(execution_generator)

        ec2_instance_status, host_name, ec2_instance_id, key_file_location = res
        assert ec2_instance_status == "running"
        print("running!")
        res = next(execution_generator)
        ec2_instance_status, host_name, ec2_instance_id, key_file_location = res
        assert ec2_instance_status == "terminated"
    finally:
        command = "localstack stop"
        subprocess.run(shlex.split(command))


if __name__ == '__main__':
    test_with_local_stack()
