"""Mathematical engine - Hilbert/Banach spaces, operators, and proof generation."""

from xml_lib.engine.operators import Operator, compose
from xml_lib.engine.spaces import HilbertSpace, BanachSpace
from xml_lib.engine.norms import Norm, InnerProduct
from xml_lib.engine.fixed_points import FixedPointIterator, ConvergenceResult
from xml_lib.engine.proofs import Proof, ProofGenerator

__all__ = [
    "Operator",
    "compose",
    "HilbertSpace",
    "BanachSpace",
    "Norm",
    "InnerProduct",
    "FixedPointIterator",
    "ConvergenceResult",
    "Proof",
    "ProofGenerator",
]
