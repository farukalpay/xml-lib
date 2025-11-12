# Interactive Features Examples

Examples demonstrating xml-lib's interactive developer experience features.

## Examples

### 01-shell-basics

Learn the interactive shell with autocomplete and history.

```bash
cd 01-shell-basics
# Follow README.md instructions
```

### 02-watch-mode

Set up automated file watching and validation.

```bash
cd 02-watch-mode
# Follow README.md instructions
```

### 03-custom-config

Configure xml-lib for your workflow with aliases and custom settings.

```bash
cd 03-custom-config
# Follow README.md instructions
```

## Quick Start

```bash
# Try the interactive shell
cd 01-shell-basics
xml-lib shell

# Try watch mode
cd 02-watch-mode
xml-lib watch "*.xml" --command "validate {file}"

# Configure aliases
xml-lib config set aliases.v "validate --schema schema.xsd"
```

## Documentation

See [INTERACTIVE_GUIDE.md](../../docs/INTERACTIVE_GUIDE.md) for complete documentation.
