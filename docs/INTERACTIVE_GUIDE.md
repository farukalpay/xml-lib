# XML-Lib Interactive Developer Experience Guide

Complete guide to xml-lib's modern interactive CLI features: shell, watch mode, autocomplete, and enhanced output.

## Table of Contents

- [Quick Start](#quick-start)
- [Interactive Shell](#interactive-shell)
- [Watch Mode](#watch-mode)
- [Configuration Management](#configuration-management)
- [Shell Completions](#shell-completions)
- [Enhanced Output](#enhanced-output)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Installation

```bash
# Install xml-lib with interactive features
pip install -r requirements.txt
pip install -e .

# Install shell completions (optional but recommended)
./scripts/install_completions.sh
```

### Try It Out

```bash
# Launch interactive shell
xml-lib shell

# Inside the shell:
xml-lib> validate example_document.xml
xml-lib> help
xml-lib> exit

# Watch files for changes
xml-lib watch "*.xml" --command "validate {file}"

# Configure settings
xml-lib config set output.emoji true
xml-lib config show
```

## Interactive Shell

The interactive shell provides a REPL (Read-Eval-Print Loop) environment with powerful features:

### Features

- **Tab Completion**: Press Tab to autocomplete commands, file paths, and flags
- **Command History**: Navigate with ↑/↓ arrows, persistent across sessions
- **Auto-Suggestions**: Gray text suggests commands from history (→ to accept)
- **Aliases**: Create shortcuts for frequently-used commands
- **Syntax Highlighting**: Commands are highlighted for readability

### Basic Usage

```bash
# Launch shell
xml-lib shell

# You'll see:
╔═══════════════════════════════════════════════════════════╗
║                    XML-LIB Interactive                    ║
║            Modern XML Toolkit for DevOps & CI/CD          ║
╚═══════════════════════════════════════════════════════════╝

Type 'help' for commands, 'exit' or Ctrl+D to quit.

xml-lib>
```

### Shell Commands

Inside the shell, you can use any xml-lib command:

```bash
# Validation
xml-lib> validate data.xml --schema schema.xsd
✅ Validation passed (0.23s)

# Pipeline execution
xml-lib> pipeline run templates/pipelines/ci-validation.yaml data.xml
✅ Pipeline completed successfully

# Linting
xml-lib> lint . --format json

# Configuration
xml-lib> config show
xml-lib> config set output.verbose true
```

### Built-in Shell Commands

- `help` - Show available commands
- `config` - Manage configuration (show, get, set, reset)
- `clear` - Clear the screen
- `history` - Show command history
- `exit` / `quit` - Exit shell (or press Ctrl+D)

### Keyboard Shortcuts

- **Tab** - Autocomplete
- **Ctrl+C** - Cancel current input (doesn't exit shell)
- **Ctrl+D** - Exit shell (when input is empty)
- **↑/↓** - Navigate command history
- **→** - Accept auto-suggestion
- **Ctrl+R** - Reverse history search (if enabled)

### Creating Aliases

Aliases let you create shortcuts for complex commands:

```bash
# Inside shell
xml-lib> config set aliases.v "validate --schema schemas/main.xsd"
✅ Set alias: v = validate --schema schemas/main.xsd

# Now use the alias
xml-lib> v data.xml
✅ Validation passed

# More alias examples
xml-lib> config set aliases.p "pipeline run"
xml-lib> config set aliases.s "stream validate"
xml-lib> config set aliases.lj "lint --format json"
```

### Tab Completion Examples

```bash
# Command completion
xml-lib> val<Tab>
# Completes to: validate

# Subcommand completion
xml-lib> pipeline <Tab>
# Shows: run  list  dry-run  validate

# File completion (only shows XML files for validate)
xml-lib> validate da<Tab>
# Completes to: data.xml

# Flag completion
xml-lib> validate data.xml --sc<Tab>
# Completes to: --schema

# Context-aware completion
xml-lib> validate data.xml --schema sch<Tab>
# Only shows .xsd and .rng files
```

## Watch Mode

Watch mode automatically executes commands when files change. Perfect for rapid development!

### Basic Usage

```bash
# Watch all XML files in current directory
xml-lib watch "*.xml" --command "validate {file} --schema schema.xsd"

# You'll see:
👀 Watching: *.xml
📝 Command: validate {file} --schema schema.xsd
Press Ctrl+C to stop

# When you edit an XML file:
[12:34:56] Change detected: data/records.xml
✅ Command completed (0.15s)
```

### Watch Patterns

```bash
# Watch specific extension
xml-lib watch "*.xml" --command "lint {file}"

# Watch specific directory
xml-lib watch "data/**/*.xml" --command "validate {file}" --path data/

# Watch multiple patterns (use shell or multiple terminals)
xml-lib watch "*.xml" --command "validate {file}" &
xml-lib watch "*.yaml" --command "pipeline validate {file}" &
```

### Placeholder: `{file}`

Use `{file}` in your command to represent the changed file:

```bash
# Validate changed file
xml-lib watch "*.xml" --command "validate {file} --schema schema.xsd"

# Lint changed file
xml-lib watch "*.xml" --command "lint {file} --format json"

# Run pipeline with changed file
xml-lib watch "*.xml" --command "pipeline run workflow.yaml {file}"

# Multiple commands (use shell scripting)
xml-lib watch "*.xml" --command "validate {file} && echo Validated!"
```

### Watch Options

```bash
# Custom debounce delay (avoid rapid re-runs)
xml-lib watch "*.xml" --command "validate {file}" --debounce 1.0

# Don't clear terminal on change
xml-lib watch "*.xml" --command "validate {file}" --no-clear

# Watch non-recursively (current directory only)
xml-lib watch "*.xml" --command "validate {file}" --no-recursive

# Watch specific path
xml-lib watch "*.xml" --command "validate {file}" --path ./data/
```

### Debouncing

Debouncing prevents commands from running multiple times when you save a file repeatedly:

```bash
# Default: 0.5 seconds
xml-lib watch "*.xml" --command "validate {file}"

# Increase debounce for slow operations
xml-lib watch "*.xml" --command "validate {file}" --debounce 2.0

# Set globally
xml-lib config set watch.debounce_seconds 1.0
```

### Watch Mode Use Cases

**1. Continuous Validation**
```bash
xml-lib watch "data/**/*.xml" --command "validate {file} --schema schema.xsd"
```

**2. Auto-Linting**
```bash
xml-lib watch "*.xml" --command "lint {file} --fail-level warning"
```

**3. Pipeline Testing**
```bash
xml-lib watch "*.xml" --command "pipeline run test-pipeline.yaml {file}"
```

**4. Documentation Generation**
```bash
xml-lib watch "docs/*.xml" --command "publish . --output-dir out/docs"
```

## Configuration Management

Configure xml-lib behavior through persistent configuration.

### Configuration File

Configuration is stored at:
- Linux/macOS: `~/.xml-lib/config.yaml`
- Or: `$XDG_CONFIG_HOME/xml-lib/config.yaml`

### Available Settings

```yaml
# Aliases (command shortcuts)
aliases:
  v: "validate --schema schemas/main.xsd"
  p: "pipeline run"

# Watch mode settings
watch:
  debounce_seconds: 0.5
  notify: false
  clear_on_change: true
  ignore_patterns:
    - "*.swp"
    - "*.tmp"
    - ".git/*"

# Output formatting
output:
  colors: true
  emoji: true
  verbose: false
  show_timing: true
  progress_bars: true
  max_error_lines: 50

# Interactive shell
shell:
  prompt: "xml-lib> "
  history_size: 1000
  multiline: false
  vi_mode: false
  auto_suggest: true
  complete_while_typing: true
```

### Commands

```bash
# Show all configuration
xml-lib config show

# Show as YAML
xml-lib config show --format yaml

# Show as JSON
xml-lib config show --format json

# Get specific value
xml-lib config get output.emoji
xml-lib config get shell.prompt

# Set value
xml-lib config set output.emoji false
xml-lib config set shell.prompt ">>> "
xml-lib config set watch.debounce_seconds 1.0

# Set alias
xml-lib config set aliases.v "validate --schema schema.xsd"

# Reset to defaults
xml-lib config reset --confirm
```

### Common Configurations

**Disable Emoji (for CI/CD)**
```bash
xml-lib config set output.emoji false
```

**Increase Debounce for Slow Validations**
```bash
xml-lib config set watch.debounce_seconds 2.0
```

**Enable Vi Mode in Shell**
```bash
xml-lib config set shell.vi_mode true
```

**Custom Shell Prompt**
```bash
xml-lib config set shell.prompt "🚀 xml> "
```

**Disable Colors (for Logs)**
```bash
xml-lib config set output.colors false
# Or use NO_COLOR environment variable:
export NO_COLOR=1
```

## Shell Completions

Shell completions provide Tab completion in your terminal (outside the interactive shell).

### Installation

```bash
# Install for both Bash and Zsh
./scripts/install_completions.sh

# Or install specific shell
./scripts/install_completions.sh bash
./scripts/install_completions.sh zsh
```

### Bash

```bash
# After installation, reload completions:
source ~/.bashrc

# Or source directly:
source ~/.local/share/bash-completion/completions/xml-lib
```

### Zsh

```bash
# After installation, reload completions:
rm -f ~/.zcompdump
exec zsh

# Or reload manually:
autoload -Uz compinit && compinit
```

### Usage

```bash
# Tab completion works the same as in the shell
xml-lib val<Tab>              # Completes to: validate
xml-lib validate da<Tab>      # Completes to: data.xml
xml-lib pipeline <Tab>        # Shows: run  list  dry-run
```

## Enhanced Output

xml-lib provides beautiful, informative terminal output with colors, progress bars, and structured formatting.

### Colored Output

- ✅ **Green**: Success messages
- ❌ **Red**: Errors
- ⚠️ **Yellow**: Warnings
- ℹ️ **Blue**: Info messages

### Progress Bars

For long-running operations:

```
Processing files...
[████████████████████] 100% (150/150) - 2.3s
✅ All files processed
```

### Validation Results

```
╔══════════════════════════════════╗
║ ✅ Validation Passed              ║
║ File: data.xml                   ║
╚══════════════════════════════════╝

Metric               Value
─────────────────────────────────
Duration             0.234s
Elements             1,523
Errors               0
Warnings             0
```

### Error Display

```
❌ Validation Failed

Errors:
  1. ❌ Invalid element 'settigns' (expected 'settings')
     Line 15, Column 3

     13 │ <configuration>
     14 │   <system>
     15 │   <settigns>
        │   ^^^^^^^^^
     16 │     <debug>true</debug>
```

### Disable Enhanced Output

```bash
# Disable emoji
xml-lib config set output.emoji false

# Disable colors
xml-lib config set output.colors false

# Or use environment variable
export NO_COLOR=1
```

## Advanced Usage

### Using in CI/CD

**Disable Interactive Features**
```bash
# Set environment variables
export NO_COLOR=1
export CI=true

# Use JSON output for parsing
xml-lib validate . --format json
xml-lib lint . --format json --fail-level warning
```

**Configuration for CI**
```yaml
# .xml-lib-ci.yaml
output:
  colors: false
  emoji: false
  progress_bars: false
```

### Scripting with Watch Mode

```bash
# Run multiple watchers in background
xml-lib watch "*.xml" --command "validate {file}" &
WATCH_PID=$!

# Do other work...

# Stop watcher
kill $WATCH_PID
```

### Custom Workflows

**Validation + Linting**
```bash
xml-lib watch "*.xml" --command "validate {file} && lint {file}"
```

**Pipeline with Notification**
```bash
xml-lib watch "*.xml" --command "pipeline run workflow.yaml {file} && notify-send 'Success!'"
```

## Troubleshooting

### Shell Doesn't Start

```bash
# Check if prompt-toolkit is installed
python -c "import prompt_toolkit; print(prompt_toolkit.__version__)"

# Reinstall dependencies
pip install -r requirements.txt
```

### Watch Mode Not Detecting Changes

```bash
# Check if watchdog is installed
python -c "import watchdog; print(watchdog.__version__)"

# Verify pattern matches files
ls *.xml  # Should show files

# Try absolute path
xml-lib watch "*.xml" --command "validate {file}" --path /absolute/path
```

### Completions Not Working

**Bash:**
```bash
# Check if completion is loaded
complete -p xml-lib

# Re-source completion
source ~/.local/share/bash-completion/completions/xml-lib
```

**Zsh:**
```bash
# Check fpath
echo $fpath

# Rebuild completion cache
rm -f ~/.zcompdump
autoload -Uz compinit && compinit
```

### Colors Not Showing

```bash
# Check if NO_COLOR is set
echo $NO_COLOR

# Unset if needed
unset NO_COLOR

# Or force colors
xml-lib config set output.colors true
```

### Configuration Not Persisting

```bash
# Check config file location
ls -la ~/.xml-lib/config.yaml

# Check permissions
ls -la ~/.xml-lib/

# Try explicit save
xml-lib config set output.emoji false
xml-lib config show  # Should reflect change
```

## Tips & Best Practices

### 1. Use Aliases for Common Commands

```bash
xml-lib config set aliases.v "validate --schema schemas/main.xsd"
xml-lib config set aliases.ll "lint --fail-level warning"
```

### 2. Combine Watch with Aliases

```bash
# In shell, set alias first
xml-lib> config set aliases.v "validate --schema schema.xsd"

# Then use in watch command
xml-lib watch "*.xml" --command "v {file}"
```

### 3. Project-Specific Configuration

```bash
# Create .xml-lib-project.yaml in your project
# Then export path:
export XML_LIB_CONFIG=.xml-lib-project.yaml
```

### 4. Terminal Multiplexers

Use with tmux/screen for persistent watching:

```bash
# In one pane:
xml-lib watch "*.xml" --command "validate {file}"

# In another pane:
vim data.xml
```

### 5. Shell Integration

Add to your `.bashrc` or `.zshrc`:

```bash
# Quick alias
alias xmlsh="xml-lib shell"
alias xmlw="xml-lib watch"

# Auto-cd to project
alias xmlproj="cd ~/projects/xml-project && xmlsh"
```

## Next Steps

- See [README.md](../README.md) for general xml-lib usage
- See [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) for pipeline automation
- Check out [examples/interactive/](../examples/interactive/) for example workflows
- Join our [GitHub Discussions](https://github.com/farukalpay/xml-lib/discussions)

## Feedback

Found a bug or have a feature request? [Open an issue](https://github.com/farukalpay/xml-lib/issues)!
