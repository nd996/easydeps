#!/usr/bin/env python
#
# neil.douglas@york.ac.uk
#

import argparse
import ast
import os
import re
import subprocess
import sys
import textwrap

# Need the lookup tables in both directions
toolchain_table = {
    '2025a': '14.2.0',
    '2024a': '13.3.0',
    '2023b': '13.2.0',
    '2023a': '12.3.0',
    '2022b': '12.2.0',
    '2022a': '11.3.0',
    '2021b': '11.2.0',
    '2021a': '10.3.0',
}
gcc_table = {
    '14.2.0': '2025a',
    '13.3.0': '2024a',
    '13.2.0': '2023b',
    '12.3.0': '2023a',
    '12.2.0': '2022b',
    '11.3.0': '2022a',
    '11.2.0': '2021b',
    '10.3.0': '2021a',
}


def get_toolchain(file_path):
    """
    Opens the given EasyConfig file, searches and returns the toolchain value
    """

    if not os.path.exists(file_path):
        print(f"Error: file not found at '{file_path}'")
        return None

    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return None

    pattern = re.compile(rf"^toolchain = .+$")
    match = ""

    try:
        with open(file_path, "r") as f:
            for line in f:
                stripped_line = line.strip()
                match = pattern.match(stripped_line)
                if match:
                    # only return the value
                    return match.group().replace("toolchain = ", "")
        # return None if no toolchain is found (should never happen!)
        raise Exception("ERROR: No toolchain found!")

    except SyntaxError as e:
        print(f"Parsing error for 'toolchain' in '{file_path}': {e}")
        print(f"Content attempted to parse:\ntoolchain")
        return None
    except Exception as e:
        print(
            f"An unexpected error occurred while reading the file or parsing 'toolchain': {e}"
        )
        return None


