"""Mathematical engine for xml-lib: Banach/Hilbert constructs and proof obligations."""

from xml_lib.engine.spaces import (
    MathematicalSpace,
    MetricSpace,
    NormedSpace,
    BanachSpace,
    HilbertSpace,
    InnerProduct,
)
from xml_lib.engine.operators import (
    Operator,
    ContractionOperator,
    NonexpansiveOperator,
    FirmlyNonexpansiveOperator,
    ResolventOperator,
    ProximalOperator,
    ProjectionOperator,
)
from xml_lib.engine.fixed_points import (
    FixedPointIterator,
    FejerMonotoneSequence,
    ConvergenceResult,
    ConvergenceMetrics,
)
from xml_lib.engine.proofs import (
    ProofObligation,
    ProofStep,
    ProofResult,
    GuardrailProof,
    ProofEngine,
)
from xml_lib.engine.parser import EngineSpecParser
from xml_lib.engine.integration import EngineLedgerIntegration, EngineMetrics

__all__ = [
    # Spaces
    "MathematicalSpace",
    "MetricSpace",
    "NormedSpace",
    "BanachSpace",
    "HilbertSpace",
    "InnerProduct",
    # Operators
    "Operator",
    "ContractionOperator",
    "NonexpansiveOperator",
    "FirmlyNonexpansiveOperator",
    "ResolventOperator",
    "ProximalOperator",
    "ProjectionOperator",
    # Fixed points
    "FixedPointIterator",
    "FejerMonotoneSequence",
    "ConvergenceResult",
    "ConvergenceMetrics",
    # Proofs
    "ProofObligation",
    "ProofStep",
    "ProofResult",
    "GuardrailProof",
    "ProofEngine",
    # Parser and integration
    "EngineSpecParser",
    "EngineLedgerIntegration",
    "EngineMetrics",
]
