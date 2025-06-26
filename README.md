# Easydeps

My attempt to write a script to help with writing EasyConfig (.eb) files. If you create a new, or begin to update an older file as long as you put the dependencies and the (new) toolchain, this script should use those fields to search for possible compatible existing modules.

It leverages the `eb --search` command, so having [EasyBuild](https://easybuild.io/) installed and any additional EasyConfig repos added to your `EASYBUILD_ROBOT_PATHS` is required.

### Requirements
- [Install EasyBuild](https://docs.easybuild.io/installation/)
- Update your `EASYBUILD_ROBOT_PATHS` environment variable to include any additional GitHub repos containing more EasyConfig files.

### Usage
```bash
python find_easyconfig_deps.py [-i | --input-file] /path/to/easyconfig.eb [-b | --builddependendies]
```
Mandatory `-i` or `--input-file` followed by the path to the EasyConfig file\
Optional `-b` or `--builddependendies` to search for the build dependencies, by default it will search for dependencies only.
