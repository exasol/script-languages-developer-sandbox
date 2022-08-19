import os
import time

from datetime import datetime

import pytest

import fabric
import requests

from invoke import Responder

from exasol_script_languages_developer_sandbox.cli.options.id_options import DEFAULT_ID
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_access import AnsibleAccess
from exasol_script_languages_developer_sandbox.lib.asset_id import AssetId
from exasol_script_languages_developer_sandbox.lib.aws_access.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.run_create_vm import run_create_vm
from exasol_script_languages_developer_sandbox.lib.setup_ec2.run_setup_ec2 import run_lifecycle_for_ec2, \
    EC2StackLifecycleContextManager

import string
import random


def generate_random_password(length) -> str:
    return ''.join(random.sample(string.ascii_letters, length))


def change_password(host: str, user: str, curr_pass: str, new_password: str) -> None:
    with fabric.Connection(host, user=user,
                           connect_kwargs={"password": curr_pass}) as con:
        responder_current_password = Responder(
            pattern=r"Current password: ",
            response=f"{curr_pass}\n",
        )
        responder_mew_password = Responder(
            pattern=r"New password: ",
            response=f"{new_password}\n",
        )
        responder_retype_password = Responder(
            pattern=r"Retype new password: ",
            response=f"{new_password}\n",
        )
        res = con.run("uname",
                      watchers=[responder_current_password, responder_mew_password, responder_retype_password],
                      pty=True)
        assert res.ok


@pytest.fixture(scope="session")
def new_ec2_from_ami():
    """
    This fixtures starts the EC-2 instance, runs all setup, exports the AMI,
    then starts another EC-2 instance, based on the new AMI, then changes the password (which is expired),
    and finally  returns that EC-2 name together with the new temporary password.
    """
    default_password = generate_random_password(12)
    new_password = generate_random_password(12)
    aws_access = AwsAccess(aws_profile=None)
    asset_id = AssetId("ci-test-{suffix}-{now}".format(now=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
                                                       suffix=DEFAULT_ID))
    run_create_vm(aws_access, None, None,
                  AnsibleAccess(), default_password, tuple(), asset_id)

    # Use the ami_name to find the AMI id (alternatively we could use the tag here)
    amis = aws_access.list_amis(filters=[{'Name': 'name', 'Values': [asset_id.ami_name]}])
    assert len(amis) == 1
    ami_id = amis[0].id

    stack_prefix = str(asset_id).replace(".", "-")
    lifecycle_generator = run_lifecycle_for_ec2(aws_access, None, None, stack_prefix=stack_prefix,
                                                tag_value=asset_id.tag_value, ami_id=ami_id)

    with EC2StackLifecycleContextManager(lifecycle_generator) as ec2_data:
        ec2_instance_description, key_file_location = ec2_data
        assert ec2_instance_description.is_running

        status = aws_access.get_instance_status(ec2_instance_description.id)
        while status.initializing:
            time.sleep(10)
            status = aws_access.get_instance_status(ec2_instance_description.id)
        assert status.ok
        time.sleep(10)
        change_password(host=ec2_instance_description.public_dns_name, user='ubuntu',
                        curr_pass=default_password, new_password=new_password)
        yield ec2_instance_description.public_dns_name, new_password


@pytest.mark.skipif(os.environ.get('RUN_DEVELOPER_SANDBOX_CI_TEST') != 'true',
                    reason="CI test need to be activated by env variable RUN_DEVELOPER_SANDBOX_CI_TEST")
def test_exaslct_with_ec2_based_on_new_ami(new_ec2_from_ami):
    """
    This test validates that exaslct is correctly working on the EC-2 instance, which was launched from the
    newly created AMI.
    """
    ec2_instance, password = new_ec2_from_ami
    with fabric.Connection(ec2_instance, user='ubuntu',
                           connect_kwargs={"password": password}) as con:
        with con.cd("script-languages-release"):
            cmd = "./exaslct build --flavor-path ./flavors/python-3.8-minimal-EXASOL-6.2.0"
            result = con.run(cmd)
            assert result.ok
            assert result.return_code == 0


@pytest.mark.skipif(os.environ.get('RUN_DEVELOPER_SANDBOX_CI_TEST') != 'true',
                    reason="CI test need to be activated by env variable RUN_DEVELOPER_SANDBOX_CI_TEST")
def test_jupyter_with_ec2_based_on_new_ami(new_ec2_from_ami):
    """
    This test validates that Jupyterlab is correctly working on the EC-2 instance, which was launched from the
    newly created AMI.
    """
    ec2_instance, password = new_ec2_from_ami
    http_conn = requests.get(f"http://{ec2_instance}:8888/lab")
    assert http_conn.status_code == 200
