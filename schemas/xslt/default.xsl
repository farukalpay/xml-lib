<?xml version="1.0" encoding="UTF-8"?>
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
