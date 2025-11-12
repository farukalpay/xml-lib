#!/usr/bin/env bash
# Install shell completions for xml-lib
# Usage: ./scripts/install_completions.sh [bash|zsh|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_TYPE="${1:-all}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}!${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

install_bash_completion() {
    echo "Installing Bash completion..."

    # Try different locations
    local installed=false

    # System-wide bash completion directory (Debian/Ubuntu)
    if [[ -d /etc/bash_completion.d ]]; then
        sudo cp "$SCRIPT_DIR/bash_completion.sh" /etc/bash_completion.d/xml-lib
        log_info "Installed system-wide completion to /etc/bash_completion.d/xml-lib"
        installed=true
    fi

    # Homebrew bash completion directory (macOS)
    if command -v brew &> /dev/null; then
        local brew_prefix=$(brew --prefix 2>/dev/null || echo "")
        if [[ -n "$brew_prefix" && -d "$brew_prefix/etc/bash_completion.d" ]]; then
            cp "$SCRIPT_DIR/bash_completion.sh" "$brew_prefix/etc/bash_completion.d/xml-lib"
            log_info "Installed Homebrew completion to $brew_prefix/etc/bash_completion.d/xml-lib"
            installed=true
        fi
    fi

    # User-specific directory
    local user_completion_dir="$HOME/.local/share/bash-completion/completions"
    if [[ ! -d "$user_completion_dir" ]]; then
        mkdir -p "$user_completion_dir"
    fi
    cp "$SCRIPT_DIR/bash_completion.sh" "$user_completion_dir/xml-lib"
    log_info "Installed user completion to $user_completion_dir/xml-lib"
    installed=true

    if $installed; then
        echo ""
        log_info "Bash completion installed successfully!"
        echo "  To activate in current shell:"
        echo "    source $user_completion_dir/xml-lib"
        echo "  Or restart your shell"
    else
        log_error "Could not find bash completion directory"
        return 1
    fi
}

install_zsh_completion() {
    echo "Installing Zsh completion..."

    local installed=false

    # Get zsh fpath directories
    local fpath_dirs=""
    if command -v zsh &> /dev/null; then
        fpath_dirs=$(zsh -c 'echo $fpath' 2>/dev/null || echo "")
    fi

    # Try Homebrew zsh completions (macOS)
    if command -v brew &> /dev/null; then
        local brew_prefix=$(brew --prefix 2>/dev/null || echo "")
        if [[ -n "$brew_prefix" && -d "$brew_prefix/share/zsh/site-functions" ]]; then
            cp "$SCRIPT_DIR/zsh_completion.zsh" "$brew_prefix/share/zsh/site-functions/_xml-lib"
            log_info "Installed Homebrew completion to $brew_prefix/share/zsh/site-functions/_xml-lib"
            installed=true
        fi
    fi

    # Try system-wide directory
    if [[ -d /usr/local/share/zsh/site-functions ]]; then
        sudo cp "$SCRIPT_DIR/zsh_completion.zsh" /usr/local/share/zsh/site-functions/_xml-lib
        log_info "Installed system-wide completion to /usr/local/share/zsh/site-functions/_xml-lib"
        installed=true
    elif [[ -d /usr/share/zsh/site-functions ]]; then
        sudo cp "$SCRIPT_DIR/zsh_completion.zsh" /usr/share/zsh/site-functions/_xml-lib
        log_info "Installed system-wide completion to /usr/share/zsh/site-functions/_xml-lib"
        installed=true
    fi

    # User-specific directory
    local user_completion_dir="$HOME/.zsh/completions"
    if [[ ! -d "$user_completion_dir" ]]; then
        mkdir -p "$user_completion_dir"
    fi
    cp "$SCRIPT_DIR/zsh_completion.zsh" "$user_completion_dir/_xml-lib"
    log_info "Installed user completion to $user_completion_dir/_xml-lib"

    # Check if user completion dir is in fpath
    if ! echo "$fpath_dirs" | grep -q "$user_completion_dir"; then
        echo ""
        log_warn "Add the following to your ~/.zshrc:"
        echo "    fpath=($user_completion_dir \$fpath)"
        echo "    autoload -Uz compinit && compinit"
    fi

    installed=true

    if $installed; then
        echo ""
        log_info "Zsh completion installed successfully!"
        echo "  Reload completions:"
        echo "    rm -f ~/.zcompdump && exec zsh"
    else
        log_error "Could not find zsh completion directory"
        return 1
    fi
}

print_usage() {
    echo "Usage: $0 [bash|zsh|all]"
    echo ""
    echo "Install shell completions for xml-lib"
    echo ""
    echo "Options:"
    echo "  bash    Install Bash completion only"
    echo "  zsh     Install Zsh completion only"
    echo "  all     Install both (default)"
    echo ""
}

main() {
    echo "xml-lib Shell Completion Installer"
    echo "===================================="
    echo ""

    case "$INSTALL_TYPE" in
        bash)
            install_bash_completion
            ;;
        zsh)
            install_zsh_completion
            ;;
        all)
            install_bash_completion
            echo ""
            echo "---"
            echo ""
            install_zsh_completion
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        *)
            log_error "Unknown install type: $INSTALL_TYPE"
            print_usage
            exit 1
            ;;
    esac

    echo ""
    echo "===================================="
    log_info "Installation complete!"
}

main
