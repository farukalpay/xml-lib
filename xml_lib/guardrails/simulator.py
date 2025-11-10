"""Finite-state machine simulator for guardrails."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StateType(str, Enum):
    """FSM state types."""

    INITIAL = "initial"
    ACTIVE = "active"
    CHECKING = "checking"
    PASSED = "passed"
    FAILED = "failed"
    FINAL = "final"


@dataclass
class State:
    """FSM state."""

    name: str
    type: StateType
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Transition:
    """FSM transition."""

    from_state: str
    to_state: str
    condition: str
    action: str | None = None


@dataclass
class SimulationResult:
    """Result of guardrail simulation."""

    success: bool
    final_state: str
    trace: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class GuardrailSimulator:
    """Finite-state machine simulator for guardrail workflows."""

    def __init__(self) -> None:
        """Initialize simulator."""
        self.states: dict[str, State] = {}
        self.transitions: list[Transition] = []
        self.current_state: str | None = None

    def add_state(self, state: State) -> None:
        """Add state to simulator."""
        self.states[state.name] = state
        if state.type == StateType.INITIAL:
            self.current_state = state.name

    def add_transition(self, transition: Transition) -> None:
        """Add transition to simulator."""
        self.transitions.append(transition)

    def step(self, input_data: dict[str, Any]) -> str | None:
        """Execute one simulation step.

        Args:
            input_data: Input data for transition conditions

        Returns:
            New state name or None if no transition
        """
        if not self.current_state:
            return None

        # Find applicable transition
        for trans in self.transitions:
            if trans.from_state == self.current_state:
                # Evaluate condition (simplified)
                if self._evaluate_condition(trans.condition, input_data):
                    self.current_state = trans.to_state
                    return self.current_state

        return None

    def simulate(self, inputs: list[dict[str, Any]]) -> SimulationResult:
        """Run full simulation.

        Args:
            inputs: List of input data for each step

        Returns:
            SimulationResult with trace
        """
        trace = [self.current_state] if self.current_state else []
        errors = []

        for input_data in inputs:
            new_state = self.step(input_data)
            if new_state:
                trace.append(new_state)
            else:
                errors.append(f"No transition from {self.current_state}")
                break

        final_state = self.current_state or "unknown"
        success = self.states.get(final_state, State("", StateType.ACTIVE)).type == StateType.PASSED

        return SimulationResult(
            success=success,
            final_state=final_state,
            trace=trace,
            errors=errors,
        )

    def _evaluate_condition(self, condition: str, data: dict[str, Any]) -> bool:
        """Evaluate transition condition (simplified).

        Args:
            condition: Condition expression
            data: Input data

        Returns:
            True if condition met
        """
        # Simplified evaluation - in production, use safe expression evaluator
        try:
            return eval(condition, {"__builtins__": {}}, data)
        except Exception:
            return False
