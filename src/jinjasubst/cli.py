import os
import sys
import shlex
import base64
import argparse
import traceback
import subprocess

# For template rendering
import yaml
import jinja2


def _internal_normalize(value: str | bytes) -> str:
    # Convert input to string
    if isinstance(value, bytes):
        return value.decode("utf-8")

    # Make sure input is a string
    if isinstance(value, str):
        return value

    # Not a valid value
    raise ValueError(f"{value!r} is not a string")


# Define helper functions to be used in lambdas
def _internal_run_process(value, input: str | bytes = None, shell: bool = True, check: bool = False) -> str:
    if input is not None:
        # Convert input to string
        input = _internal_normalize(input)

    # Run value as a shell command and capture the output
    process = subprocess.run(value, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, input=input, shell=shell, check=check)

    # Return the process output
    return process.stdout


def main():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # POSIX envsubst style compatibility
    parser.add_argument("-p", "--posix", action="store_true", help="Use POSIX like ${variable} syntax")

    # Custom prefix and suffix
    parser.add_argument("-P", "--prefix", action="store", type=str, help="Variable start string")
    parser.add_argument("-S", "--suffix", action="store", type=str, help="Variable end string")

    # Enable command execution support
    parser.add_argument("-s", "--shell", action="store_true", help="Enable shells functionality")

    # Enable strict variable names
    parser.add_argument("-e", "--strict", action="store_true", help="Error out when a value is missing")

    # Load additional variable to the context from YAML
    parser.add_argument("-f", "--load", action="store", type=str, nargs="*", help="Load YAML variable file")

    # Input filename
    parser.add_argument("-i", "--input", action="store", type=str, default="-", help="Input file path")

    # Output filename
    parser.add_argument("-o", "--output", action="store", type=str, default="-", help="Output file path")

    # Parse the arguments
    arguments = parser.parse_args()

    # Generate the search path. When reading from stdin (-), this would be the current working directory.
    searchpath = os.path.dirname(arguments.input) or os.getcwd()

    # Create context variables
    context = dict()

    # Load additional variable files
    if arguments.load:
        for path in arguments.load:
            with open(path, "r", encoding="utf-8") as variables_file:
                context.update(yaml.safe_load(variables_file))

    # Load the environment into the context
    context.update(os.environ.copy())

    # Create jinja2 environment
    environment = jinja2.Environment(
        # Disable autoescaping of HTML tags
        autoescape=False,

        # Don't strip outputs
        keep_trailing_newline=True,

        # File system loader for {% include %}
        loader=jinja2.FileSystemLoader(searchpath),
    )

    if arguments.posix:
        # Variables start with ${ just like in POSIX shells
        environment.variable_start_string = "${"

        # Variables end with } just like in POSIX shells
        environment.variable_end_string = "}"

    if arguments.prefix:
        # Use custom prefix
        environment.variable_start_string = arguments.prefix

    if arguments.suffix:
        # Use custom suffix
        environment.variable_end_string = arguments.suffix

    if arguments.strict:
        # Set the error handler
        environment.undefined = jinja2.StrictUndefined

    # Add additional environment globals
    functions = dict(
        # For reading files
        read=lambda *paths: open(os.path.join(searchpath, *[_internal_normalize(path) for path in paths]), "r", encoding="utf-8").read(),

        # For listing files in a directory
        listdir=lambda *paths: os.listdir(os.path.join(searchpath, *[_internal_normalize(path) for path in paths])),

        # For encoding shell arguments
        toshell=lambda value: shlex.quote(_internal_normalize(value)),

        # YAML encoder and decoder
        yaml=lambda value: yaml.safe_dump(value),
        toyaml=lambda value: yaml.safe_dump(value),
        fromyaml=lambda value: yaml.safe_load(_internal_normalize(value)),

        # Hex encoder and decoder
        hex=lambda value: bytes.hex(_internal_normalize(value).encode("utf-8")),
        tohex=lambda value: bytes.hex(_internal_normalize(value).encode("utf-8")),
        fromhex=lambda value: bytes.fromhex(_internal_normalize(value)).decode("utf-8"),

        # Base64 encoder and decoder
        base64=lambda value: base64.b64encode(_internal_normalize(value).encode("utf-8")).decode("utf-8"),
        tobase64=lambda value: base64.b64encode(_internal_normalize(value).encode("utf-8")).decode("utf-8"),
        frombase64=lambda value: base64.b64decode(_internal_normalize(value).encode("utf-8")).decode("utf-8"),
    )

    # Add the functions as globals and filters
    environment.globals.update(functions)
    environment.filters.update(functions)

    # Process execution capabilities are disabled by default since
    # they might expose the rendering host to RCE.
    if arguments.shell:
        # Globals don't take input, so lambdas are without input=
        environment.globals.update(
            shell=lambda command: _internal_run_process(command, shell=True, check=False),
            shell_check=lambda command: _internal_run_process(command, shell=True, check=True),
            exec=lambda *arguments: _internal_run_process(arguments, shell=False, check=False),
            exec_check=lambda *arguments: _internal_run_process(arguments, shell=False, check=True),
        )

        # Filters take input, so use input=
        environment.filters.update(
            shell=lambda input, command: _internal_run_process(command, input=input, shell=True, check=False),
            shell_check=lambda input, command: _internal_run_process(command, input=input, shell=True, check=True),
            exec=lambda input, *arguments: _internal_run_process(arguments, input=input, shell=False, check=False),
            exec_check=lambda input, *arguments: _internal_run_process(arguments, input=input, shell=False, check=True),
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
        template = template.render(context)

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
