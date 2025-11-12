#!/usr/bin/env bash
# Bash completion script for xml-lib
# Install: source this file or copy to /etc/bash_completion.d/xml-lib

_xml_lib_completion() {
    local cur prev words cword
    _init_completion || return

    # Main commands
    local commands="validate publish render-pptx diff roundtrip phpify lint pipeline stream engine shell watch config help"

    # Subcommands
    local pipeline_cmds="run list dry-run validate"
    local stream_cmds="validate generate checkpoint benchmark"
    local engine_cmds="export visualize"
    local config_cmds="show get set reset"

    # Common flags
    local common_flags="--help -h --version"
    local output_flags="--output -o"
    local format_flags="--format"

    # Get the main command (first word after xml-lib)
    local cmd=""
    local subcmd=""
    local i
    for ((i = 1; i < cword; i++)); do
        if [[ "${words[i]}" != -* ]]; then
            if [[ -z "$cmd" ]]; then
                cmd="${words[i]}"
            elif [[ -z "$subcmd" ]]; then
                subcmd="${words[i]}"
            fi
        fi
    done

    # Complete main commands
    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return 0
    fi

    # Complete subcommands
    case "$cmd" in
        pipeline)
            if [[ -z "$subcmd" ]]; then
                COMPREPLY=($(compgen -W "$pipeline_cmds" -- "$cur"))
                return 0
            fi
            ;;
        stream)
            if [[ -z "$subcmd" ]]; then
                COMPREPLY=($(compgen -W "$stream_cmds" -- "$cur"))
                return 0
            fi
            ;;
        engine)
            if [[ -z "$subcmd" ]]; then
                COMPREPLY=($(compgen -W "$engine_cmds" -- "$cur"))
                return 0
            fi
            ;;
        config)
            if [[ -z "$subcmd" ]]; then
                COMPREPLY=($(compgen -W "$config_cmds" -- "$cur"))
                return 0
            fi
            ;;
    esac

    # Complete flags
    if [[ "$cur" == -* ]]; then
        local flags="$common_flags"

        case "$cmd" in
            validate)
                flags="$flags --schemas-dir --guardrails-dir $output_flags --jsonl --strict --math-policy --engine-check --streaming --progress"
                ;;
            publish)
                flags="$flags --output-dir --template --index --no-index"
                ;;
            render-pptx)
                flags="$flags $output_flags --template"
                ;;
            diff)
                flags="$flags --explain $format_flags $output_flags"
                ;;
            lint)
                flags="$flags $format_flags --fail-level --no-check-attribute-order --no-check-indentation --no-check-xxe"
                ;;
            pipeline)
                flags="$flags --output-dir $output_flags --var -v $format_flags --verbose -V"
                ;;
            stream)
                flags="$flags --schema --checkpoint-interval --checkpoint-dir --resume-from --track-memory --no-track-memory $format_flags"
                ;;
            watch)
                flags="$flags --command -c --path --debounce -d --clear --no-clear --recursive --no-recursive"
                ;;
            config)
                if [[ "$subcmd" == "show" ]]; then
                    flags="$flags $format_flags"
                fi
                ;;
        esac

        COMPREPLY=($(compgen -W "$flags" -- "$cur"))
        return 0
    fi

    # Complete file paths based on previous flag
    case "$prev" in
        --schema|--xsd)
            _filedir '@(xsd|rng)'
            ;;
        --template)
            if [[ "$cmd" == "render-pptx" ]]; then
                _filedir '@(pptx)'
            else
                _filedir
            fi
            ;;
        --output|-o|--output-dir)
            _filedir
            ;;
        --format)
            COMPREPLY=($(compgen -W "text json yaml xml" -- "$cur"))
            ;;
        --math-policy)
            COMPREPLY=($(compgen -W "sanitize mathml skip error" -- "$cur"))
            ;;
        --fail-level)
            COMPREPLY=($(compgen -W "error warning info" -- "$cur"))
            ;;
        *)
            # Default to XML file completion for main commands
            case "$cmd" in
                validate|publish|render-pptx|diff|lint)
                    _filedir '@(xml)'
                    ;;
                pipeline)
                    if [[ "$subcmd" == "run" ]]; then
                        _filedir '@(yaml|yml)'
                    fi
                    ;;
                stream)
                    _filedir '@(xml)'
                    ;;
                *)
                    _filedir
                    ;;
            esac
            ;;
    esac

    return 0
}

# Register completion function
complete -F _xml_lib_completion xml-lib

# Also support "xml_lib" command (underscore version)
complete -F _xml_lib_completion xml_lib
