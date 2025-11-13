"""Exception hierarchy for xml-lib.

This module defines a coherent exception hierarchy for the library.
Exceptions are used for "cannot even start" conditions like missing paths
or misconfiguration. For per-file validation issues, use result objects
(ValidationResult, LintResult, PublishResult) instead.

Exception Hierarchy:
    XMLLibError (base)
    ├── XMLConfigurationError (configuration issues)
    ├── XMLFileError (file I/O issues)
    │   ├── XMLFileNotFoundError (file not found)
    │   └── XMLParseError (XML parsing failed)
    ├── XMLValidationError (validation setup failed)
    ├── XMLPublishingError (publishing setup failed)
    └── XMLTelemetryError (telemetry backend failed)

Usage:
    >>> from xml_lib.exceptions import XMLFileNotFoundError
    >>> raise XMLFileNotFoundError("Project not found", path="/path/to/project")
"""


class XMLLibError(Exception):
    """Base exception for all xml-lib errors.

    This is the base class for all exceptions raised by xml-lib.
    Catch this to handle all library-specific errors.

    Attributes:
        message: Human-readable error message
        details: Optional dictionary with additional error details
    """

    def __init__(self, message: str, **details):
        """Initialize XMLLibError.

        Args:
            message: Error message
            **details: Additional error details as keyword arguments
        """
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        """Format error message with details."""
        if not self.details:
            return self.message

        details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
        return f"{self.message} ({details_str})"


class XMLConfigurationError(XMLLibError):
    """Configuration error - invalid or missing configuration.

    Raised when the library is misconfigured, such as:
    - Invalid schema directory
    - Missing required guardrails
    - Invalid telemetry configuration

    Example:
        >>> raise XMLConfigurationError(
        ...     "Invalid schemas directory",
        ...     path="/invalid/schemas",
        ...     reason="Directory does not exist"
        ... )
    """

    pass


class XMLFileError(XMLLibError):
    """File I/O error - problems reading or writing files.

    Base class for file-related errors.
    """

    pass


class XMLFileNotFoundError(XMLFileError, FileNotFoundError):
    """File or directory not found.

    Raised when a required file or directory doesn't exist.

    Example:
        >>> raise XMLFileNotFoundError("Project not found", path="/path/to/project")
    """

    pass


class XMLParseError(XMLFileError):
    """XML parsing failed.

    Raised when XML content cannot be parsed due to syntax errors.
    Note: For validation errors after parsing, use ValidationResult instead.

    Example:
        >>> raise XMLParseError(
        ...     "Failed to parse XML",
        ...     file="invalid.xml",
        ...     line=10,
        ...     message="Unclosed tag"
        ... )
    """

    pass


class XMLValidationError(XMLLibError):
    """Validation setup failed.

    Raised when validation cannot start due to configuration issues.
    Note: For validation errors during validation, use ValidationResult instead.

    Example:
        >>> raise XMLValidationError(
        ...     "No schemas found",
        ...     schemas_dir="/path/to/schemas"
        ... )
    """

    pass


class XMLPublishingError(XMLLibError):
    """Publishing setup failed.

    Raised when publishing cannot start due to configuration issues.
    Note: For publishing errors during operation, use PublishResult instead.

    Example:
        >>> raise XMLPublishingError(
        ...     "XSLT templates not found",
        ...     xslt_dir="/path/to/xslt"
        ... )
    """

    pass


class XMLTelemetryError(XMLLibError):
    """Telemetry backend error.

    Raised when telemetry cannot be initialized.
    Note: Telemetry errors during operation should be logged, not raised.

    Example:
        >>> raise XMLTelemetryError(
        ...     "Failed to connect to PostgreSQL",
        ...     connection_string="postgresql://localhost/telemetry"
        ... )
    """

    pass


class XMLSchemaError(XMLLibError):
    """Schema-related error.

    Raised when schema loading or compilation fails.

    Example:
        >>> raise XMLSchemaError(
        ...     "Invalid Relax NG schema",
        ...     schema_file="lifecycle.rng",
        ...     reason="Syntax error in schema"
        ... )
    """

    pass


class XMLGuardrailError(XMLLibError):
    """Guardrail-related error.

    Raised when guardrail loading or compilation fails.

    Example:
        >>> raise XMLGuardrailError(
        ...     "Invalid guardrail policy",
        ...     guardrail_file="policy.yaml",
        ...     reason="Unknown policy type"
        ... )
    """

    pass


# Convenience aliases for backward compatibility
ConfigurationError = XMLConfigurationError
FileNotFound = XMLFileNotFoundError
ParseError = XMLParseError
ValidationSetupError = XMLValidationError
PublishingSetupError = XMLPublishingError


__all__ = [
    # Base exception
    "XMLLibError",
    # Specific exceptions
    "XMLConfigurationError",
    "XMLFileError",
    "XMLFileNotFoundError",
    "XMLParseError",
    "XMLValidationError",
    "XMLPublishingError",
    "XMLTelemetryError",
    "XMLSchemaError",
    "XMLGuardrailError",
    # Aliases
    "ConfigurationError",
    "FileNotFound",
    "ParseError",
    "ValidationSetupError",
    "PublishingSetupError",
]
