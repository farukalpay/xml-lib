"""Mathematical engine for xml-lib: Banach/Hilbert constructs and proof obligations."""

from xml_lib.engine.fixed_points import (
    ConvergenceMetrics,
    ConvergenceResult,
    FejerMonotoneSequence,
    FixedPointIterator,
)
from xml_lib.engine.integration import EngineLedgerIntegration, EngineMetrics
from xml_lib.engine.operators import (
    ContractionOperator,
    FirmlyNonexpansiveOperator,
    NonexpansiveOperator,
    Operator,
    ProjectionOperator,
    ProximalOperator,
    ResolventOperator,
)
from xml_lib.engine.parser import EngineSpecParser
from xml_lib.engine.proofs import (
    GuardrailProof,
    ProofEngine,
    ProofObligation,
    ProofResult,
    ProofStep,
)
from xml_lib.engine.spaces import (
    BanachSpace,
    HilbertSpace,
    InnerProduct,
    MathematicalSpace,
    MetricSpace,
    NormedSpace,
)

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
