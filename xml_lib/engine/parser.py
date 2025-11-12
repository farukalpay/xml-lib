"""Parser for XML engine specifications."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from lxml import etree

from xml_lib.engine.operators import (
    ComposedOperator,
    ContractionOperator,
    FunctionOperator,
    NonexpansiveOperator,
    Operator,
    ProjectionOperator,
)
from xml_lib.engine.spaces import (
    BanachSpace,
    HilbertSpace,
    InnerProduct,
    MathematicalSpace,
    MetricSpace,
    NormedSpace,
)


@dataclass
class EngineSpec:
    """Parsed engine specification."""

    spaces: dict[str, MathematicalSpace]
    operators: dict[str, Operator]
    axioms: dict[str, str]
    theorems: dict[str, dict]
    metadata: dict[str, Any]


class EngineSpecParser:
    """Parse XML engine specifications into typed Python objects."""

    def __init__(self, engine_dir: Path):
        self.engine_dir = engine_dir
        self.spaces: dict[str, MathematicalSpace] = {}
        self.operators: dict[str, Operator] = {}
        self.axioms: dict[str, str] = {}
        self.theorems: dict[str, dict] = {}

    def parse(self) -> EngineSpec:
        """Parse all engine XML files."""
        # Parse spaces.xml
        spaces_file = self.engine_dir / "spaces.xml"
        if spaces_file.exists():
            self._parse_spaces(spaces_file)

        # Parse hilbert.xml
        hilbert_file = self.engine_dir / "hilbert.xml"
        if hilbert_file.exists():
            self._parse_hilbert(hilbert_file)

        # Parse operators.xml
        operators_file = self.engine_dir / "operators.xml"
        if operators_file.exists():
            self._parse_operators(operators_file)

        # Parse axioms.xml
        axioms_file = self.engine_dir / "axioms.xml"
        if axioms_file.exists():
            self._parse_axioms(axioms_file)

        # Parse proof.xml
        proof_file = self.engine_dir / "proof.xml"
        if proof_file.exists():
            self._parse_proofs(proof_file)

        return EngineSpec(
            spaces=self.spaces,
            operators=self.operators,
            axioms=self.axioms,
            theorems=self.theorems,
            metadata={"engine_dir": str(self.engine_dir)},
        )

    def _parse_spaces(self, path: Path) -> None:
        """Parse spaces.xml."""
        try:
            doc = etree.parse(str(path))
            root = doc.getroot()

            # Parse metric space
            metric_elem = root.find(".//metric")
            if metric_elem is not None:
                self.spaces["metric"] = MetricSpace(
                    dimension=10,  # Default
                    name="MetricSpace",
                    is_complete=False,
                )

            # Parse normed space
            normed_elem = root.find(".//normed")
            if normed_elem is not None:
                self.spaces["normed"] = NormedSpace(
                    dimension=10,
                    name="NormedSpace",
                )

            # Parse Banach space
            banach_elem = root.find(".//space[@id='banach']")
            if banach_elem is not None:
                self.spaces["banach"] = BanachSpace(
                    dimension=10,
                    name="BanachSpace",
                )

            # Parse Hilbert space reference
            hilbert_elem = root.find(".//space[@id='hilbert-ref']")
            if hilbert_elem is not None:
                # Will be populated in _parse_hilbert
                self.spaces["hilbert"] = HilbertSpace(
                    dimension=10,
                    name="HilbertSpace",
                )

        except Exception as e:
            print(f"Warning: Failed to parse spaces.xml: {e}")

    def _parse_hilbert(self, path: Path) -> None:
        """Parse hilbert.xml."""
        try:
            doc = etree.parse(str(path))
            root = doc.getroot()

            # Create Hilbert space with Euclidean inner product
            hilbert = HilbertSpace(
                dimension=10,
                name="HilbertSpace",
                inner_product=InnerProduct.euclidean(),
            )
            self.spaces["hilbert"] = hilbert

            # Parse operator definitions
            for op_elem in root.xpath(".//operators/definition"):
                op_id = op_elem.get("id")
                if op_id == "nonexpansive":
                    self.operators["T_nonexpansive"] = NonexpansiveOperator(
                        space=hilbert,
                        name="NonexpansiveT",
                    )
                elif op_id == "contraction":
                    self.operators["T_contraction"] = ContractionOperator(
                        space=hilbert,
                        name="ContractionT",
                        contraction_q=0.9,
                    )

        except Exception as e:
            print(f"Warning: Failed to parse hilbert.xml: {e}")

    def _parse_operators(self, path: Path) -> None:
        """Parse operators.xml."""
        try:
            doc = etree.parse(str(path))
            root = doc.getroot()

            # Get base space
            space = self.spaces.get("hilbert", HilbertSpace(dimension=10, name="H"))

            # Parse operator definitions
            for op_elem in root.xpath(".//definitions/operator"):
                op_id = op_elem.get("id")
                if op_id == "T":
                    # Baseline transform
                    self.operators["T"] = NonexpansiveOperator(
                        space=space,
                        name="BaselineTransform",
                    )
                elif op_id == "P_C":
                    # Projection onto feasibility set
                    self.operators["P_C"] = ProjectionOperator(
                        space=space,
                        name="ProjectionC",
                    )

            # Parse composition G = P_C ∘ T
            comp_elem = root.find(".//composition[@id='G']")
            if comp_elem is not None and "T" in self.operators and "P_C" in self.operators:
                self.operators["G"] = ComposedOperator(
                    operators=[self.operators["P_C"], self.operators["T"]],
                    space=space,
                    name="ComposedG",
                )

        except Exception as e:
            print(f"Warning: Failed to parse operators.xml: {e}")

    def _parse_axioms(self, path: Path) -> None:
        """Parse axioms.xml."""
        try:
            doc = etree.parse(str(path))
            root = doc.getroot()

            for axiom in root.xpath("//axiom"):
                axiom_id = axiom.get("id")
                text = "".join(axiom.itertext()).strip()
                if axiom_id:
                    self.axioms[axiom_id] = text

        except Exception as e:
            print(f"Warning: Failed to parse axioms.xml: {e}")

    def _parse_proofs(self, path: Path) -> None:
        """Parse proof.xml."""
        try:
            doc = etree.parse(str(path))
            root = doc.getroot()

            # Parse lemmas
            for lemma in root.xpath("//lemma"):
                lemma_id = lemma.get("id")
                statement = lemma.find("statement")
                if lemma_id and statement is not None:
                    self.theorems[f"lemma_{lemma_id}"] = {
                        "type": "lemma",
                        "id": lemma_id,
                        "statement": "".join(statement.itertext()).strip(),
                    }

            # Parse theorems
            for theorem in root.xpath("//theorem"):
                thm_id = theorem.get("id")
                statement = theorem.find("statement")
                if thm_id and statement is not None:
                    self.theorems[f"theorem_{thm_id}"] = {
                        "type": "theorem",
                        "id": thm_id,
                        "statement": "".join(statement.itertext()).strip(),
                    }

        except Exception as e:
            print(f"Warning: Failed to parse proof.xml: {e}")

    def create_sample_operator(
        self,
        operator_type: str,
        space: MathematicalSpace,
        **kwargs: Any,
    ) -> Operator:
        """Create a sample operator for testing."""
        if operator_type == "contraction":
            return ContractionOperator(
                space=space,
                name=kwargs.get("name", "SampleContraction"),
                contraction_q=kwargs.get("q", 0.9),
            )
        elif operator_type == "nonexpansive":
            return NonexpansiveOperator(
                space=space,
                name=kwargs.get("name", "SampleNonexpansive"),
            )
        elif operator_type == "projection":
            return ProjectionOperator(
                space=space,
                name=kwargs.get("name", "SampleProjection"),
            )
        elif operator_type == "function":
            # Default: scaled identity
            scale = kwargs.get("scale", 0.9)
            return FunctionOperator(
                space=space,
                name=kwargs.get("name", "SampleFunction"),
                function=lambda x: scale * x,
            )
        else:
            return NonexpansiveOperator(space=space, name="DefaultOperator")

    def generate_sample_points(
        self,
        space: MathematicalSpace,
        count: int = 10,
        seed: int = 42,
    ) -> list[npt.NDArray[np.float64]]:
        """Generate sample points in space for testing."""
        np.random.seed(seed)
        points: list[npt.NDArray[np.float64]] = []
        for _ in range(count):
            point = np.random.randn(space.dimension) * 0.5
            points.append(point)
        return points
