# Script-Languages-Developer-Sandbox User Guide

## Requirements

This package requires:
* Python (>=3.8)
* Poetry (>=1.2.0)
* Docker (for integration tests)
* AWS CLI

## Overview

This packages aims to create a virtual machine image, in different formats, which can be used to build easily Exasol's script-languages-container, which are the runtime container for UDF's.
The idea is to set-up an AWS EC-2 instance, using cloudformation templates, then install all dependencies via _Ansible_, generate an AMI image based on the final EC-2 instance, and finally export the AMI image to the virtual image formats.
The virtual machine image provides:
* The script-languages-release repositories
* All necessary dependencies to execute _exaslct_ in script-languages-release (This includes a correctly configured docker runtime)
* A running Jupyterlab instance which is automatically started during boot of the vm

## Objective

The objective is to have a complete VM ready, including all dependencies, which can be used as base to customize the existing template script-languages-container (e.g. python-3.x-minimal templates, the r-minimal templates); or, if needed, to create new script-languages-container from scratch.
The VM is per default large enough to build and test script-languages-container.

## Provided medias

### AMI

The AMI id is linked in the release notes and can be used to start an EC2-instance in your AWS account.
Following name format is used for the AMI: "_Exasol-SLC-Developer-Sandbox-**version**_", e.g. "_Exasol-SLC-Developer-Sandbox-5.0.0_"

### VM image

Currently two VM formats are supported:

| Format      | Description                       |
| ----------- | --------------------------------- |
| VMDK        | VMware Virtual Machine Disk       |
| VHD         | Virtual Hard Disk by Microsoft    |

The links to the images are stored in the release notes.  
For security reasons the formats are currently stored in a private AWS S3 Bucket, and not publicly available.
Please feel free to contact us (opensource@exasol.com) if you are interested in getting a copy.

## Usage

At the first login to the sandbox (image or AMI) you will be prompted to change your password.  
The default password is: **scriptlanguages**

However, we suggest to use ssh-keys for the connection. When you use the AWS AMI, this will work automatically. When you use the VM images, you need to deploy your ssh-keys.

Also, we strongly recommend to change the Jupyter password as soon as possible. Details about how to do that will be shown in the login screen.

## Content

### script-languages-release

**Location**: `/home/ubuntu/script-languages-release`  
**Source**: [Github repo](https://github.com/exasol/script-languages-release)  
The images are tightly coupled to the releases of script-languages-release; for each release of the script-languages-release there will be a release of the developer sandbox.  
By default, the images contain a cloned repository of script-languages-container, including all dependencies to run it (Python, Poetry, Docker, etc.). The checked out version will be the tag of the respective release, e.g. a Developer Sandbox image for release 5.0.0 will have the tag 5.0.0 checked out for script-languages-release.  
If you aim to customize existing containers, this should be fine. However, if you want to rebuild a container, you might encounter problems as dependant packages might have changed. In that case, we suggest to check out branch master  
```shell
git checkout --recurse-submodules master
```

For information about how to build script-languages-container please check:
- [slc User Guide](https://github.com/exasol/script-languages-release/blob/master/doc/user_guide/user_guide.md) - Infos about the container
- [exaslct User Guide](https://github.com/exasol/script-languages-container-tool/blob/main/doc/user_guide/user_guide.md) - Details about the build tool

### Jupyter

**Location virtual environment**: `/home/ubuntu/jupyterenv`  
**Location notebooks**: `/home/ubuntu/notebooks`
**Password**: `script-languages`
**Http Port**: 8888  

Check [Jupyter Home](https://jupyter.org/) for more information.
