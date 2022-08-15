from typing import Tuple, Optional

import click

from exasol_script_languages_developer_sandbox.cli.cli import cli
from exasol_script_languages_developer_sandbox.cli.common import add_options
from exasol_script_languages_developer_sandbox.cli.options.aws_options import aws_options
from exasol_script_languages_developer_sandbox.cli.options.logging import logging_options, set_log_level
from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.print_assets import print_assets, all_asset_types


@cli.command()
@add_options(aws_options)
@add_options(logging_options)
@click.option('--slc-version', type=str, default="",
              help="Filters for a specific version. If empty, shows all versions.")
@click.option('--asset-id', type=str, default=None,
              help="The asset-id used to create the AWS resources during the other commands. "
                   "If not set, all resources will be printed.")
@click.option('--asset-type', default=all_asset_types(),
              type=click.Choice(list(all_asset_types())), multiple=True,
              help="The asset types to print. Can be declared multiple times.")
@click.option('--out-file', default=None, type=click.Path(exists=False, file_okay=True, dir_okay=False),
              help="If given, writes the AWS assets to this file in markdown format.")
def show_aws_assets(
            aws_profile: str,
            slc_version: str,
            asset_id: Optional[str],
            asset_type: Tuple[str, ...],
            out_file: Optional[str],
            log_level: str):
    """
    Shows all AWS assets.
    """
    set_log_level(log_level)
    print_assets(AwsAccess(aws_profile=aws_profile), asset_id=asset_id, outfile=out_file, asset_types=asset_type)
