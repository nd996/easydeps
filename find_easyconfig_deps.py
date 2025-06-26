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
    Opens the given EasyConfig file, searches for the 'toolchain' definition,
    and returns its value.

    The toolchain is expected to be on a line like:
    toolchain = {'name': 'foss', 'version': '2023b'}

    Args:
        file_path (str): The path to the EasyConfig file.

    Returns:
        str: The string representation of the toolchain value 
             (e.g., "{'name': 'foss', 'version': '2023b'}"), or None if the file
             does not exist or toolchain is not found.
    """
    if not os.path.exists(file_path):
        print(f"Error: file not found at '{file_path}'")
        return None

    pattern = re.compile(r"^toolchain = (.+)$")

    try:
        with open(file_path, "r") as f:
            for line in f:
                stripped_line = line.strip()
                match = pattern.match(stripped_line)
                if match:
                    # Return only the value part after "toolchain = "
                    return match.group(1).strip()
        # If no toolchain is found after reading the entire file
        raise Exception("ERROR: No toolchain found in the EasyConfig file!")

    except SyntaxError as e:
        print(f"Parsing error for 'toolchain' in '{file_path}': {e}")
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
       list: A list of strings or an empty list if the property is not found or
             is empty. Returns None if the file does not exist or a parsing 
             error occurs.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return None

    content_to_parse = ""
    in_property_block = False
    # This pattern matches the property name, '=', and then captures
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

        # Pre-process the content: replace bare 'SYSTEM' with quoted 'SYSTEM'
        # This handles cases like ('CUDA', '12.2.0', '', SYSTEM)
        # It's important to only replace if 'SYSTEM' is a bare word within a tuple,
        # not if it's part of a string. This simple replace assumes it's always bare.
        # This is a bit fragile if 'SYSTEM' can appear in string literals like "MY_SYSTEM_VAR"
        # A more robust solution might involve tokenizing or a more complex regex for 'bare SYSTEM'.
        # For typical easyconfig, this direct replace should be sufficient.
        processed_content = content_to_parse.replace("SYSTEM", "'SYSTEM'")
        # Add a placeholder for other potential bare constants if they appear
        # e.g., processed_content = processed_content.replace('TRUE', 'True') etc.

        # Safely evaluate the string as a Python literal
        # ast.literal_eval is safer than eval() as it only processes literal structures.
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
    """
    Validates if the provided argument is a valid file path.

    Args:
        arg (str): The file path to validate.

    Returns:
        str: The validated file path if it exists.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if os.path.exists(arg):
        return arg
    else:
        raise FileNotFoundError(f"Error: File not found at '{arg}'")


def get_toolchain_version(tc_string):
    """
    Extracts the version from a toolchain string.

    Args:
        tc_string (str): A string representing the toolchain, e.g., "{'name': 'foss', 'version': '2023b'}" or "SYSTEM".

    Returns:
        str: The toolchain version e.g., '2023b' or 'SYSTEM'.
    """
    if tc_string == 'SYSTEM':
        return tc_string
    else:
        # Evaluate the string to a dict and return the version string
        # Assuming format is {'name': 'foss', 'version': '2023b'}
        parsed_tc = ast.literal_eval(tc_string)
        if isinstance(parsed_tc, dict) and 'version' in parsed_tc:
            return parsed_tc['version']
        else:
            print(
                f"Warning: Unexpected toolchain format: {tc_string}. Returning original string.")
            return tc_string


def get_dependencies_list(deps):
    """
    Extracts the module names from a list of dependency tuples.

    Args:
        deps (list): A list of dependency tuples, e.g., [('zlib', '1.2.13'), ...].

    Returns:
        list: A list of dependency module names, e.g., ['zlib', 'bzip2', ...].
    """
    result_list = []
    for dep in deps:
        if isinstance(dep, tuple) and len(dep) > 0:
            result_list.append(dep[0])
        else:
            print(f"Warning: Unexpected dependency format in list: {dep}")
    return result_list


def string_to_list(input_string):
    """
    Converts a multi-line string into a list of non-empty, stripped lines.

    Args:
        input_string (str): The input string, possibly containing multiple lines.

    Returns:
        list: A list where each element is a stripped, non-empty line from the input.
    """
    return [y for y in (x.strip() for x in input_string.splitlines()) if y]


def return_matched_items(items_list, pattern):
    """
    Filters a list of strings, returning only those that contain the given pattern.

    Args:
        items_list (list): A list of strings to search through.
        pattern (str): The substring pattern to search for.

    Returns:
       list: A list of items from items_list that contain the pattern.
    """
    result = [item for item in items_list if pattern in item]
    return result


