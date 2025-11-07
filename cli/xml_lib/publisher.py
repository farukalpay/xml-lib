"""XSLT 3.0 publisher for HTML rendering."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from lxml import etree
import tempfile

from xml_lib.telemetry import TelemetrySink
from xml_lib.sanitize import Sanitizer, MathPolicy


@dataclass
class PublishResult:
    """Result of publishing operation."""

    success: bool
    files: List[str] = field(default_factory=list)
    error: Optional[str] = None


class Publisher:
    """Publishes XML documents to HTML using XSLT 3.0."""

    def __init__(
        self,
        xslt_dir: Path,
        telemetry: Optional[TelemetrySink] = None,
    ):
        self.xslt_dir = xslt_dir
        self.telemetry = telemetry

        # Ensure XSLT directory exists
        self.xslt_dir.mkdir(parents=True, exist_ok=True)

        # Create default XSLT if not exists
        self._ensure_default_xslt()

    def _ensure_default_xslt(self) -> None:
        """Create default XSLT templates if they don't exist."""
        default_xslt = self.xslt_dir / "default.xsl"
        if not default_xslt.exists():
            default_xslt.write_text(self._get_default_xslt())

    def _get_default_xslt(self) -> str:
        """Get default XSLT template."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs">

  <xsl:output method="html" version="5.0" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <html>
      <head>
        <title>XML Document</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 2em; }
          h1 { color: #333; }
          .phase { margin: 2em 0; padding: 1em; border: 1px solid #ccc; }
          .phase-name { font-weight: bold; color: #0066cc; }
          .meta { background: #f5f5f5; padding: 1em; margin: 1em 0; }
          .payload { margin: 1em 0; }
          .timestamp { color: #666; font-size: 0.9em; }
          .checksum { font-family: monospace; font-size: 0.8em; color: #666; }
          pre { background: #f5f5f5; padding: 1em; overflow-x: auto; }
        </style>
      </head>
      <body>
        <xsl:apply-templates/>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="document">
    <h1>XML Lifecycle Document</h1>
    <xsl:if test="@timestamp">
      <div class="timestamp">Timestamp: <xsl:value-of select="@timestamp"/></div>
    </xsl:if>
    <xsl:if test="@checksum">
      <div class="checksum">Checksum: <xsl:value-of select="@checksum"/></div>
    </xsl:if>
    <xsl:apply-templates select="meta"/>
    <xsl:apply-templates select="phases"/>
    <xsl:apply-templates select="summary"/>
  </xsl:template>

  <xsl:template match="meta">
    <div class="meta">
      <h2>Metadata</h2>
      <xsl:if test="title">
        <p><strong>Title:</strong> <xsl:value-of select="title"/></p>
      </xsl:if>
      <xsl:if test="description">
        <p><strong>Description:</strong> <xsl:value-of select="description"/></p>
      </xsl:if>
      <xsl:if test="author">
        <p><strong>Author:</strong> <xsl:value-of select="author"/></p>
      </xsl:if>
    </div>
  </xsl:template>

  <xsl:template match="phases">
    <h2>Lifecycle Phases</h2>
    <xsl:apply-templates select="phase"/>
  </xsl:template>

  <xsl:template match="phase">
    <div class="phase">
      <div class="phase-name">Phase: <xsl:value-of select="@name"/></div>
      <xsl:if test="@timestamp">
        <div class="timestamp">Timestamp: <xsl:value-of select="@timestamp"/></div>
      </xsl:if>
      <xsl:apply-templates select="use"/>
      <xsl:apply-templates select="payload"/>
    </div>
  </xsl:template>

  <xsl:template match="use">
    <p><em>Using template: <xsl:value-of select="@path"/></em></p>
    <xsl:if test="text()">
      <p><xsl:value-of select="text()"/></p>
    </xsl:if>
  </xsl:template>

  <xsl:template match="payload">
    <div class="payload">
      <strong>Payload:</strong>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="summary">
    <div class="meta">
      <h2>Summary</h2>
      <xsl:if test="status">
        <p><strong>Status:</strong> <xsl:value-of select="status"/></p>
      </xsl:if>
      <xsl:if test="next-action">
        <p><strong>Next Action:</strong> <xsl:value-of select="next-action"/></p>
      </xsl:if>
    </div>
  </xsl:template>

  <!-- Default template for unknown elements -->
  <xsl:template match="*">
    <div style="margin-left: 1em;">
      <strong><xsl:value-of select="local-name()"/>:</strong>
      <xsl:text> </xsl:text>
      <xsl:choose>
        <xsl:when test="*">
          <xsl:apply-templates/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="."/>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

</xsl:stylesheet>
"""

    def publish(
        self,
        project_path: Path,
        output_dir: Path,
        strict: bool = False,
        math_policy: MathPolicy = MathPolicy.SANITIZE,
    ) -> PublishResult:
        """Publish XML documents to HTML.

        Args:
            project_path: Path to project containing XML files
            output_dir: Output directory for HTML files
            strict: Fail fast on errors
            math_policy: Policy for handling mathy XML (default: sanitize)

        Returns:
            PublishResult
        """
        start_time = datetime.now()
        result = PublishResult(success=True)
        sanitizer = (
            Sanitizer(output_dir) if math_policy == MathPolicy.SANITIZE else None
        )

        try:
            # Check if project path exists
            if not project_path.exists():
                result.success = False
                result.error = f"Project path does not exist: {project_path}"
                return result

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Load XSLT
            xslt_file = self.xslt_dir / "default.xsl"
            xslt_doc = etree.parse(str(xslt_file))
            transform = etree.XSLT(xslt_doc)

            # Find all XML files
            xml_files = [
                f
                for f in project_path.rglob("*.xml")
                if "schema" not in str(f) and f.parent.name != "guardrails"
            ]

            # Check if there are any files to publish
            if not xml_files:
                result.success = False
                result.error = f"No XML files found in {project_path}"
                return result

            # Transform each file
            for xml_file in xml_files:
                try:
                    doc = None

                    # Try to parse file, with sanitization if needed
                    try:
                        doc = etree.parse(str(xml_file))
                    except etree.XMLSyntaxError as parse_error:
                        # Handle based on policy
                        if math_policy == MathPolicy.ERROR:
                            raise
                        elif math_policy == MathPolicy.SKIP:
                            if strict:
                                result.success = False
                                result.error = (
                                    f"XML parse error in {xml_file}: {parse_error}"
                                )
                                break
                            else:
                                print(
                                    f"Warning: Skipping {xml_file} - XML parse error: {parse_error}"
                                )
                                continue
                        elif math_policy == MathPolicy.SANITIZE and sanitizer:
                            # Try sanitizing
                            sanitize_result = sanitizer.sanitize_for_parse(xml_file)
                            if sanitize_result.has_surrogates:
                                # Write mapping
                                rel_path = xml_file.relative_to(project_path)
                                sanitizer.write_mapping(
                                    rel_path, sanitize_result.mappings
                                )

                                # Parse sanitized content
                                with tempfile.NamedTemporaryFile(
                                    mode="wb", suffix=".xml", delete=False
                                ) as tmp:
                                    tmp.write(sanitize_result.content)
                                    tmp_path = Path(tmp.name)

                                try:
                                    doc = etree.parse(str(tmp_path))
                                    print(
                                        f"Info: Sanitized {xml_file} ({len(sanitize_result.mappings)} surrogates)"
                                    )
                                finally:
                                    tmp_path.unlink()
                            else:
                                # Still failed, re-raise
                                raise parse_error

                    if doc is None:
                        continue

                    html = transform(doc)

                    # Generate output filename
                    rel_path = xml_file.relative_to(project_path)
                    output_file = output_dir / rel_path.with_suffix(".html")
                    output_file.parent.mkdir(parents=True, exist_ok=True)

                    # Write HTML
                    output_file.write_bytes(bytes(html))
                    result.files.append(str(output_file))

                except etree.XMLSyntaxError as e:
                    # Final fallback for XMLSyntaxError
                    if strict or math_policy == MathPolicy.ERROR:
                        result.success = False
                        result.error = f"XML parse error in {xml_file}: {e}"
                        break
                    else:
                        print(f"Warning: Skipping {xml_file} - XML parse error: {e}")
                        continue

                except Exception as e:
                    result.success = False
                    result.error = f"Failed to transform {xml_file}: {e}"
                    break

            # Create index page
            if result.success:
                self._create_index(output_dir, result.files)

        except Exception as e:
            result.success = False
            result.error = str(e)

        # Log telemetry
        duration = (datetime.now() - start_time).total_seconds()
        if self.telemetry:
            self.telemetry.log_publish(
                project=str(project_path),
                success=result.success,
                duration=duration,
                output_files=len(result.files),
            )

        return result

    def _create_index(self, output_dir: Path, files: List[str]) -> None:
        """Create an index.html page."""
        html = (
            """<!DOCTYPE html>
<html>
<head>
    <title>XML-Lib Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2em; }
        h1 { color: #333; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 0.5em 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>XML-Lib Documentation</h1>
    <p>Generated on """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</p>
    <h2>Documents</h2>
    <ul>
"""
        )
        for file in sorted(files):
            rel_path = Path(file).relative_to(output_dir)
            name = rel_path.stem.replace("_", " ").title()
            html += f'        <li><a href="{rel_path}">{name}</a></li>\n'

        html += """    </ul>
</body>
</html>
"""

        index_file = output_dir / "index.html"
        index_file.write_text(html)
        files.append(str(index_file))
