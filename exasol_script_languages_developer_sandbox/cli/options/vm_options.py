import click

from exasol_script_languages_developer_sandbox.lib.export_vm.vm_disk_image_format \
    import default_vm_disk_image_formats, all_vm_disk_image_formats

vm_options = [
              click.option('--vm-image-format', default=default_vm_disk_image_formats(),
                             type=click.Choice(all_vm_disk_image_formats()), multiple=True,
                             help="The VM image format. Can be declared multiple times."),
              click.option('--no-vm', is_flag=True, help="If set, no vm image will be exported. "
                                                         "Overrides 'vm-image-format."),
              click.option('--name-suffix', type=str, default="", help="A suffix appended to the AMI name and all tags")
]
