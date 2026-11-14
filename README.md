# jinjasubst

## What does it do?

Renders the stdin as a Jinja2 template, with the current environment variables as arguments.

## Installation

```bash
pip install jinjasubst
```

or:

```bash
pipx install jinjasubst
```

## Quirks

The jinja2 environment is initialized with a `FileSystemLoader`.
The searchpath of this loader is the parent directory of the input file.
When the input file is `-` (stdin), the current working directory is used instead.

## Functions and filters

Files and directories:

- read - read a file
- listdir - list entries in a directory

Encoding and escaping:

- toshell - escape using `shlex.quote`
- base64, tobase64 - encode to base64
- frombase64 - decode from base64
- hex, tohex - encode to hex
- fromhex - decode from hex

Process execution, enabled with -s (all accept stdin when used as filters):

- shell - execute shell command
- shell_check - execute shell command and check exit code
- exec - execute program with arguments
- exec_check - execute program with arguments and check exit code

## Usage examples

```bash
# Format a template file
jinjasubst < kubernetes.yml | kubectl apply -f -

# Format from file path
jinjasubst -i kubernetes.yml -o rendered.yml

# Using shortened versions
jsubst -i kubernetes.yml > rendered.yml
jenvsubst -i kubernetes.yml > rendered.yml
j2subst -i kubernetes.yml > rendered.yml
j2envsubst -i kubernetes.yml > rendered.yml

# Using the shell global
jinjasubst -s <<'EOF'
Hello {{ USER }}, the date is {{ shell("date +%s") }}
EOF

# Using the shell filter
jinjasubst -s <<'EOF'
Hello {{ USER }}, your reversed name is {{ USER | shell("rev") }}
EOF
```

### Usage in development

```bash
# Inline example
python3 -m src.jinjasubst.cli -s <<'EOF'
Hello {{ USER }}, it is {{ shell("date") | tojson }}
Hello {{ USER }}, let's run some docker {{ exec_check("docker", "image", "ls") }}
EOF

# Run from file
python3 -m src.jinjasubst.cli -s < ./examples/shell.j2
```
