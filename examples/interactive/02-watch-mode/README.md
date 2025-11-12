# Example 02: Watch Mode

Learn how to use watch mode for automatic validation.

## What You'll Learn

- Setting up file watching
- Auto-validating on file changes
- Customizing watch behavior
- Using watch with different commands

## Setup

Create a test XML file:

```bash
cat > test.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<document>
    <title>Test Document</title>
    <content>
        <paragraph>This is a test.</paragraph>
    </content>
</document>
EOF
```

## Instructions

### 1. Basic Watch

Start watching XML files:

```bash
xml-lib watch "*.xml" --command "validate {file}"
```

You should see:

```
👀 Watching: *.xml
📝 Command: validate {file}
Press Ctrl+C to stop
```

### 2. Modify the File

In another terminal (or editor), edit `test.xml`:

```bash
# Add a new element
vim test.xml
# Or use any editor
```

When you save, you'll see:

```
[12:34:56] Change detected: test.xml
✅ Command completed (0.15s)
```

### 3. Introduce an Error

Edit `test.xml` and break the XML:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<document>
    <title>Test Document</title>
    <content>
        <paragraph>Broken XML
    </content>
</document>
```

Save and watch the error appear:

```
[12:35:42] Change detected: test.xml
❌ Command failed (0.08s)
Error: Mismatched tags...
```

### 4. Watch with Linting

Stop the previous watch (Ctrl+C) and try linting:

```bash
xml-lib watch "*.xml" --command "lint {file}"
```

### 5. Custom Debounce

For slow operations, increase debounce:

```bash
xml-lib watch "*.xml" --command "validate {file}" --debounce 2.0
```

Now when you save rapidly, the command only runs after 2 seconds of no changes.

### 6. Watch Specific Directory

```bash
# Watch only files in data/ directory
xml-lib watch "data/*.xml" --command "validate {file}" --path data/
```

### 7. Disable Terminal Clearing

```bash
xml-lib watch "*.xml" --command "validate {file}" --no-clear
```

Now output accumulates instead of clearing on each change.

### 8. Watch Multiple Patterns

In separate terminals:

```bash
# Terminal 1: Watch XML files
xml-lib watch "*.xml" --command "validate {file}"

# Terminal 2: Watch YAML pipeline files
xml-lib watch "*.yaml" --command "pipeline validate {file}"
```

## Use Cases

### Continuous Validation

Keep this running while developing:

```bash
xml-lib watch "src/**/*.xml" --command "validate {file} --schema schema.xsd"
```

### Auto-Linting

Ensure code quality as you edit:

```bash
xml-lib watch "*.xml" --command "lint {file} --fail-level warning"
```

### Pipeline Testing

Test pipelines automatically:

```bash
xml-lib watch "*.xml" --command "pipeline run test-workflow.yaml {file}"
```

## Configuration

Set default watch behavior:

```bash
# Increase debounce globally
xml-lib config set watch.debounce_seconds 1.0

# Disable terminal clearing by default
xml-lib config set watch.clear_on_change false
```

## Tips

1. **Background Watching**: Run watch in background with `&` or in a tmux/screen session

2. **Editor Integration**: Some editors trigger multiple save events. Increase debounce if needed.

3. **Ignore Patterns**: Temporary files are automatically ignored (.swp, .tmp, etc.)

4. **Combine Commands**: Use `&&` to chain commands:
   ```bash
   xml-lib watch "*.xml" --command "validate {file} && lint {file}"
   ```

## Next Steps

- Try [03-custom-config](../03-custom-config/) to learn about configuration
- Read the [Interactive Guide](../../../docs/INTERACTIVE_GUIDE.md) for advanced watch patterns
