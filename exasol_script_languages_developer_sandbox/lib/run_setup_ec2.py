import logging
from contextlib import closing
from typing import Optional
import signal

from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.cf_stack import CloudformationStack
from exasol_script_languages_developer_sandbox.lib.key_file_manager import KeyFileManager


def run_setup_ec2(aws_access: AwsAccess, ec2_key_file: Optional[str], ec2_key_name: Optional[str]) -> None:
    km = KeyFileManager(aws_access, ec2_key_name, ec2_key_file)
    with closing(km):
        cf_stack = CloudformationStack(aws_access)
        with closing(cf_stack):
            cf_stack.launch_ec2_stack(km.key_name)
            ec2_instance_id = cf_stack.get_ec2_instance_id()

            logging.info(f"Waiting for EC2 instance ({ec2_instance_id}) to start...")
            while True:
                ec2_instance_description = aws_access.describe_instance(ec2_instance_id)
                ec2_instance_status = ec2_instance_description["State"]["Name"]
                if ec2_instance_status != "pending":
                    break
                logging.info(f"EC2 instance not ready yet.")

            if ec2_instance_status != "running":
                print(f"Error during startup of EC2 instance '{ec2_instance_id}'. Status is {ec2_instance_status}")
            else:
                host_name = ec2_instance_description["PublicDnsName"]
                print(f"You can now login to the ec2 machine with 'ssh -i {km.key_file_location}  ubuntu@{host_name}'")
            print('Press Ctrl+C to stop and cleanup.')
            signal.pause()
