import click

aws_options = [
    click.option('--aws-profile', required=False, type=str,
                 help="Id of the AWS profile to use."),
    click.option('--ec2-key-file', required=False, type=click.Path(exists=True, file_okay=True, dir_okay=False),
                 default=None, help="The EC2 key-pair-file to use. If not given a temporary key-pair-file will be created."),
    click.option('--ec2-key-name', required=False, type=str,
                 default=None, help="The EC2 key-pair-name to use. Only needs to be set together with ec2-key-file."),
]