def parse_easyconfig_list_property(file_path, property_name):
    """
    Parses an EasyConfig file and extracts a list property defined as a
    multi-line Python-like list of tuples, including single-line definitions.

    Assumes the property is defined in the format:
    property_name = [
        ('item1', 'val1'),
        ('item2', 'val2', 'val3', CONSTANT),
        ...
    ]
    or
    property_name = [('item1', 'val1'), ('item2', 'val2')]

    Args:
        file_path (str): The path to the EasyConfig file.
        property_name (str): The name of the list property to extract
                             (e.g., 'dependencies', 'builddependencies').

    Returns:
        list: A list of tuples (or other Python literals), or an empty list if
              the property is not found or is empty.
              Returns None if the file does not exist or a parsing error occurs.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return None

    content_to_parse = ""
    in_property_block = False
    # matches pattern of the property_name, '=', and then captures
    # everything from '[' to the end of the line.
    initial_line_pattern = re.compile(
        rf"^\s*{re.escape(property_name)}\s*=\s*\[(.*)$")

    try:
        with open(file_path, "r") as f:
            for line in f:
                stripped_line = line.strip()

                if in_property_block:
                    # If we are already in a block, just append the line.
                    content_to_parse += stripped_line + "\n"
                    # check for the closing bracket ']' at end of line to end the block.
                    if stripped_line.endswith("]"):
                        in_property_block = False
                        break  # Found the end of the block, stop reading lines for this property
                else:
                    match = initial_line_pattern.match(stripped_line)
                    if match:
                        # We found the start of the property list
                        captured_content_after_bracket = match.group(1)
                        content_to_parse = "[" + \
                            captured_content_after_bracket + "\n"

                        # If the closing ']' is on the same line, it's a single-line definition
                        if captured_content_after_bracket.endswith("]"):
                            in_property_block = False  # Already found the end
                            break  # No need to read further lines for this property
                        else:
                            in_property_block = True  # It's a multi-line definition, continue collecting

            if in_property_block:
                # This means we started a block but never found the closing ']'
                print(
                    f"Error: Missing closing ']' for '{property_name}' in '{file_path}'"
                )
                return None

        if not content_to_parse:
            # Property not found or it was like 'prop = ' (no '[')
            return []

        processed_content = content_to_parse.replace("SYSTEM", "'SYSTEM'")

        # safely evaluate the string as a Python literal
        parsed_list = ast.literal_eval(processed_content)

        if not isinstance(parsed_list, list):
            print(
                f"Warning: Expected a list for '{property_name}', but got {type(parsed_list)}"
            )
            return []

        return parsed_list

    except SyntaxError as e:
        print(f"Parsing error for '{property_name}' in '{file_path}': {e}")
        print(f"Content attempted to parse:\n{content_to_parse}")
        return None
    except Exception as e:
        print(
            f"An unexpected error occurred while reading the file or parsing '{property_name}': {e}"
        )
        return None


def validate_file(arg):
    if (os.path.exists(arg)):
        return arg
    else:
        raise FileNotFoundError(arg)


def get_toolchain_version(tc):
    if tc == 'SYSTEM':
        return tc
    else:
        # evaluate the string to a dict, return only the version string
        dict = ast.literal_eval(tc)
        return dict["version"]


def get_dependencies_list(deps):
    list = []
    for dep in deps:
        list.append(dep[0])
    return list


def string_to_list(str):
    return [y for y in (x.strip() for x in str.splitlines()) if y]


def return_matched_items(list, pattern):
    result = None
    result = [v for v in list if pattern in v]
    return(result)


def get_compatible_dependency(toolchain, deps):
    tcver = get_toolchain_version(toolchain)
    print(f"tcver: {tcver}")

    # get toolchain compatible GCC version
    altver = None
    if re.match(rf"\d\d\d\d[abc]", tcver):
        altver = toolchain_table[tcver]
        print(f"altver: {altver}")
    elif re.match(rf"\d+\.\d\.\d", tcver):
        altver = gcc_table[tcver]
        print(f"altver: {altver}")


    matches = ''
    for dep in deps:
        module = dep[0]
        # search for deps with full paths, store results
        command = f"eb --search {module}"
        matches += subprocess.check_output(command, shell=True, text=True)

    if not tcver == 'SYSTEM':
        results = return_matched_items(string_to_list(matches), tcver)
        results += return_matched_items(string_to_list(matches), altver)
    else: results = matches.split('\n')[2:]

    # search results for matching toolchain OR version (unless gcc == None)
    if altver == None:
        command = f""

    return results


def print_results(list):
    # https://cissandbox.bentley.edu/sandbox/wp-content/uploads/2022-02-10-Documentation-on-f-strings-Updated.pdf
    """Takes a list of results and prints them one item at a time cleaning the results"""
    for item in list:
        x = item.replace("*", "").strip()
        print(x)
    return

def print_info(ec, tc, deps, bdeps):
    """Print useful info of that easyconfig, toolchain, dependencies and builddependencies are found"""
    print(f"EasyConfig:\t\t {ec}")
    print(f"Toolchain:\t\t {tc}")
    print(f"Toolchain version:\t {get_toolchain_version(tc)}")
    print(f"Builddependencies:\t {bdeps}")
    print(f"Dependencies:\t\t {deps}")
    print(f"Deps list:\t\t {get_dependencies_list(deps)}")


if __name__ == "__main__":
    """Entry point of the script"""

    examples = textwrap.dedent(
        f"""
           Example usage with EasyBuild:
            {sys.argv[0]} -i example.eb
    """
    )

    parser = argparse.ArgumentParser(
        prog = 'parse_easyconfig_list_property.py',
        description = "Find compatible ECs to dependencies",
        epilog = examples,
    )

    parser.add_argument("-b", metavar="builddependency",
                        help = "Search for 'builddependency'",
                        action = argparse.BooleanOptionalAction)
    parser.add_argument("-i", type=validate_file, metavar="/path/to/easyconfig.eb",
                        help = "EasyConfig file path", required = True)
    args = parser.parse_args()

    toolchain = get_toolchain(args.i)
    builddependencies = parse_easyconfig_list_property(
        args.i, 'builddependencies')
    dependencies = parse_easyconfig_list_property(args.i, 'dependencies')

    print_info(os.path.basename(args.i), toolchain, dependencies, builddependencies)

    if args.b:
        print_results(get_compatible_dependency(toolchain, builddependencies))
    else:
        print_results(get_compatible_dependency(toolchain, dependencies))
