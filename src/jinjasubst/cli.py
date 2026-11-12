import os
import sys
import shlex
import base64
import argparse
import traceback
import subprocess

# For template rendering
import jinja2


def _run(value, input: str | bytes = None, shell: bool = True, check: bool = False):
    # Convert input to bytes
    if isinstance(input, bytes):
        input = input.decode("utf-8")

    # Run value as a shell command and capture the output
    process = subprocess.run(value, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, input=input, shell=shell, check=check)

    # Return the process output
    return process.stdout


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

    # Functions that have the same implementation as globals and filters
    functions = dict(
        # Shell argument quoting
        shlex=shlex.quote,
        shlex_quote=shlex.quote,
        shlex_split=shlex.split,

        # Hex encoding
        hex=lambda value: bytes.hex(value.encode("utf-8")),
        hex_encode=lambda value: bytes.hex(value.encode("utf-8")),
        hex_decode=lambda value: bytes.fromhex(value).decode("utf-8"),

        # Base64 encoding
        base64=lambda value: base64.b64encode(value.encode("utf-8")).decode("utf-8"),
        base64_encode=lambda value: base64.b64encode(value.encode("utf-8")).decode("utf-8"),
        base64_decode=lambda value: base64.b64decode(value.encode("utf-8")).decode("utf-8"),
    )

    # Add functions to globals and filters
    environment.globals.update(functions)
    environment.filters.update(functions)

    # If shell filter is enabled, add it
    if arguments.shell:
        # Globals don't take input, so lambdas are without input
        environment.globals.update(
            shell=lambda command: _run(command, shell=True, check=False),
            shell_check=lambda command: _run(command, shell=True, check=True),
            exec=lambda *arguments: _run(arguments, shell=False, check=False),
            exec_check=lambda *arguments: _run(arguments, shell=False, check=True),
        )

        # Filters take input, so use input
        environment.filters.update(
            shell=lambda input, command: _run(command, input=input, shell=True, check=False),
            shell_check=lambda input, command: _run(command, input=input, shell=True, check=True),
            exec=lambda input, *arguments: _run(arguments, input=input, shell=False, check=False),
            exec_check=lambda input, *arguments: _run(arguments, input=input, shell=False, check=True),
        )

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