def get_compatible_dependency(toolchain, deps):
    """
    Searches for compatible EasyBuild dependencies based on the provided toolchain
    and a list of dependencies. It uses 'eb --search' command.

    Args:
        toolchain (str): The toolchain string (e.g., "('foss', '2023b')").
        deps (list): A list of dependency tuples, e.g., [('Python', '3.10.4')].

    Returns:
       list: A list of strings representing the compatible EasyBuild modules found.
             Returns an empty list if no matches are found or an error occurs.
    """
    tc_version = get_toolchain_version(toolchain)
    print(f"Toolchain version for search: {tc_version}")

    # Get toolchain compatible GCC version or EasyBuild version
    alt_version = None
    if re.match(r"\d{4}[abc]", tc_version):  # e.g., 2023a, 2024b
        alt_version = toolchain_table.get(tc_version)
        print(f"Alternate GCC version: {alt_version}")
    elif re.match(r"\d+\.\d+\.\d", tc_version):  # e.g., 12.3.0, 13.2.0
        alt_version = gcc_table.get(tc_version)
        print(f"Alternate EasyBuild toolchain version: {alt_version}")

    matches = ''
    all_results = []

    if tc_version == 'SYSTEM':
        # For SYSTEM toolchain, just search for the modules
        for dep in deps:
            module_name = dep[0]
            command = f"eb --search {module_name}"
            try:
                matches += subprocess.check_output(
                    command, shell=True, text=True, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                print(
                    f"Warning: 'eb --search {module_name}' failed with error: {e.stderr.strip()}")
        # Filter out header line, only when its a SYSTEM toolchain as we don't filter any further
        all_results = string_to_list(matches)
        if len(all_results) > 1:  # Assuming first line of output is a header
            all_results = all_results[1:]
        return all_results
    else:
        # Search for each dependency and filter by toolchain version
        for dep in deps:
            module_name = dep[0]
            # use `--search` to get full paths in output to indicate which repo the results are from
            command = f"eb --search {module_name}"
            try:
                module_search_output = subprocess.check_output(
                    command, shell=True, text=True, stderr=subprocess.PIPE)
                module_lines = string_to_list(module_search_output)

                # Filter by primary toolchain version
                results_for_module = return_matched_items(
                    module_lines, tc_version)

                # Filter by alternate version if available
                if alt_version:
                    results_for_module.extend(
                        return_matched_items(module_lines, alt_version))

                # we remove duplicates later, so for now just collect the results
                all_results.extend(results_for_module)

            except subprocess.CalledProcessError as e:
                print(
                    f"Warning: '{command}' failed with error: {e.stderr.strip()}")
            except Exception as e:
                print(
                    f"An unexpected error occurred during search for {module_name}: {e}")
        # use set() to remove duplicates
        return list(set(all_results))


def print_results(results_list):
    """
    Takes a list of search results and prints them one item at a time,
    cleaning up any '*' prefixes typically found in 'eb --search' output.

    Args:
        results_list (list): A list of strings, where each string represents a search result.
    """
    if not results_list:
        print("No compatible modules found. 😔")
        return

    print("\n--- Possible compatible Modules Found ---")
    for item in results_list:
        x = item.replace("*", "").strip()
        if x:  # Only print non-empty results
            print(x)
    print(f"{len(results_list)} modules found! 🎉")


def print_info(ec_file_name, toolchain_str, dependencies_list, builddependencies_list):
    """
    Prints useful information extracted from the EasyConfig file, including
    the EasyConfig filename, toolchain, and parsed dependencies.

    Args:
        ec_file_name (str): The base name of the EasyConfig file.
        toolchain_str (str): The raw toolchain string from the EasyConfig.
        dependencies_list (list): The parsed list of dependencies.
        builddependencies_list (list): The parsed list of build dependencies.
    """
    print("\n--- EasyConfig Information Summary ---")
    print(f"EasyConfig File:\t {ec_file_name}")
    print(f"Toolchain String:\t {toolchain_str}")
    print(f"Toolchain Version:\t {get_toolchain_version(toolchain_str)}")
    print(f"Build Dependencies ({len(builddependencies_list)}):")
    for bdep in builddependencies_list:
        print(f"\t- {bdep}")
    print(f"Dependencies ({len(dependencies_list)}):")
    for dep in dependencies_list:
        print(f"\t- {dep}")
    print(
        f"Dependency Module Names:\t {get_dependencies_list(dependencies_list)}")
    print("------------------------------------")


def main():
    """
    Entry point of the script.
    Parses an EasyConfig file to extract and find compatible dependencies
    using 'eb --search'.
    """

    examples = textwrap.dedent(
        f"""
        Example usage:
          # Search for compatible dependencies of 'example.eb'
          {sys.argv[0]} -i example.eb

          # Search for compatible builddependencies of 'example.eb'
          {sys.argv[0]} -i example.eb -b
        """
    )

    parser = argparse.ArgumentParser(
        prog='easyconfig_deps_finder.py',
        description="""
        A script to parse EasyConfig (.eb) files and find compatible
        EasyBuild modules based on the specified toolchain and dependencies/builddependencies.
        It leverages 'eb --search' to query the EasyBuild environment.
        """,
        epilog=examples,
        # Preserves formatting of description and epilog
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-i",
        "--input-file",
        type=validate_file,
        metavar="/path/to/easyconfig.eb",
        help="""
        Required: Path to the EasyConfig (.eb) file to be parsed.
        This file defines the software configuration, including
        toolchain, dependencies, and build dependencies.
        """,
        required=True
    )
    parser.add_argument(
        "-b",
        "--builddependencies",
        action=argparse.BooleanOptionalAction,
        help="""
        Optional: If specified, the script will search for compatible modules
        based on the 'builddependencies' list defined in the EasyConfig file.
        By default, it searches for 'dependencies'.
        Example: -b or --builddependencies
        """,
    )
    args = parser.parse_args()

    toolchain = get_toolchain(args.input_file)
    builddependencies = parse_easyconfig_list_property(
        args.input_file, 'builddependencies')
    dependencies = parse_easyconfig_list_property(
        args.input_file, 'dependencies')

    print_info(os.path.basename(args.input_file),
               toolchain, dependencies, builddependencies)

    if args.builddependencies:
        print_results(get_compatible_dependency(toolchain, builddependencies))
    else:
        print_results(get_compatible_dependency(toolchain, dependencies))


if __name__ == "__main__":
    main()
