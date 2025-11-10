"""Mathematical engine - Hilbert/Banach spaces, operators, and proof generation."""

from xml_lib.engine.fixed_points import ConvergenceResult, FixedPointIterator
from xml_lib.engine.norms import InnerProduct, Norm
from xml_lib.engine.operators import Operator, compose
from xml_lib.engine.proofs import Proof, ProofGenerator
from xml_lib.engine.spaces import BanachSpace, HilbertSpace

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
