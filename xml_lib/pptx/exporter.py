"""HTML exporter for PPTX handouts."""

from pathlib import Path

from pptx import Presentation


class HTMLExporter:
    """Exporter for PPTX to HTML handouts."""

    def export(self, pptx_path: Path, output_path: Path) -> bool:
        """Export PPTX to HTML handout.

        Args:
            pptx_path: Input .pptx file
            output_path: Output .html file

        Returns:
            True if successful
        """
        try:
            prs = Presentation(str(pptx_path))

            html = ["<!DOCTYPE html>"]
            html.append("<html>")
            html.append("<head>")
            html.append("<meta charset='utf-8'>")
            html.append("<title>Presentation Handout</title>")
            html.append(self._get_styles())
            html.append("</head>")
            html.append("<body>")
            html.append("<h1>Presentation Handout</h1>")

            # Export each slide
            for i, slide in enumerate(prs.slides, 1):
                html.append(f'<div class="slide">')
                html.append(f"<h2>Slide {i}</h2>")

                # Extract text from shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        html.append(f"<p>{shape.text}</p>")

                # Add notes if present
                notes_slide = slide.notes_slide
                if notes_slide and notes_slide.notes_text_frame.text:
                    html.append(f'<div class="notes">')
                    html.append(f"<strong>Notes:</strong> {notes_slide.notes_text_frame.text}")
                    html.append("</div>")

                html.append("</div>")

            html.append("</body>")
            html.append("</html>")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(html))

            return True

        except Exception as e:
            return False

    def _get_styles(self) -> str:
        """Get CSS styles for HTML export."""
        return """
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .slide { border: 1px solid #ccc; padding: 15px; margin: 20px 0; }
            .notes { background: #f0f0f0; padding: 10px; margin-top: 10px; }
        </style>
        """
