# Changelog

All notable changes to xml-lib will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Task 1: Developer UX & Safety
- **New `xml-lib lint` command** for XML code quality and security checks
  - Check indentation consistency with configurable indent size (default: 2 spaces)
  - Verify alphabetical attribute ordering
  - Detect XXE vulnerabilities (external entity declarations and DTD references)
  - Check trailing whitespace, line length (120 chars), and final newlines
  - Support for `--allow-xxe` flag to explicitly allow external entities when needed
  - Output formats: `text` (human-friendly with emojis) and `json` (machine-readable for CI/CD)
  - Configurable `--fail-level` (info/warning/error) to control exit codes

- **Enhanced `validate` command** with new output options
  - `--format {text,json}` for machine-readable validation results
  - `--fail-level {warning,error}` to treat warnings as errors
  - JSON output includes structured error/warning data with file locations

- **Enhanced `diff` command** with JSON output
  - `--format {text,json}` for programmatic diff consumption
  - JSON output includes difference type, paths, values, and explanations

#### Task 2: Performance & Large Files
- **Streaming validation** using iterparse for memory-efficient processing
  - `--streaming/--no-streaming` flag (default: off)
  - Configurable `--streaming-threshold` in bytes (default: 10MB)
  - Automatic fallback when schema engines require full tree
  - Element-by-element processing with periodic memory cleanup

- **Progress reporting** with visual feedback
  - `--progress/--no-progress` flag for validate command
  - Unicode spinner animation during validation (⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)
  - File-by-file progress tracking with counts
  - Completion summary with status
  - Automatically disabled for non-TTY outputs

#### Task 4: PHP Generator Security
- **Comprehensive XXE protection test suite** (12 tests)
  - Tests for external entity blocking
  - Tests for external DTD blocking
  - Tests for parameter entity blocking
  - Billion laughs attack prevention tests
  - Network access blocking tests
  - Size and time limit tests

- **`--allow-xxe` flag for phpify command**
  - Explicit opt-in for external entity resolution
  - Clear warning message when enabled
  - Documented security risks in CLI help
  - Default remains secure (XXE disabled)

### Changed
- Validator now accepts `use_streaming`, `streaming_threshold_bytes`, and `show_progress` parameters
- ValidationResult includes `used_streaming` flag to track when streaming was used
- ParseConfig in PHP generator now includes `allow_xxe` parameter (default: False)
- SecureXMLParser respects `allow_xxe` configuration with appropriate security warnings

### Security
- **XXE Protection hardened** in PHP generator
  - Default configuration blocks external entities, DTD loading, and network access
  - Explicit `--allow-xxe` flag required to enable external entities
  - Prevention of billion laughs attacks with `huge_tree=False`
  - Comprehensive test coverage for XXE attack vectors

- **XML Linter** detects security issues
  - Scans for external entity declarations
  - Warns about external DTD references
  - Provides `--allow-xxe` override for legitimate use cases

### Fixed
- Minor linting issues resolved with ruff auto-fix
- Improved error handling in streaming validation mode

## [0.1.0] - Previous Release

Initial production-grade release with:
- XML lifecycle validation (Relax NG + Schematron)
- Content-addressed storage with SHA-256
- Cryptographic signing of validation results
- HTML publishing via XSLT 3.0
- PowerPoint generation from XML
- PHP page generation with security controls
- Mathematical engine (Hilbert/Banach spaces)
- Z3 formal verification
- Multi-backend proof visualization
- Property-based testing with Hypothesis
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions
