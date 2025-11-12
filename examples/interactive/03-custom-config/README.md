# Example 03: Custom Configuration

Learn how to configure xml-lib for your workflow.

## What You'll Learn

- Managing configuration settings
- Creating command aliases
- Customizing output formatting
- Project-specific configuration

## Instructions

### 1. View Current Configuration

```bash
xml-lib config show
```

You'll see:

```
Configuration
───────────────────────────────────────
Setting                        Value
───────────────────────────────────────
aliases                        (none)
output.colors                  True
output.emoji                   True
watch.debounce_seconds         0.5
...
```

### 2. Create Aliases

Aliases are shortcuts for frequently-used commands:

```bash
# Validation alias
xml-lib config set aliases.v "validate --schema schemas/main.xsd"

# Pipeline alias
xml-lib config set aliases.p "pipeline run"

# Linting alias with options
xml-lib config set aliases.lj "lint --format json --fail-level warning"
```

### 3. Use Aliases

```bash
# In shell
xml-lib shell

# Use your aliases
xml-lib> v data.xml
xml-lib> p workflow.yaml input.xml
xml-lib> lj .
```

### 4. Customize Output

```bash
# Disable emoji (for CI/CD or personal preference)
xml-lib config set output.emoji false

# Disable colors
xml-lib config set output.colors false

# Enable verbose mode
xml-lib config set output.verbose true

# Show timing information
xml-lib config set output.show_timing true
```

### 5. Configure Watch Mode

```bash
# Increase debounce for slow operations
xml-lib config set watch.debounce_seconds 2.0

# Keep terminal output (don't clear)
xml-lib config set watch.clear_on_change false
```

### 6. Customize Shell

```bash
# Change prompt
xml-lib config set shell.prompt "🚀 xml> "

# Increase history size
xml-lib config set shell.history_size 5000

# Enable Vi mode
xml-lib config set shell.vi_mode true
```

### 7. View Specific Setting

```bash
# Get a single value
xml-lib config get output.emoji
# Output: True

xml-lib config get aliases.v
# Output: validate --schema schemas/main.xsd
```

### 8. Export Configuration

```bash
# View as YAML (for sharing)
xml-lib config show --format yaml > my-config.yaml

# View as JSON
xml-lib config show --format json > my-config.json
```

### 9. Reset to Defaults

```bash
# Reset everything
xml-lib config reset --confirm
```

## Project-Specific Configuration

Create `.xml-lib.yaml` in your project:

```yaml
aliases:
  v: "validate --schema project-schema.xsd --strict"
  p: "pipeline run workflows/main.yaml"
  test: "pipeline run workflows/test.yaml"

output:
  emoji: false
  verbose: true

watch:
  debounce_seconds: 1.0
  clear_on_change: true
```

## Example Configurations

### For CI/CD

```bash
xml-lib config set output.colors false
xml-lib config set output.emoji false
xml-lib config set output.progress_bars false
```

### For Development

```bash
xml-lib config set output.colors true
xml-lib config set output.emoji true
xml-lib config set output.verbose true
xml-lib config set watch.debounce_seconds 0.5
```

### For Power Users

```bash
# Vi keybindings in shell
xml-lib config set shell.vi_mode true

# Custom prompt
xml-lib config set shell.prompt "→ "

# Useful aliases
xml-lib config set aliases.vv "validate --verbose"
xml-lib config set aliases.pp "pipeline run --verbose"
xml-lib config set aliases.ll "lint --format json"
```

## Configuration File Location

Your configuration is stored at:

- **Linux/macOS**: `~/.xml-lib/config.yaml`
- **With XDG**: `$XDG_CONFIG_HOME/xml-lib/config.yaml`

You can edit this file directly if you prefer.

## Environment Variables

Override configuration with environment variables:

```bash
# Disable colors
export NO_COLOR=1
xml-lib validate data.xml

# Use custom config location
export XML_LIB_CONFIG=./project-config.yaml
xml-lib shell
```

## All Available Settings

### Output Settings

- `output.colors` - Enable colored output (default: true)
- `output.emoji` - Use emoji in output (default: true)
- `output.verbose` - Verbose output mode (default: false)
- `output.show_timing` - Show operation timing (default: true)
- `output.progress_bars` - Show progress bars (default: true)
- `output.max_error_lines` - Max errors to display (default: 50)

### Watch Settings

- `watch.debounce_seconds` - Delay before re-running (default: 0.5)
- `watch.notify` - Desktop notifications (default: false)
- `watch.clear_on_change` - Clear terminal on change (default: true)
- `watch.ignore_patterns` - Files to ignore (list)

### Shell Settings

- `shell.prompt` - Shell prompt text (default: "xml-lib> ")
- `shell.history_size` - History entries to keep (default: 1000)
- `shell.multiline` - Enable multiline input (default: false)
- `shell.vi_mode` - Vi keybindings (default: false)
- `shell.auto_suggest` - Auto-suggestions from history (default: true)
- `shell.complete_while_typing` - Live completion (default: true)

## Tips

1. **Backup Configuration**:
   ```bash
   cp ~/.xml-lib/config.yaml ~/.xml-lib/config.yaml.backup
   ```

2. **Share Configuration**:
   ```bash
   xml-lib config show --format yaml > team-config.yaml
   # Share with team, they can manually apply settings
   ```

3. **Per-Project Settings**:
   Create `.xml-lib-project.yaml` and use:
   ```bash
   export XML_LIB_CONFIG=.xml-lib-project.yaml
   ```

4. **Temporary Override**:
   ```bash
   NO_COLOR=1 xml-lib validate data.xml
   ```

## Next Steps

- Read the [Interactive Guide](../../../docs/INTERACTIVE_GUIDE.md) for complete reference
- Experiment with different settings to find your perfect workflow
- Share your configuration with your team
