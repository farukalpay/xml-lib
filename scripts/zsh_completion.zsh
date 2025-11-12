#compdef xml-lib xml_lib
# Zsh completion script for xml-lib
# Install: Copy to a directory in $fpath (e.g., /usr/local/share/zsh/site-functions/_xml-lib)

_xml-lib() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    local -a commands=(
        'validate:Validate XML documents'
        'publish:Generate HTML documentation'
        'render-pptx:Create PowerPoint presentation'
        'diff:Compare XML documents'
        'roundtrip:Round-trip XML processing'
        'phpify:Generate PHP pages'
        'lint:Check XML formatting and security'
        'pipeline:Run automation pipelines'
        'stream:Process large XML files'
        'engine:Mathematical engine operations'
        'shell:Launch interactive shell'
        'watch:Watch files for changes'
        'config:Manage configuration'
        'help:Show help'
    )

    _arguments -C \
        '1: :->command' \
        '*: :->args' \
        '--help[Show help]' \
        '--version[Show version]'

    case $state in
        command)
            _describe -t commands 'xml-lib commands' commands
            ;;
        args)
            case $line[1] in
                validate)
                    _arguments \
                        '1:project path:_files -/' \
                        '--schemas-dir[Schemas directory]:directory:_files -/' \
                        '--guardrails-dir[Guardrails directory]:directory:_files -/' \
                        '(--output -o)'{--output,-o}'[Output file]:file:_files' \
                        '--jsonl[JSON Lines output]:file:_files' \
                        '--strict[Strict mode]' \
                        '--math-policy[Math policy]:policy:(sanitize mathml skip error)' \
                        '--engine-check[Run engine checks]' \
                        '--streaming[Enable streaming validation]' \
                        '--progress[Show progress]' \
                        '--help[Show help]'
                    ;;
                publish)
                    _arguments \
                        '1:project path:_files -/' \
                        '(--output-dir -o)'{--output-dir,-o}'[Output directory]:directory:_files -/' \
                        '--template[Template file]:file:_files' \
                        '--index[Generate index]' \
                        '--no-index[Skip index generation]' \
                        '--help[Show help]'
                    ;;
                render-pptx)
                    _arguments \
                        '1:XML file:_files -g "*.xml"' \
                        '(--output -o)'{--output,-o}'[Output file]:file:_files -g "*.pptx"' \
                        '--template[Template file]:file:_files -g "*.pptx"' \
                        '--help[Show help]'
                    ;;
                diff)
                    _arguments \
                        '1:first file:_files -g "*.xml"' \
                        '2:second file:_files -g "*.xml"' \
                        '--explain[Show explanations]' \
                        '--format[Output format]:format:(text json xml)' \
                        '(--output -o)'{--output,-o}'[Output file]:file:_files' \
                        '--help[Show help]'
                    ;;
                lint)
                    _arguments \
                        '1:path:_files' \
                        '--format[Output format]:format:(text json)' \
                        '--fail-level[Fail level]:level:(error warning info)' \
                        '--no-check-attribute-order[Skip attribute order]' \
                        '--no-check-indentation[Skip indentation check]' \
                        '--no-check-xxe[Skip XXE check]' \
                        '--help[Show help]'
                    ;;
                pipeline)
                    case $words[2] in
                        run)
                            _arguments \
                                '1:pipeline file:_files -g "*.{yaml,yml}"' \
                                '2:input XML:_files -g "*.xml"' \
                                '(--output-dir -o)'{--output-dir,-o}'[Output directory]:directory:_files -/' \
                                '(--var -v)'{--var,-v}'[Set variable]:variable:' \
                                '--format[Output format]:format:(text json)' \
                                '(--verbose -V)'{--verbose,-V}'[Verbose output]' \
                                '--help[Show help]'
                            ;;
                        list|dry-run|validate)
                            _arguments '--help[Show help]'
                            ;;
                        *)
                            local -a pipeline_commands=(
                                'run:Execute pipeline'
                                'list:List templates'
                                'dry-run:Preview execution'
                                'validate:Check pipeline'
                            )
                            _describe -t pipeline-commands 'pipeline commands' pipeline_commands
                            ;;
                    esac
                    ;;
                stream)
                    case $words[2] in
                        validate)
                            _arguments \
                                '1:XML file:_files -g "*.xml"' \
                                '--schema[Schema file]:file:_files -g "*.{xsd,rng}"' \
                                '--checkpoint-interval[Checkpoint interval (MB)]:interval:' \
                                '--checkpoint-dir[Checkpoint directory]:directory:_files -/' \
                                '--resume-from[Resume from checkpoint]:file:_files' \
                                '(--track-memory --no-track-memory)'{--track-memory,--no-track-memory}'[Track memory]' \
                                '--format[Output format]:format:(text json)' \
                                '--help[Show help]'
                            ;;
                        generate|benchmark|checkpoint)
                            _arguments '--help[Show help]'
                            ;;
                        *)
                            local -a stream_commands=(
                                'validate:Validate large file'
                                'generate:Generate test data'
                                'checkpoint:Manage checkpoints'
                                'benchmark:Run benchmarks'
                            )
                            _describe -t stream-commands 'stream commands' stream_commands
                            ;;
                    esac
                    ;;
                watch)
                    _arguments \
                        '1:pattern:' \
                        '(--command -c)'{--command,-c}'[Command to execute]:command:' \
                        '--path[Base path]:directory:_files -/' \
                        '(--debounce -d)'{--debounce,-d}'[Debounce delay]:seconds:' \
                        '(--clear --no-clear)'{--clear,--no-clear}'[Clear terminal]' \
                        '(--recursive --no-recursive)'{--recursive,--no-recursive}'[Watch recursively]' \
                        '--help[Show help]'
                    ;;
                config)
                    case $words[2] in
                        show)
                            _arguments \
                                '--format[Output format]:format:(text yaml json)' \
                                '--help[Show help]'
                            ;;
                        get)
                            _arguments \
                                '1:key:' \
                                '--help[Show help]'
                            ;;
                        set)
                            _arguments \
                                '1:key:' \
                                '2:value:' \
                                '--help[Show help]'
                            ;;
                        reset)
                            _arguments \
                                '--confirm[Confirm reset]' \
                                '--help[Show help]'
                            ;;
                        *)
                            local -a config_commands=(
                                'show:Show configuration'
                                'get:Get config value'
                                'set:Set config value'
                                'reset:Reset to defaults'
                            )
                            _describe -t config-commands 'config commands' config_commands
                            ;;
                    esac
                    ;;
                shell)
                    _arguments '--help[Show help]'
                    ;;
                engine)
                    case $words[2] in
                        export|visualize)
                            _arguments '--help[Show help]'
                            ;;
                        *)
                            local -a engine_commands=(
                                'export:Export proofs'
                                'visualize:Visualize proofs'
                            )
                            _describe -t engine-commands 'engine commands' engine_commands
                            ;;
                    esac
                    ;;
                help)
                    _describe -t commands 'xml-lib commands' commands
                    ;;
            esac
            ;;
    esac

    return 0
}

_xml-lib "$@"
