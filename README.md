# EasyDeps

## Description

My attempt to write a script to help with writing EasyConfig (.eb) files. If you create a new, or begin to update an older file as long as you put the dependencies and the (new) toolchain, this script should use those fields to search for possible compatible existing modules.

It parses the given EasyConfig file and finds the toolchain version and any listed dependencies and uses them to search for possibly compatible modules by leveraging the `eb --search` command. Having [EasyBuild](https://easybuild.io/) installed and any additional EasyConfig repos added to your `EASYBUILD_ROBOT_PATHS` is required. It only searches for compatible modules using the toolchain and any listed dependencies already written in the EasyConfig file, it does not search for dependencies in any other way.

## Requirements
- [Install EasyBuild](https://docs.easybuild.io/installation/)
- Update your `EASYBUILD_ROBOT_PATHS` environment variable to include any additional GitHub repos containing more EasyConfig files.

## Example usage
To search for anypossible compatible dependencies:
```bash
python find_easyconfig_deps.py -i /path/to/easyconfig.eb
```

### Options
`-i` or `--input-file` followed by the path to the EasyConfig file (mandatory)\
`-b` or `--builddependencies` to search for the build dependencies, by default it will search for dependencies only (optional)
