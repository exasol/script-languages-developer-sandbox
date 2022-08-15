from typing import Tuple

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
@click.option('--name-suffix', type=str, default="",
              help="An optional suffix appended to the search tag. Mostly for developer checks.")
@click.option('--asset-type', default=all_asset_types(),
              type=click.Choice(list(all_asset_types())), multiple=True,
              help="The asset types to print. Can be declared multiple times.")
def show_aws_assets(
            aws_profile: str,
            slc_version: str,
            name_suffix: str,
            asset_type: Tuple[str, ...],
            log_level: str):
    """
    Shows all AWS assets.
    """
    set_log_level(log_level)
    print_assets(AwsAccess(aws_profile=aws_profile), slc_version=slc_version,
                 name_suffix=name_suffix, asset_types=asset_type)
