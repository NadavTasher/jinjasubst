import os
import sys
import json
import shlex
import argparse
import traceback
import subprocess

# For template rendering
import jinja2


def exec(value: str, check: bool = False):
    # Run value as a shell command and capture the output
    process = subprocess.run(value, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=check)

    # Return the process output
    return process.stdout


def exec_check(value: str):
    return exec(value, check=True)


def shell(value: str, command: str, check: bool = False):
    # Run command with value as input and capture the output
    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, input=value, check=check)

    # Return the process output
    return process.stdout


def shell_check(value: str, command: str):
    return shell(value, command, check=True)


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Enable shell filter
    parser.add_argument("-s", "--shell", action="store_true", help="Enable shell() filter")

    # Input filename
    parser.add_argument("-i", "--input", action="store", default="-", help="Input file path")

    # Output filename
    parser.add_argument("-o", "--output", action="store", default="-", help="Output file path")

    # Parse the arguments
    return parser.parse_args()


def main():
    # Parse the arguments
    arguments = parse_arguments()

    # Create jinja2 environment
    environment = jinja2.Environment(
        autoescape=False,
        keep_trailing_newline=True,
    )

    # Add the json dumps filter
    environment.filters.update(json=json.dumps)

    # Add the shlex quote filter
    environment.filters.update(shlex=shlex.quote)

    # If shell filter is enabled, add it
    if arguments.shell:
        # When executing a shell without a filter, shell -> exec
        environment.globals.update(shell=exec, shell_check=exec_check)

        # When executing a shell with a filter, shell -> shell, and takes input
        environment.filters.update(shell=shell, shell_check=shell_check)

    try:
        # Load the input template
        if arguments.input == "-":
            # Load template from stdin
            template = environment.from_string(sys.stdin.read())
        else:
            # Load template from file
            with open(arguments.input, "r", encoding="utf-8") as file:
                template = environment.from_string(file.read())

        # Render the template
        template = template.render(os.environ)

        # Write the rendered template to the output
        if arguments.output == "-":
            # Write to stdout
            sys.stdout.write(template)
        else:
            # Write to file
            with open(arguments.output, "w", encoding="utf-8") as file:
                file.write(template)
    except:
        # Write error to stderr
        sys.stderr.write(traceback.format_exc())

        # Exit with error code
        sys.exit(1)


if __name__ == "__main__":
    # Just call the main function
    main()
