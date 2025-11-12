"""YAML pipeline definition loader."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from xml_lib.pipeline.context import ErrorStrategy
from xml_lib.pipeline.engine import Pipeline
from xml_lib.pipeline.stages import CustomStage, OutputStage, Stage, TransformStage, ValidateStage

logger = logging.getLogger(__name__)


class PipelineLoader:
    """Loads pipeline definitions from YAML files.

    YAML Format:
        name: my_pipeline
        description: Pipeline description
        error_strategy: fail_fast
        rollback_enabled: true
        variables:
          timestamp: "{{ datetime.now().isoformat() }}"
        stages:
          - type: validate
            name: validate_input
            schemas_dir: schemas
          - type: transform
            name: enrich
            transform: transforms/enrich.xsl
          - type: output
            name: output_html
            format: html
            output_path: out/report.html
    """

    def __init__(self):
        self.variables: Dict[str, Any] = {}

    def load(self, yaml_path: Path) -> Pipeline:
        """Load pipeline from YAML file.

        Args:
            yaml_path: Path to YAML pipeline definition

        Returns:
            Configured Pipeline instance

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is invalid or missing required fields
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Pipeline definition not found: {yaml_path}")

        logger.info(f"Loading pipeline from {yaml_path}")

        # Load YAML
        with open(yaml_path) as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise ValueError("Pipeline definition must be a YAML dictionary")

        # Extract pipeline configuration
        name = config.get("name", yaml_path.stem)
        description = config.get("description", "")
        error_strategy_str = config.get("error_strategy", "fail_fast")
        rollback_enabled = config.get("rollback_enabled", True)
        max_snapshots = config.get("max_snapshots", 100)

        # Parse error strategy
        try:
            error_strategy = ErrorStrategy(error_strategy_str)
        except ValueError:
            raise ValueError(
                f"Invalid error_strategy '{error_strategy_str}'. "
                f"Valid options: {[e.value for e in ErrorStrategy]}"
            )

        # Load variables
        self.variables = config.get("variables", {})
        self.variables = self._resolve_variables(self.variables)

        # Create pipeline
        pipeline = Pipeline(
            name=name,
            error_strategy=error_strategy,
            rollback_enabled=rollback_enabled,
            max_snapshots=max_snapshots,
        )

        # Load stages
        stages_config = config.get("stages", [])
        if not stages_config:
            raise ValueError("Pipeline must have at least one stage")

        for i, stage_config in enumerate(stages_config):
            try:
                stage = self._load_stage(stage_config, yaml_path.parent)
                pipeline.add_stage(stage)
            except Exception as e:
                raise ValueError(f"Failed to load stage {i + 1}: {e}") from e

        logger.info(
            f"Loaded pipeline '{name}' with {len(pipeline.stages)} stages: "
            f"{', '.join(s.name for s in pipeline.stages)}"
        )

        return pipeline

    def _load_stage(self, config: Dict[str, Any], base_dir: Path) -> Stage:
        """Load a stage from configuration dictionary.

        Args:
            config: Stage configuration
            base_dir: Base directory for resolving relative paths

        Returns:
            Configured Stage instance

        Raises:
            ValueError: If stage type is unknown or configuration is invalid
        """
        stage_type = config.get("type")
        if not stage_type:
            raise ValueError("Stage must have 'type' field")

        name = config.get("name")

        # Resolve variables in config
        config = self._resolve_config_variables(config)

        # Route to appropriate stage loader
        if stage_type == "validate":
            return self._load_validate_stage(config, base_dir, name)
        elif stage_type == "transform":
            return self._load_transform_stage(config, base_dir, name)
        elif stage_type == "output":
            return self._load_output_stage(config, base_dir, name)
        elif stage_type == "custom":
            return self._load_custom_stage(config, base_dir, name)
        else:
            raise ValueError(
                f"Unknown stage type '{stage_type}'. "
                f"Valid types: validate, transform, output, custom"
            )

    def _load_validate_stage(
        self,
        config: Dict[str, Any],
        base_dir: Path,
        name: Optional[str],
    ) -> ValidateStage:
        """Load ValidateStage from configuration."""
        schemas_dir = config.get("schemas_dir")
        if schemas_dir:
            schemas_dir = base_dir / schemas_dir

        guardrails_dir = config.get("guardrails_dir")
        if guardrails_dir:
            guardrails_dir = base_dir / guardrails_dir

        return ValidateStage(
            schemas_dir=schemas_dir,
            guardrails_dir=guardrails_dir,
            strict=config.get("strict", True),
            streaming=config.get("streaming", False),
            streaming_threshold=config.get("streaming_threshold", 10 * 1024 * 1024),
            name=name,
        )

    def _load_transform_stage(
        self,
        config: Dict[str, Any],
        base_dir: Path,
        name: Optional[str],
    ) -> TransformStage:
        """Load TransformStage from configuration."""
        transform_path = config.get("transform")
        if not transform_path:
            raise ValueError("TransformStage requires 'transform' field")

        # Resolve transform path relative to base_dir
        transform_path = base_dir / transform_path

        if not transform_path.exists():
            raise FileNotFoundError(f"Transform file not found: {transform_path}")

        params = config.get("params", {})

        return TransformStage(
            transform=transform_path,
            params=params,
            name=name,
        )

    def _load_output_stage(
        self,
        config: Dict[str, Any],
        base_dir: Path,
        name: Optional[str],
    ) -> OutputStage:
        """Load OutputStage from configuration."""
        format = config.get("format")
        if not format:
            raise ValueError("OutputStage requires 'format' field")

        output_path = config.get("output_path")
        if not output_path:
            raise ValueError("OutputStage requires 'output_path' field")

        # Resolve output path relative to base_dir
        output_path = base_dir / output_path

        template = config.get("template")
        if template:
            template = base_dir / template

        options = config.get("options", {})

        return OutputStage(
            format=format,
            output_path=output_path,
            template=template,
            options=options,
            name=name,
        )

    def _load_custom_stage(
        self,
        config: Dict[str, Any],
        base_dir: Path,
        name: Optional[str],
    ) -> CustomStage:
        """Load CustomStage from configuration."""
        raise NotImplementedError(
            "Custom stages are not yet supported in YAML definitions. "
            "Use the programmatic API to create custom stages."
        )

    def _resolve_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve variable expressions.

        Supports:
        - ${VAR_NAME} for environment variables
        - {{ python_expr }} for Python expressions (limited)

        Args:
            variables: Dictionary of variables

        Returns:
            Dictionary with resolved values
        """
        import os

        resolved = {}

        for key, value in variables.items():
            if isinstance(value, str):
                # Resolve environment variables: ${VAR_NAME}
                value = re.sub(
                    r"\$\{([^}]+)\}",
                    lambda m: os.environ.get(m.group(1), ""),
                    value,
                )

                # Resolve simple expressions: {{ datetime.now().isoformat() }}
                value = re.sub(
                    r"\{\{\s*datetime\.now\(\)\.isoformat\(\)\s*\}\}",
                    datetime.now().isoformat(),
                    value,
                )

            resolved[key] = value

        return resolved

    def _resolve_config_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve variable references in configuration.

        Replaces ${VAR_NAME} with variable values.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with resolved variables
        """
        resolved = {}

        for key, value in config.items():
            if isinstance(value, str):
                # Replace variable references
                for var_name, var_value in self.variables.items():
                    placeholder = f"${{{var_name}}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(var_value))

            elif isinstance(value, dict):
                # Recursively resolve nested dictionaries
                value = self._resolve_config_variables(value)

            resolved[key] = value

        return resolved


def load_pipeline(yaml_path: Path) -> Pipeline:
    """Convenience function to load a pipeline from YAML.

    Args:
        yaml_path: Path to YAML pipeline definition

    Returns:
        Configured Pipeline instance
    """
    loader = PipelineLoader()
    return loader.load(yaml_path)
