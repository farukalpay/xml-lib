"""PPTX builder using python-pptx."""

from dataclasses import dataclass
from pathlib import Path

from pptx import Presentation

from xml_lib.pptx.parser import BuildPlan


@dataclass
class BuildResult:
    """Result of PPTX build."""

    success: bool
    output_path: Path | None = None
    slide_count: int = 0
    error: str | None = None


class PPTXBuilder:
    """Builder for PowerPoint presentations."""

    def __init__(self, template_path: Path | None = None):
        """Initialize PPTX builder.

        Args:
            template_path: Optional template .pptx file
        """
        self.template_path = template_path

    def build(self, plan: BuildPlan, output_path: Path) -> BuildResult:
        """Build PPTX from build plan.

        Args:
            plan: BuildPlan specification
            output_path: Output .pptx file path

        Returns:
            BuildResult
        """
        try:
            # Create presentation
            if self.template_path and self.template_path.exists():
                prs = Presentation(str(self.template_path))
            else:
                prs = Presentation()

            # Add title slide
            title_slide_layout = prs.slide_layouts[0]
            slide = prs.slides.add_slide(title_slide_layout)
            title = slide.shapes.title
            title.text = plan.title

            # Add content slides
            for slide_spec in plan.slides:
                slide_layout = prs.slide_layouts[1]  # Title and Content
                slide = prs.slides.add_slide(slide_layout)

                # Set title
                title = slide.shapes.title
                title.text = slide_spec.title

                # Add content
                if slide_spec.content:
                    body = slide.shapes.placeholders[1]
                    tf = body.text_frame
                    for item in slide_spec.content:
                        p = tf.add_paragraph()
                        p.text = item
                        p.level = 0

                # Add notes
                if slide_spec.notes:
                    notes_slide = slide.notes_slide
                    text_frame = notes_slide.notes_text_frame
                    text_frame.text = slide_spec.notes

            # Save presentation
            output_path.parent.mkdir(parents=True, exist_ok=True)
            prs.save(str(output_path))

            return BuildResult(
                success=True,
                output_path=output_path,
                slide_count=len(prs.slides),
            )

        except Exception as e:
            return BuildResult(
                success=False,
                error=str(e),
            )
