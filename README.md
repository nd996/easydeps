# EasyDeps

## Description

My attempt to write a script to help with writing EasyConfig (.eb) files. If you create a new, or begin to update an older file as long as you put the dependencies and the (new) toolchain, this script should use those fields to search for possible compatible existing modules.

It parses the given EasyConfig file and finds the toolchain version and any listed dependencies and uses them to search for possibly compatible modules by leveraging the `eb --search` command. Having [EasyBuild](https://easybuild.io/) installed and any additional EasyConfig repos added to your `EASYBUILD_ROBOT_PATHS` is required. It only searches for compatible modules using the toolchain and any listed dependencies already written in the EasyConfig file, it does not search for dependencies in any other way.

> *Note:*
> The 'Python' dependency is ignored as the sting appears in so many results it was useless.

## Requirements
- [Install EasyBuild](https://docs.easybuild.io/installation/)
- Update your `EASYBUILD_ROBOT_PATHS` environment variable to include any additional GitHub repos containing more EasyConfig files.

## Example usage
To search for possible compatible dependencies:
```bash
python get_available_deps.py /path/to/easyconfig.eb
```

## BONUS

To validate an EasyConfig file name, based on it's contents:
```bash
python ec_check_name.py /path/to/easyconfig.eb
```
