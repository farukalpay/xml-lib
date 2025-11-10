"""Policy language for guardrails."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from xml_lib.types import Priority


@dataclass
class PolicyRule:
    """Individual policy rule."""

    id: str
    name: str
    description: str
    constraint: str
    constraint_type: str = "xpath"
    priority: Priority = Priority.MEDIUM
    message: str = ""


@dataclass
class Policy:
    """Collection of policy rules."""

    name: str
    version: str
    rules: list[PolicyRule] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Policy":
        """Load policy from YAML file.

        Args:
            yaml_path: Path to YAML policy file

        Returns:
            Policy instance
        """
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        rules = [
            PolicyRule(
                id=rule.get("id", ""),
                name=rule.get("name", ""),
                description=rule.get("description", ""),
                constraint=rule.get("constraint", ""),
                constraint_type=rule.get("type", "xpath"),
                priority=Priority(rule.get("priority", "medium")),
                message=rule.get("message", ""),
            )
            for rule in data.get("rules", [])
        ]

        return cls(
            name=data.get("name", ""),
            version=data.get("version", "1.0"),
            rules=rules,
        )

    def to_yaml(self, output_path: Path) -> None:
        """Write policy to YAML file.

        Args:
            output_path: Output file path
        """
        data = {
            "name": self.name,
            "version": self.version,
            "rules": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "type": rule.constraint_type,
                    "constraint": rule.constraint,
                    "priority": rule.priority.value,
                    "message": rule.message,
                }
                for rule in self.rules
            ],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
