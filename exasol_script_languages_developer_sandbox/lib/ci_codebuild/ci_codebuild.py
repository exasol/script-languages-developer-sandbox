import logging

from exasol_script_languages_developer_sandbox.lib.aws_access.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.render_template import render_template
from exasol_script_languages_developer_sandbox.lib.vm_bucket.vm_slc_bucket import find_vm_bucket

STACK_NAME = "CI-TEST-CODEBUILD"


def run_setup_ci_codebuild(aws_access: AwsAccess) -> None:
    yml = render_template("ci_code_build.jinja.yaml", vm_bucket=find_vm_bucket(aws_access))
    aws_access.upload_cloudformation_stack(yml, STACK_NAME)
    logging.info(f"Deployed cloudformation stack {STACK_NAME}")

