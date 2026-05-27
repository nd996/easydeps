# neil.douglas@york.ac.uk

import os
import subprocess
import sys
from easybuild.framework.easyconfig.parser import EasyConfigParser

TOOLCHAIN_TABLE = {
    '2026.1': '15.2.0',
    '2025b': '14.3.0',
    '2025a': '14.2.0',
    '2024a': '13.3.0',
    '2023b': '13.2.0',
    '2023a': '12.3.0',
    'system': None,
}

WIDTH = 64

# Generate a reverse lookup dictionary once at startup
REVERSE_TOOLCHAIN_TABLE = {v: k for k, v in TOOLCHAIN_TABLE.items() if v is not None}
IGNORE_MODULES = {'Python'}

def get_alt_toolchain_version(key):
    """Looks up toolchain version by name or GCC version."""
    if key.lower() in TOOLCHAIN_TABLE:
        return TOOLCHAIN_TABLE[key]
    if key.lower() in REVERSE_TOOLCHAIN_TABLE:
        return REVERSE_TOOLCHAIN_TABLE[key]
    raise ValueError(f"No matching toolchain or GCC version for '{key}'")

def get_raw_avail_dependencies(module_name):
    """Queries EasyBuild for available modules."""
    command = f"eb --detect-loaded-modules=ignore --search {module_name}"
    try:
        matches = subprocess.check_output(
            command, shell=True, text=True, stderr=subprocess.PIPE
        )
        # Convert multi-line string to list
        return [line.strip() for line in matches.splitlines() if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"Warning: 'eb --search {module_name}' failed: {e.stderr.strip()}", file=sys.stderr)
        return []

def print_parsed_avail_dependencies(deps, toolchain, alt_toolchain):
    """Searches and prints available modules for a list of dependencies."""
    for d in deps:
        if d in IGNORE_MODULES:
            continue

        raw_deps = get_raw_avail_dependencies(d)

        # If it's the system toolchain, don't filter it just dump all the results
        if toolchain.lower() == 'system':
            matched = raw_deps
            header_info = f"{d} {toolchain}"
        else:
            # items containing toolchain OR alt_toolchain (if it exists)
            matched = [ item for item in raw_deps if toolchain in item or (alt_toolchain and alt_toolchain in item) ]
            header_info = f"{d} {toolchain} {alt_toolchain}"

        print('-' * WIDTH)
        print(f'Results for: {header_info}')
        print('-' * WIDTH)

        for item in matched:
            print(item)

def process_easyconfig(path):
    """Orchestrates the parsing and dependency checking for a single file."""
    try:
        ec = EasyConfigParser(path).get_config_dict()
    except Exception as e:
        print(f"💩 Failed to parse {path}: {e}", file=sys.stderr)
        return False

    toolchain_tc = ec['toolchain']['version']
    toolchain_gcc = get_alt_toolchain_version(toolchain_tc)

    build_dependencies = [dep[0] for dep in ec.get('builddependencies', [])]
    dependencies = [dep[0] for dep in ec.get('dependencies', [])]

    print('=' * WIDTH)
    print(f"Toolchain:\t\t{toolchain_tc}")
    print(f"GCC version:\t\t{toolchain_gcc}")
    print(f"Build Dependencies:\t{', '.join(build_dependencies)}")
    print(f"Dependencies:\t\t{', '.join(dependencies)}")
    print('=' * WIDTH)

    print_parsed_avail_dependencies(build_dependencies, toolchain_tc, toolchain_gcc)
    print_parsed_avail_dependencies(dependencies, toolchain_tc, toolchain_gcc)

    print('=' * WIDTH)
    print('🏁 FINSISHED!!')
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {os.path.basename(__file__)} /path/to/easyconfig/file")
        sys.exit(1)

    files = sys.argv[1:]
    results = [process_easyconfig(f) for f in files]

    # success if all files processed successfully
    sys.exit(0 if all(results) else 1)
