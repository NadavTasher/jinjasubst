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
Hello {{ USER }}, the date is {{ shell("date") }}
EOF

# Using the shell filter
jinjasubst -s <<'EOF'
Hello {{ USER }}, your reversed name is {{ USER | shell("rev") }}
EOF
```

### Usage in development

```bash
python3 -m src.jinjasubst.cli -s <<'EOF'
Hello {{ USER }}, it is {{ shell("date") }}
EOF
```