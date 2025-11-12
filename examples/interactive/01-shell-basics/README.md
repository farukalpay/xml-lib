# Example 01: Interactive Shell Basics

Learn how to use the xml-lib interactive shell.

## What You'll Learn

- Launching the interactive shell
- Using tab completion
- Creating and using aliases
- Navigating command history

## Instructions

### 1. Launch the Shell

```bash
xml-lib shell
```

You should see:

```
╔═══════════════════════════════════════════════════════════╗
║                    XML-LIB Interactive                    ║
║            Modern XML Toolkit for DevOps & CI/CD          ║
╚═══════════════════════════════════════════════════════════╝

Type 'help' for commands, 'exit' or Ctrl+D to quit.

xml-lib>
```

### 2. Try Tab Completion

Type these commands and press Tab:

```bash
# Command completion
xml-lib> val<Tab>
# Should complete to: validate

# Subcommand completion
xml-lib> pipeline <Tab>
# Should show: run  list  dry-run  validate

# File completion
xml-lib> validate exa<Tab>
# Should show XML files starting with 'exa'
```

### 3. Get Help

```bash
xml-lib> help
# Shows all available commands

xml-lib> validate --help
# Shows help for validate command
```

### 4. Run Commands

```bash
# Validate an example file
xml-lib> validate ../../example_document.xml

# Check configuration
xml-lib> config show
```

### 5. Create Aliases

```bash
# Create an alias for quick validation
xml-lib> config set aliases.v "validate"
✅ Set alias: v = validate

# Use the alias
xml-lib> v ../../example_document.xml

# Create more aliases
xml-lib> config set aliases.ex "validate ../../example_document.xml"
xml-lib> ex
```

### 6. View Command History

```bash
xml-lib> history
# Shows recent commands
```

### 7. Navigate History

- Press ↑ to go back in history
- Press ↓ to go forward
- Type part of a command and press ↑ to search history

### 8. Exit the Shell

```bash
xml-lib> exit
# Or press Ctrl+D
```

## Tips

1. **Auto-suggestions**: As you type, you'll see gray text suggesting commands from history. Press → to accept.

2. **Interrupt**: Press Ctrl+C to cancel current input without exiting the shell.

3. **Clear Screen**: Type `clear` to clear the terminal.

4. **Persistent History**: Your command history is saved between sessions in `~/.xml-lib/history`.

## Next Steps

- Try [02-watch-mode](../02-watch-mode/) to learn about automatic file watching
- Read the [Interactive Guide](../../../docs/INTERACTIVE_GUIDE.md) for advanced features
