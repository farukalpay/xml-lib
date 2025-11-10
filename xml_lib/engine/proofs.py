"""Structured proof generation and rendering."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProofStep:
    """Single step in a proof."""

    statement: str
    justification: str
    references: list[str] = field(default_factory=list)


@dataclass
class Proof:
    """Structured mathematical proof."""

    theorem: str
    hypothesis: list[str] = field(default_factory=list)
    steps: list[ProofStep] = field(default_factory=list)
    conclusion: str = ""

    def to_latex(self) -> str:
        """Generate LaTeX proof.

        Returns:
            LaTeX formatted proof
        """
        latex = ["\\begin{proof}"]
        latex.append(f"\\textbf{{Theorem:}} {self.theorem}\n")

        if self.hypothesis:
            latex.append("\\textbf{Hypothesis:}")
            latex.append("\\begin{itemize}")
            for hyp in self.hypothesis:
                latex.append(f"  \\item {hyp}")
            latex.append("\\end{itemize}\n")

        latex.append("\\textbf{Proof:}")
        for i, step in enumerate(self.steps, 1):
            latex.append(f"\\textbf{{Step {i}:}} {step.statement}")
            latex.append(f"\\textit{{Justification:}} {step.justification}\n")

        if self.conclusion:
            latex.append(f"\\textbf{{Conclusion:}} {self.conclusion}")

        latex.append("\\end{proof}")
        return "\n".join(latex)

    def to_html(self) -> str:
        """Generate HTML proof.

        Returns:
            HTML formatted proof
        """
        html = ['<div class="proof">']
        html.append(f'<h3>Theorem: {self.theorem}</h3>')

        if self.hypothesis:
            html.append('<h4>Hypothesis:</h4>')
            html.append("<ul>")
            for hyp in self.hypothesis:
                html.append(f"<li>{hyp}</li>")
            html.append("</ul>")

        html.append("<h4>Proof:</h4>")
        for i, step in enumerate(self.steps, 1):
            html.append(f'<div class="proof-step">')
            html.append(f"<strong>Step {i}:</strong> {step.statement}<br>")
            html.append(f'<em>Justification:</em> {step.justification}')
            html.append("</div>")

        if self.conclusion:
            html.append(f"<p><strong>Conclusion:</strong> {self.conclusion}</p>")

        html.append("</div>")
        return "\n".join(html)


class ProofGenerator:
    """Generator for mathematical proofs from XML specs."""

    def generate_from_xml(self, xml_path: Path) -> Proof:
        """Generate proof from XML specification.

        Args:
            xml_path: Path to XML proof spec

        Returns:
            Structured Proof
        """
        # Placeholder - would parse XML and extract proof structure
        return Proof(
            theorem="Placeholder theorem",
            hypothesis=["Hypothesis 1"],
            steps=[
                ProofStep(
                    statement="Placeholder step",
                    justification="By construction",
                )
            ],
            conclusion="Q.E.D.",
        )

    def export_proof(self, proof: Proof, output_path: Path, format: str = "latex") -> None:
        """Export proof to file.

        Args:
            proof: Proof to export
            output_path: Output file path
            format: Output format ('latex' or 'html')
        """
        if format == "latex":
            content = proof.to_latex()
        elif format == "html":
            content = proof.to_html()
        else:
            raise ValueError(f"Unsupported format: {format}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
